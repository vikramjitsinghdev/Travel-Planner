"""
TravelAgent: destination selection, independent research,
consistency checking, and destination enrichment.
"""

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

    # --------------------------------------------------
    # DESTINATION SELECTION
    # --------------------------------------------------

    def select_destinations(
        self,
        requirements,
        count=3
    ):
        """
        Select exactly the requested number of destinations.
        """

        prompt = f"""
Choose exactly {count} distinct, real travel destinations
that best match these requirements.

Respect explicit country/region, budget, mobility,
transport, safety, wanted and avoided preferences.

If a country or region is explicitly specified, stay
within it. Do not invent user constraints.

Return only JSON in this format:

{{
  "destinations": [
    {{
      "destination": "city or destination name",
      "country": "country",
      "reason": "short fit explanation"
    }}
  ]
}}

Requirements:
{json.dumps(requirements, ensure_ascii=False, default=str)}
"""

        result = self.llm.chat_json(
            (
                "You are Wanderlust's destination-selection "
                "agent. Return valid JSON only. Select "
                "destinations, do not research or invent citations."
            ),
            prompt,
            temperature=0.25,
        )

        if not isinstance(result, dict):
            raise ValueError(
                "TravelAgent returned invalid destination data."
            )

        destinations = result.get("destinations")

        if not isinstance(destinations, list):
            raise ValueError(
                "TravelAgent did not return a destinations array."
            )

        clean = []
        seen = set()

        for item in destinations:
            if not isinstance(item, dict):
                continue

            name = str(
                item.get("destination")
                or item.get("name")
                or ""
            ).strip()

            country = str(
                item.get("country") or ""
            ).strip()

            if not name or not country:
                continue

            key = (
                name.casefold(),
                country.casefold()
            )

            if key in seen:
                continue

            seen.add(key)

            clean.append({
                "destination": name,
                "country": country,
                "reason": str(
                    item.get("reason") or ""
                ).strip(),
            })

            if len(clean) == count:
                break

        if len(clean) != count:
            raise ValueError(
                f"TravelAgent returned {len(clean)} valid "
                f"destinations; expected {count}."
            )

        return clean

    # --------------------------------------------------
    # INDEPENDENT BASIC INFORMATION
    # --------------------------------------------------

    def get_basic_information(
        self,
        destination,
        country,
        retry_number=0
    ):
        """
        Retrieve an independent summary for comparison
        against the deep research result.
        """

        suffix = (
            " travel overview culture attractions "
            "visitor information best time to visit"
        )

        if retry_number:
            suffix = (
                " official tourism guide geography "
                "local culture major attractions "
                "visitor essentials"
            )

        query = f"{destination}, {country}{suffix}"

        search = self.tavily.search_raw(
            query,
            max_results=6
        )

        results = search.get("results", [])

        evidence = self._clean_evidence(
            results,
            limit=12
        )

        if not evidence:
            return {
                "basic_info": (
                    "Basic information could not be retrieved "
                    "from the available web results."
                ),
                "key_facts": [],
                "uncertainties": [
                    "No usable independent search evidence."
                ],
                "sources": self._source_list(results),
                "search_query": query,
            }

        prompt = f"""
Destination: {destination}, {country}

Summarize the destination using ONLY the supplied
search evidence.

Never add unsupported facts.

Evidence:
{json.dumps(evidence, ensure_ascii=False)}

Return JSON only:

{{
  "basic_info": "120-180 word overview",
  "key_facts": ["fact"],
  "uncertainties": ["uncertain item"]
}}
"""

        summary = self.llm.chat_json(
            (
                "Summarize travel destinations using only "
                "supplied search evidence. Never add "
                "unsupported facts. Return valid JSON only."
            ),
            prompt,
            temperature=0.1,
        )

        if not isinstance(summary, dict):
            raise ValueError(
                "Basic-information model returned invalid data."
            )

        return {
            "basic_info": str(
                summary.get("basic_info")
                or "Basic information could not be summarized."
            ),
            "key_facts": self._string_list(
                summary.get("key_facts"),
                8
            ),
            "uncertainties": self._string_list(
                summary.get("uncertainties"),
                5
            ),
            "sources": self._source_list(results),
            "search_query": query,
        }

    # --------------------------------------------------
    # DESTINATION ENRICHMENT
    # --------------------------------------------------

    def enrich_destination(
        self,
        destination,
        country,
        basic_info=None
    ):
        """
        Attach destination images and map information.

        Each external provider fails independently.
        """

        warnings = []

        try:
            images = self.pexels.search_destination(
                destination,
                country,
                per_page=4
            )

            if not isinstance(images, list):
                images = []

        except Exception as exc:
            images = []

            warnings.append(
                f"Destination image lookup failed: {exc}"
            )

        try:
            map_data = self.maps.get_destination_map(
                destination,
                country
            )

        except Exception as exc:
            map_data = None

            warnings.append(
                f"Map lookup failed: {exc}"
            )

        if not isinstance(map_data, dict):
            map_data = None

        return {
            "basic_info": basic_info or {},
            "images": images,
            "image_urls": [
                image.get("image_url")
                for image in images
                if (
                    isinstance(image, dict)
                    and image.get("image_url")
                )
            ],
            "map_coordinates": map_data,
            "map_url": (
                map_data or {}
            ).get("map_url"),
            "enrichment_warnings": warnings,
        }

    def enrich_attractions(
        self,
        attractions,
        destination,
        country
    ):
        """
        Add Pexels images to individual attractions.

        Uses bounded concurrency so image requests do not
        grow without limit.

        Original attraction order is preserved.
        """

        from concurrent.futures import (
            ThreadPoolExecutor,
            as_completed
        )

        if not isinstance(attractions, list):
            return []

        output = [
            dict(item)
            for item in attractions
            if isinstance(item, dict)
        ]

        tasks = []

        max_workers = min(
            4,
            len(output)
        )

        if max_workers == 0:
            return output

        def lookup_image(index, attraction):
            existing_image = (
                attraction.get("image_url")
                or attraction.get("imageUrl")
                or attraction.get("photo_url")
                or attraction.get("thumbnail_url")
            )

            if existing_image:
                return index, None, None

            attraction_name = str(
                attraction.get("name")
                or attraction.get("attraction")
                or ""
            ).strip()

            if not attraction_name:
                return index, None, None

            try:
                photos = self.pexels.search_attraction(
                    attraction_name,
                    destination,
                    country,
                    per_page=1
                )

                if not photos:
                    return index, None, None

                photo = photos[0]

                if not isinstance(photo, dict):
                    return index, None, None

                return index, photo, None

            except Exception as exc:
                return index, None, str(exc)

        with ThreadPoolExecutor(
            max_workers=max_workers,
            thread_name_prefix="attraction-image"
        ) as executor:

            for index, attraction in enumerate(output):
                tasks.append(
                    executor.submit(
                        lookup_image,
                        index,
                        attraction
                    )
                )

            for future in as_completed(tasks):
                index, photo, error = future.result()

                if error:
                    print(
                        "[TravelAgent] Attraction image "
                        f"lookup failed for "
                        f"{output[index].get('name', 'unknown')}: "
                        f"{error}"
                    )

                if not photo:
                    continue

                image_url = photo.get("image_url")

                if image_url:
                    output[index]["image_url"] = image_url

                    output[index]["image_urls"] = [
                        image_url
                    ]

                    output[index]["image_source"] = "Pexels"

                    output[index]["image_alt"] = (
                        photo.get("alt")
                        or output[index].get("name")
                        or "Travel attraction"
                    )

        return output

    # --------------------------------------------------
    # CONSISTENCY CHECKING
    # --------------------------------------------------

    def compare_information(
        self,
        destination,
        country,
        deep_research,
        basic_info
    ):
        """
        Compare independent summaries.

        Similarity does not prove factual accuracy.
        """

        deep_summary = str(
            deep_research.get("basic_info")
            or deep_research.get("summary")
            or ""
        )

        basic_summary = str(
            basic_info.get("basic_info") or ""
        )

        # Missing information should not automatically be
        # interpreted as a contradiction.
        if not deep_summary.strip() or not basic_summary.strip():
            return {
                "similar": False,
                "reason": (
                    "Insufficient information to compare "
                    "the two summaries reliably."
                ),
                "contradictions": [],
                "method": "insufficient-evidence",
                "needs_review": True,
            }

        prompt = f"""
Compare these two descriptions of the SAME destination.

Determine whether they are broadly consistent on identity,
geography, destination type, and major characteristics.

Different detail levels are fine.

Flag substantive contradictions, not omissions.

Do not treat missing information as proof of a contradiction.

Destination: {destination}, {country}

Deep research summary:
{deep_summary[:6000]}

Independent basic-information summary:
{basic_summary[:6000]}

Return JSON only:

{{
  "similar": true,
  "reason": "short explanation",
  "contradictions": ["specific contradiction"]
}}
"""

        try:
            result = self.llm.chat_json(
                (
                    "You are a cautious factual-consistency "
                    "checker. Do not claim that similarity "
                    "proves accuracy. Return JSON only."
                ),
                prompt,
                temperature=0.0,
            )

            if not isinstance(result, dict):
                raise ValueError(
                    "Consistency checker returned invalid data."
                )

            similar_value = result.get("similar")

            if not isinstance(similar_value, bool):
                raise ValueError(
                    "Consistency checker did not return "
                    "a valid boolean 'similar' field."
                )

            contradictions = self._string_list(
                result.get("contradictions"),
                6
            )

            return {
                "similar": similar_value,
                "reason": str(
                    result.get("reason") or ""
                ),
                "contradictions": contradictions,
                "method": self.llm.model,
                "needs_review": False,
            }

        except Exception as exc:
            # A failed LLM comparison is not proof that
            # the two sources contradict each other.
            return {
                "similar": None,
                "reason": (
                    "Consistency comparison could not "
                    "be completed."
                ),
                "contradictions": [],
                "method": "comparison-error",
                "warning": str(exc),
                "needs_review": True,
            }

    # --------------------------------------------------
    # HELPERS
    # --------------------------------------------------

    @staticmethod
    def _clean_evidence(
        results,
        limit=12
    ):
        evidence = []

        for item in results:
            if not isinstance(item, dict):
                continue

            content = (
                item.get("raw_content")
                or item.get("content")
                or ""
            )

            content = re.sub(
                r"\s+",
                " ",
                str(content)
            ).strip()

            if not content:
                continue

            evidence.append({
                "title": item.get("title", ""),
                "url": item.get("url", ""),
                "content": content[:1800],
            })

            if len(evidence) >= limit:
                break

        return evidence

    @staticmethod
    def _source_list(results):
        output = []
        seen = set()

        for item in results:
            if not isinstance(item, dict):
                continue

            url = str(
                item.get("url") or ""
            ).strip()

            if not url or url in seen:
                continue

            seen.add(url)

            output.append({
                "title": str(
                    item.get("title") or url
                ),
                "url": url,
            })

        return output[:12]

    @staticmethod
    def _string_list(
        value,
        limit=8
    ):
        if not isinstance(value, list):
            return []

        return [
            str(item).strip()
            for item in value
            if str(item).strip()
        ][:limit]

    @staticmethod
    def _content_words(text):
        stop = {
            "this", "that", "with", "from", "have",
            "been", "there", "their", "about",
            "destination", "travel", "city", "country",
            "known", "also", "which", "where", "while",
            "such", "many", "most", "some", "into",
            "than", "they", "them", "are", "was",
            "were", "and", "the", "for", "you",
            "its", "has", "can"
        }

        return {
            word
            for word in re.findall(
                r"[a-z]{4,}",
                text.lower()
            )
            if word not in stop
        }