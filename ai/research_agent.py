"""
ResearchAgent: source-grounded destination research.

Each destination can be researched independently, allowing
TravelPlanner to process multiple destinations concurrently.
"""

import json
import time

from services.ollama_service import OllamaCloudService
from services.tavily_service import TavilyService


class ResearchAgent:
    def __init__(self):
        self.llm = OllamaCloudService(
            api_key_env="OLLAMA_API_KEY_RESEARCH",
            model_env="OLLAMA_RESEARCH_MODEL",
            default_model="gpt-oss:120b-cloud",
            timeout_env="OLLAMA_RESEARCH_TIMEOUT",
            default_timeout=240,
        )

        self.tavily = TavilyService()

    def research_destination(
        self,
        destination,
        requirements,
        retry_number=0
    ):
        """
        Deeply research one destination.

        This is the primary entry point used by the
        concurrent TravelPlanner.
        """

        started = time.perf_counter()

        if not isinstance(destination, dict):
            raise ValueError(
                "Destination must be a dictionary."
            )

        name = str(
            destination.get("destination") or ""
        ).strip()

        country = str(
            destination.get("country") or ""
        ).strip()

        if not name or not country:
            raise ValueError(
                "Destination and country are required."
            )

        evidence, sources, queries, warnings = (
            self._gather_evidence(
                name,
                country,
                requirements,
                retry_number
            )
        )

        structure_started = time.perf_counter()

        structured = self._structure_research(
            name,
            country,
            requirements,
            evidence
        )

        structure_elapsed = (
            time.perf_counter() - structure_started
        )

        structured["destination"] = name
        structured["country"] = country

        structured["source_urls"] = sources
        structured["search_queries"] = queries

        structured["research_attempt"] = retry_number + 1

        structured["research_warnings"] = warnings

        structured["research_timing"] = {
            "total_seconds": round(
                time.perf_counter() - started,
                3
            ),
            "structuring_seconds": round(
                structure_elapsed,
                3
            ),
            "evidence_records": len(evidence),
            "source_count": len(sources),
            "query_count": len(queries),
        }

        return structured

    def research_destinations(
        self,
        destinations,
        requirements,
        retry_number=0
    ):
        """
        Backward-compatible batch interface.

        The main planner uses research_destination()
        concurrently instead.

        This method intentionally remains sequential so
        existing callers retain predictable behavior.
        """

        if (
            not isinstance(destinations, list)
            or not destinations
        ):
            raise ValueError(
                "ResearchAgent requires a non-empty destinations list."
            )

        researched = []

        for destination in destinations:
            researched.append(
                self.research_destination(
                    destination,
                    requirements,
                    retry_number=retry_number
                )
            )

        return {
            "destinations": researched
        }

    def _gather_evidence(
        self,
        destination,
        country,
        requirements,
        retry_number
    ):
        """
        Gather evidence using concurrent Tavily searches.

        Failed searches are recorded as warnings instead
        of automatically terminating the entire research.
        """

        if retry_number:
            queries = [
                (
                    f"{destination} {country} official tourism "
                    "attractions travel information"
                ),
                (
                    f"{destination} {country} current visitor "
                    "costs accommodation food local transportation"
                ),
                (
                    f"{destination} {country} official tourism "
                    "authority travel advice accessibility safety"
                ),
                (
                    f"{destination} {country} major attractions "
                    "opening hours admission official websites"
                ),
            ]

        else:
            queries = [
                (
                    f"{destination} {country} travel guide "
                    "major attractions official tourism"
                ),
                (
                    f"{destination} {country} average daily "
                    "travel budget accommodation food transport costs"
                ),
                (
                    f"{destination} {country} best time to visit "
                    "weather seasons visitor advice"
                ),
                (
                    f"{destination} {country} local transportation "
                    "safety accessibility travel tips"
                ),
            ]

        responses = self.tavily.search_many(
            queries,
            max_results=5
        )

        all_results = []
        sources = []
        warnings = []

        seen_sources = set()

        for response in responses:
            query = response.get("query", "")

            error = response.get("error")

            if error:
                warnings.append(
                    f"Search failed for query '{query}': {error}"
                )

            for item in response.get("results", []):
                if not isinstance(item, dict):
                    continue

                content = str(
                    item.get("raw_content")
                    or item.get("content")
                    or ""
                ).strip()

                if not content:
                    continue

                url = str(
                    item.get("url") or ""
                ).strip()

                record = {
                    "query": query,
                    "title": str(
                        item.get("title") or ""
                    ),
                    "url": url,
                    "content": content[:2500],
                }

                all_results.append(record)

                if url and url not in seen_sources:
                    seen_sources.add(url)
                    sources.append(url)

        # Keep model input bounded.
        evidence = all_results[:24]

        # If every search fails or yields no usable evidence,
        # avoid presenting unsupported research as successful.
        if not evidence:
            warnings.append(
                "No usable web evidence was collected."
            )

        return (
            evidence,
            sources[:20],
            queries,
            warnings
        )

    def _structure_research(
        self,
        destination,
        country,
        requirements,
        evidence
    ):
        """
        Convert collected evidence into structured research.

        Unsupported facts must remain unknown rather than
        being filled with invented information.
        """

        prompt = f"""
Produce structured, useful travel research for
{destination}, {country} using ONLY the supplied web
evidence and user requirements.

Do not invent prices, opening hours, current availability,
transport schedules, or source URLs.

If evidence is missing or inconsistent, say so in
uncertainties.

Costs must be estimates, state currency and
per-person/per-day basis where supported; otherwise
use null.

User requirements:
{json.dumps(requirements, ensure_ascii=False, default=str)}

Search evidence:
{json.dumps(evidence, ensure_ascii=False)}

Return JSON with exactly these fields:

{{
  "basic_info": "concise 100-180 word destination overview",
  "major_attractions": [
    {{
      "name": "",
      "description": "",
      "estimated_cost": null,
      "currency": null,
      "source_url": ""
    }}
  ],
  "cost_estimates": {{
    "travel_to_destination": {{
      "amount": null,
      "currency": null,
      "basis": ""
    }},
    "accommodation_per_night": {{
      "amount": null,
      "currency": null,
      "basis": ""
    }},
    "food_per_day": {{
      "amount": null,
      "currency": null,
      "basis": ""
    }},
    "local_transport_per_day": {{
      "amount": null,
      "currency": null,
      "basis": ""
    }}
  }},
  "best_time_to_visit": "",
  "local_transport": "",
  "practical_tips": [],
  "safety_and_accessibility_notes": [],
  "fit_to_user_preferences": "",
  "uncertainties": []
}}

Use up to 8 attractions.

If a fact is not supported, use null, an empty
string, or explicitly mark it unknown.

No markdown.
"""

        result = self.llm.chat_json(
            (
                "You are Wanderlust's deep travel researcher. "
                "Ground every factual claim in the provided "
                "web evidence. Never fabricate citations or "
                "precise prices. Return valid JSON only."
            ),
            prompt,
            temperature=0.1,
        )

        if not isinstance(result, dict):
            raise ValueError(
                "Research model returned invalid structured data."
            )

        # Normalize expected fields.
        result.setdefault("basic_info", "")

        list_fields = [
            "major_attractions",
            "practical_tips",
            "safety_and_accessibility_notes",
            "uncertainties",
        ]

        for field in list_fields:
            if not isinstance(result.get(field), list):
                result[field] = []

        if not isinstance(
            result.get("cost_estimates"),
            dict
        ):
            result["cost_estimates"] = {}

        result.setdefault("best_time_to_visit", "")
        result.setdefault("local_transport", "")
        result.setdefault("fit_to_user_preferences", "")

        return result