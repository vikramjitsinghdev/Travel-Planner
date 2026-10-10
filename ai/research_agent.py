"""ResearchAgent: deep, source-grounded research for selected destinations."""
import json
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

    def research_destinations(self, destinations, requirements, retry_number=0):
        if not isinstance(destinations, list) or not destinations:
            raise ValueError("ResearchAgent requires a non-empty destinations list.")
        researched = []
        for destination in destinations:
            name = str(destination.get("destination") or "").strip()
            country = str(destination.get("country") or "").strip()
            if not name or not country:
                raise ValueError("Every destination must include destination and country.")
            evidence, sources, queries = self._gather_evidence(name, country, requirements, retry_number)
            structured = self._structure_research(name, country, requirements, evidence)
            structured["destination"] = name
            structured["country"] = country
            structured["source_urls"] = sources
            structured["search_queries"] = queries
            structured["research_attempt"] = retry_number + 1
            researched.append(structured)
        return {"destinations": researched}

    def _gather_evidence(self, destination, country, requirements, retry_number):
        if retry_number:
            queries = [
                f"{destination} {country} official tourism attractions travel information",
                f"{destination} {country} current visitor costs accommodation food local transportation",
                f"{destination} {country} official tourism authority travel advice accessibility safety",
                f"{destination} {country} major attractions opening hours admission official websites",
            ]
        else:
            queries = [
                f"{destination} {country} travel guide major attractions official tourism",
                f"{destination} {country} average daily travel budget accommodation food transport costs",
                f"{destination} {country} best time to visit weather seasons visitor advice",
                f"{destination} {country} local transportation safety accessibility travel tips",
            ]
        all_results, sources = [], []
        for query in queries:
            response = self.tavily.search_raw(query, max_results=5)
            for item in response.get("results", []):
                content = str(item.get("raw_content") or item.get("content") or "").strip()
                if not content:
                    continue
                record = {
                    "query": query,
                    "title": str(item.get("title") or ""),
                    "url": str(item.get("url") or ""),
                    "content": content[:2500],
                }
                all_results.append(record)
                if record["url"] and record["url"] not in sources:
                    sources.append(record["url"])
        # Keep source evidence bounded for model latency/context.
        return all_results[:24], sources[:20], queries

    def _structure_research(self, destination, country, requirements, evidence):
        prompt = f"""
Produce structured, useful travel research for {destination}, {country} using ONLY the supplied web evidence and user requirements.
Do not invent prices, opening hours, current availability, transport schedules, or source URLs. If evidence is missing or inconsistent, say so in uncertainties. Costs must be estimates, state currency and per-person/per-day basis where supported; otherwise use null.
User requirements:
{json.dumps(requirements, ensure_ascii=False, default=str)}
Search evidence:
{json.dumps(evidence, ensure_ascii=False)}
Return JSON with exactly these fields:
{{
 "basic_info":"concise 100-180 word destination overview",
 "major_attractions":[{{"name":"","description":"","estimated_cost":null,"currency":null,"source_url":""}}],
 "cost_estimates":{{"travel_to_destination":{{"amount":null,"currency":null,"basis":""}},"accommodation_per_night":{{"amount":null,"currency":null,"basis":""}},"food_per_day":{{"amount":null,"currency":null,"basis":""}},"local_transport_per_day":{{"amount":null,"currency":null,"basis":""}}}},
 "best_time_to_visit":"",
 "local_transport":"",
 "practical_tips":[""],
 "safety_and_accessibility_notes":[""],
 "fit_to_user_preferences":"",
 "uncertainties":[""]
}}
Use up to 8 attractions. If a fact is not supported, use null, an empty string, or explicitly mark it unknown. No markdown.
"""
        result = self.llm.chat_json(
            "You are Wanderlust's deep travel researcher. Ground every factual claim in the provided web evidence. Never fabricate citations or precise prices. Return valid JSON only.",
            prompt,
            temperature=0.1,
        )
        # Normalize expected fields so the frontend receives stable types.
        result.setdefault("basic_info", "")
        for key in ("major_attractions", "practical_tips", "safety_and_accessibility_notes", "uncertainties"):
            if not isinstance(result.get(key), list):
                result[key] = []
        result.setdefault("cost_estimates", {})
        result.setdefault("best_time_to_visit", "")
        result.setdefault("local_transport", "")
        result.setdefault("fit_to_user_preferences", "")
        return result
