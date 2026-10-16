"""
TavilyService: shared web-search service for Wanderlust.

Features:
- Bounded concurrent searches.
- Individual search failure handling.
- Search timing information.
- Backward-compatible search interfaces.
"""

import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

from dotenv import load_dotenv
from tavily import TavilyClient


class TavilyService:
    def __init__(self):
        load_dotenv()

        api_key = os.getenv("TAVILY_API_KEY")

        if not api_key:
            raise RuntimeError(
                "TAVILY_API_KEY is not set in .env."
            )

        self.client = TavilyClient(api_key=api_key)

        self.max_concurrent_searches = max(
            1,
            min(
                int(
                    os.getenv(
                        "TAVILY_MAX_CONCURRENT_SEARCHES",
                        "4"
                    )
                ),
                10
            )
        )

    def search_raw(
        self,
        query,
        max_results=5,
        topic="general"
    ):
        """
        Execute one Tavily search.

        This method preserves the original interface.
        """

        if not isinstance(query, str) or not query.strip():
            raise ValueError(
                "Tavily query must be a non-empty string."
            )

        started = time.perf_counter()

        response = self.client.search(
            query=query.strip(),
            max_results=max(
                1,
                min(int(max_results), 10)
            ),
            topic=topic,
            include_answer=False,
            include_raw_content=True,
        )

        elapsed = time.perf_counter() - started

        if not isinstance(response, dict):
            raise ValueError(
                "Tavily returned an unexpected response."
            )

        # Add timing metadata without changing the results.
        response.setdefault(
            "_search_metadata",
            {}
        )

        response["_search_metadata"].update({
            "query": query,
            "elapsed_seconds": round(elapsed, 3),
        })

        return response

    def search(
        self,
        query,
        max_results=5,
        topic="general"
    ):
        """
        Return only the search results.

        Preserves the original interface.
        """

        response = self.search_raw(
            query,
            max_results=max_results,
            topic=topic
        )

        return response.get("results", [])

    def _search_one(
        self,
        query,
        max_results,
        topic
    ):
        """
        Execute one search and capture its outcome.

        A failed search does not raise out of the
        concurrent batch.
        """

        started = time.perf_counter()

        try:
            response = self.search_raw(
                query,
                max_results=max_results,
                topic=topic
            )

            return {
                "query": query,
                "results": response.get("results", []),
                "error": None,
                "elapsed_seconds": round(
                    time.perf_counter() - started,
                    3
                ),
            }

        except Exception as exc:
            return {
                "query": query,
                "results": [],
                "error": str(exc),
                "elapsed_seconds": round(
                    time.perf_counter() - started,
                    3
                ),
            }

    def search_many(
        self,
        queries,
        max_results=5,
        topic="general"
    ):
        """
        Search multiple queries concurrently.

        Returns results in the same order as the input
        queries, regardless of completion order.

        Each entry contains:
        - query
        - results
        - error
        - elapsed_seconds
        """

        if not isinstance(queries, list):
            raise TypeError(
                "queries must be a list."
            )

        valid_queries = [
            query.strip()
            for query in queries
            if isinstance(query, str) and query.strip()
        ]

        if not valid_queries:
            return []

        started = time.perf_counter()

        output = [None] * len(valid_queries)

        worker_count = min(
            self.max_concurrent_searches,
            len(valid_queries)
        )

        with ThreadPoolExecutor(
            max_workers=worker_count,
            thread_name_prefix="tavily-search"
        ) as executor:

            futures = {
                executor.submit(
                    self._search_one,
                    query,
                    max_results,
                    topic
                ): index
                for index, query in enumerate(valid_queries)
            }

            for future in as_completed(futures):
                index = futures[future]

                try:
                    output[index] = future.result()

                except Exception as exc:
                    # Defensive fallback. _search_one should
                    # normally capture individual failures.
                    output[index] = {
                        "query": valid_queries[index],
                        "results": [],
                        "error": str(exc),
                        "elapsed_seconds": 0.0,
                    }

        elapsed = time.perf_counter() - started

        print(
            f"[Tavily] Completed {len(valid_queries)} "
            f"searches in {elapsed:.2f}s"
        )

        return output