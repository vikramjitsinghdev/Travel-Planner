import os
from tavily_service import TavilyClient
from dotenv import load_dotenv


class TavilyService:
    """
    Centralized Tavily search service.

    All workers use this class for web research.

    The Tavily API key is loaded from:

        TAVILY_API_KEY

    Workers should NEVER access the Tavily API key directly.
    """

    def __init__(self):
        load_dotenv()

        api_key = os.getenv("TAVILY_API_KEY")

        if not api_key:
            raise ValueError(
                "TAVILY_API_KEY was not found in the environment variables."
            )

        self.client = TavilyClient(api_key=api_key)

    # =========================================================
    # STANDARD SEARCH
    # =========================================================

    def search(self, query, max_results=5):
        """
        Perform a Tavily web search.

        Args:
            query (str):
                Search query.

            max_results (int):
                Maximum number of results.

        Returns:
            list:
                List of Tavily search results.
        """

        if not query or not query.strip():
            raise ValueError(
                "Search query cannot be empty."
            )

        response = self.client.search(
            query=query.strip(),
            search_depth="advanced",
            max_results=max_results,
            include_answer=False,
            include_raw_content=False
        )

        return response.get(
            "results",
            []
        )

    # =========================================================
    # RAW SEARCH
    # =========================================================

    def search_raw(self, query, max_results=5):
        """
        Perform a Tavily search and return the complete
        Tavily response.

        Useful when metadata is required.
        """

        if not query or not query.strip():
            raise ValueError(
                "Search query cannot be empty."
            )

        return self.client.search(
            query=query.strip(),
            search_depth="advanced",
            max_results=max_results,
            include_answer=False,
            include_raw_content=False
        )

    # =========================================================
    # MULTIPLE SEARCHES
    # =========================================================

    def search_many(self, queries, max_results=5):
        """
        Perform multiple Tavily searches.

        Args:
            queries (list[str]):
                List of search queries.

            max_results (int):
                Maximum results per query.

        Returns:
            list[dict]:

            [
                {
                    "query": "...",
                    "results": [...]
                },
                ...
            ]
        """

        if not queries:
            raise ValueError(
                "At least one search query is required."
            )

        results = []

        for query in queries:

            if not query or not query.strip():
                continue

            search_results = self.search(
                query=query,
                max_results=max_results
            )

            results.append({
                "query": query,
                "results": search_results
            })

        return results