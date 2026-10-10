"""Tavily web-search wrapper shared by TravelAgent and ResearchAgent."""
import os
from dotenv import load_dotenv
from tavily import TavilyClient


class TavilyService:
    def __init__(self):
        load_dotenv()
        api_key = os.getenv("TAVILY_API_KEY")
        if not api_key:
            raise RuntimeError("TAVILY_API_KEY is not set in .env.")
        self.client = TavilyClient(api_key=api_key)

    def search_raw(self, query, max_results=5, topic="general"):
        if not isinstance(query, str) or not query.strip():
            raise ValueError("Tavily query must be a non-empty string.")
        return self.client.search(
            query=query.strip(),
            max_results=max(1, min(int(max_results), 10)),
            topic=topic,
            include_answer=False,
            include_raw_content=True,
        )

    def search(self, query, max_results=5, topic="general"):
        return self.search_raw(query, max_results=max_results, topic=topic).get("results", [])

    def search_many(self, queries, max_results=5, topic="general"):
        if not isinstance(queries, list):
            raise TypeError("queries must be a list.")
        output = []
        for query in queries:
            if not isinstance(query, str) or not query.strip():
                continue
            output.append({"query": query, "results": self.search(query, max_results, topic)})
        return output
