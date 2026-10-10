"""TravelAgent: chooses destinations, obtains basic info, and checks consistency."""
import json
import re
from services.ollama_service import OllamaCloudService
from services.tavily_service import TavilyService
from services.pexel_service import PexelsService
from services.map_service import MapService


class TravelAgent:
    def __init__(self):
        self.llm = OllamaCloudService(
            api_key_env="OLLAMA_API_KEY_TRAVEL",
            model_env="OLLAMA_TRAVEL_MODEL",
            default_model="gpt-oss:20b-cloud",
            timeout_env="OLLAMA_TRAVEL_TIMEOUT",
            default_timeout=150,
        )
        self.tavily = TavilyService()
        self.pexels = PexelsService()
        self.maps = MapService()

    def select_destinations(self, requirements, count=3):
        """Select exactly three destinations using the extracted requirements."""
        prompt = f"""
Choose exactly {count} distinct, real travel destinations that best match these requirements.
Respect explicit country/region, budget, mobility, transport, safety, wanted and avoided preferences.
If a country or region is explicitly specified, stay within it. Do not invent user constraints.
Return only JSON in this format:
{{"destinations":[{{"destination":"city or destination name","country":"country","reason":"short fit explanation"}}]}}
Requirements:
{json.dumps(requirements, ensure_ascii=False, default=str)}
"""
        result = self.llm.chat_json(
            "You are Wanderlust's destination-selection agent. Return valid JSON only. Select destinations, do not research or invent citations.",
            prompt,
            temperature=0.25,
        )
        destinations = result.get("destinations")
        if not isinstance(destinations, list):
            raise ValueError("TravelAgent did not return a destinations array.")
        clean = []
        seen = set()
        for item in destinations:
            if not isinstance(item, dict):
                continue
            name = str(item.get("destination") or item.get("name") or "").strip()
            country = str(item.get("country") or "").strip()
            if not name or not country:
                continue
            key = (name.casefold(), country.casefold())
            if key in seen:
                continue
            seen.add(key)
            clean.append({"destination": name, "country": country, "reason": str(item.get("reason") or "").strip()})
            if len(clean) == count:
                break
        if len(clean) != count:
            raise ValueError(f"TravelAgent returned {len(clean)} valid destinations; expected {count}.")
        return clean

    def get_basic_information(self, destination, country, retry_number=0):
        """Search Tavily and use the 20B model to summarize the search evidence."""
        suffix = " travel overview culture attractions visitor information best time to visit"
        if retry_number:
            suffix = " official tourism guide geography local culture major attractions visitor essentials"
        query = f"{destination}, {country}{suffix}"
        search = self.tavily.search_raw(query, max_results=6)
        results = search.get("results", [])
        evidence = self._clean_evidence(results, limit=12)
        if not evidence:
            return {
                "basic_info": "Basic information could not be retrieved from the available web results.",
                "sources": [],
                "search_query": query,
            }
        summary = self.llm.chat_json(
            "Summarize travel destinations using only supplied search evidence. Never add unsupported facts. Return valid JSON only.",
            f"Destination: {destination}, {country}\nEvidence:\n{json.dumps(evidence, ensure_ascii=False)}\nReturn {{\"basic_info\":\"120-180 word overview\",\"key_facts\":[\"fact\"],\"uncertainties\":[\"uncertain item\"]}}.",
            temperature=0.1,
        )
        return {
            "basic_info": str(summary.get("basic_info") or "Basic information could not be summarized."),
            "key_facts": self._string_list(summary.get("key_facts"), 8),
            "uncertainties": self._string_list(summary.get("uncertainties"), 5),
            "sources": self._source_list(results),
            "search_query": query,
        }

    def enrich_destination(self, destination, country, basic_info=None):
        """Attach image and geocoding data. External enrichments fail independently."""
        try:
            images = self.pexels.search_destination(destination, country, per_page=4)
        except Exception as exc:
            images = []
            image_error = str(exc)
        else:
            image_error = None
        try:
            map_data = self.maps.get_destination_map(destination, country)
        except Exception as exc:
            map_data = None
            map_error = str(exc)
        else:
            map_error = None
        return {
            "basic_info": basic_info or {},
            "images": images,
            "image_urls": [image["image_url"] for image in images if image.get("image_url")],
            "map_coordinates": map_data,
            "map_url": (map_data or {}).get("map_url"),
            "enrichment_warnings": [message for message in [image_error, map_error] if message],
        }

    def compare_information(self, destination, country, deep_research, basic_info):
        """Compare two independently sourced summaries; do not treat similarity as proof of truth."""
        deep_summary = str(deep_research.get("basic_info") or deep_research.get("summary") or "")
        basic_summary = str(basic_info.get("basic_info") or "")
        prompt = f"""
Compare these two descriptions of the SAME destination. Determine whether they are broadly consistent on identity, geography, destination type, and major characteristics. Different detail levels are fine. Flag substantive contradictions, not omissions.
Destination: {destination}, {country}
Deep research summary:
{deep_summary[:6000]}
Independent basic-info summary:
{basic_summary[:6000]}
Return JSON only:
{{"similar":true,"reason":"short explanation","contradictions":["specific contradiction"]}}
"""
        try:
            result = self.llm.chat_json(
                "You are a cautious factual-consistency checker. Do not claim that similarity proves accuracy. Return JSON only.",
                prompt,
                temperature=0.0,
            )
            similar = bool(result.get("similar"))
            contradictions = self._string_list(result.get("contradictions"), 6)
            return {"similar": similar, "reason": str(result.get("reason") or ""), "contradictions": contradictions, "method": "gpt-oss:20b-cloud"}
        except Exception as exc:
            # Conservative deterministic fallback: compare meaningful words.
            a = self._content_words(deep_summary)
            b = self._content_words(basic_summary)
            overlap = len(a & b) / max(1, min(len(a), len(b)))
            return {"similar": overlap >= 0.18, "reason": "Fallback lexical comparison; LLM comparison failed.", "contradictions": [], "method": "lexical-fallback", "warning": str(exc)}

    @staticmethod
    def _clean_evidence(results, limit=12):
        evidence = []
        for item in results:
            content = item.get("raw_content") or item.get("content") or ""
            content = re.sub(r"\s+", " ", str(content)).strip()
            if not content:
                continue
            evidence.append({"title": item.get("title", ""), "url": item.get("url", ""), "content": content[:1800]})
            if len(evidence) >= limit:
                break
        return evidence

    @staticmethod
    def _source_list(results):
        output, seen = [], set()
        for item in results:
            url = str(item.get("url") or "").strip()
            if not url or url in seen:
                continue
            seen.add(url)
            output.append({"title": str(item.get("title") or url), "url": url})
        return output[:12]

    @staticmethod
    def _string_list(value, limit=8):
        if not isinstance(value, list):
            return []
        return [str(item).strip() for item in value if str(item).strip()][:limit]

    @staticmethod
    def _content_words(text):
        stop = {"this", "that", "with", "from", "have", "been", "there", "their", "about", "destination", "travel", "city", "country", "known", "also", "which", "where", "while", "such", "many", "most", "some", "into", "than", "they", "them", "are", "was", "were", "and", "the", "for", "you", "its", "has", "can"}
        return {word for word in re.findall(r"[a-z]{4,}", text.lower()) if word not in stop}
