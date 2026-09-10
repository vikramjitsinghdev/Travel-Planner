import json
import os
from concurrent.futures import ThreadPoolExecutor, as_completed

from dotenv import load_dotenv
from google import genai

from ai.research_agent import ResearchAgent
import pexels_service


load_dotenv()


class TravelAgent:
    """
    TravelAgent is responsible for:

    1. Receiving the user's travel request.
    2. Asking Gemini to select EXACTLY 3 destinations.
    3. Sending those 3 destinations to ResearchAgent.
    4. Combining research + images with the destinations.
    5. Returning one consistent destination schema.

    TravelAgent does NOT perform web research itself.
    ResearchAgent owns the research process.
    """

    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")

        if not self.api_key:
            raise RuntimeError(
                "GEMINI_API_KEY is not configured."
            )

        self.model = (
            os.getenv("GEMINI_TRAVEL_MODEL")
            or os.getenv("GEMINI_MODEL")
            or "gemini-3.6-flash"
        )

        self.client = genai.Client(api_key=self.api_key)

        # ResearchAgent owns all research workers and Ollama verification.
        self.research_agent = ResearchAgent()

        self.max_workers = 3

    # ============================================================
    # PUBLIC API
    # ============================================================

    def get_trip_recommendations(
        self,
        user_input,
        preferences=None,
        budget=None,
        trip_information=None,
    ):
        """
        Main entry point used by main.py.

        Returns:

        {
            "success": True,
            "candidates": [...],
            "research": {...},
            "travel_options": [...]
        }
        """

        try:
            candidates = self.find_candidates(
                user_input=user_input,
                preferences=preferences,
                budget=budget,
                trip_information=trip_information,
            )

            if not candidates:
                return {
                    "success": False,
                    "error": "Gemini did not return any destinations.",
                    "candidates": [],
                    "research": {},
                    "travel_options": [],
                }

            if len(candidates) != 3:
                return {
                    "success": False,
                    "error": (
                        f"TravelAgent requires exactly 3 destinations, "
                        f"but Gemini returned {len(candidates)}."
                    ),
                    "candidates": candidates,
                    "research": {},
                    "travel_options": [],
                }

            result = self.research_destinations(
                candidates=candidates,
                trip_requirements=preferences,
                trip_information=trip_information,
            )

            return result

        except Exception as e:
            print(f"[TravelAgent] ERROR: {e}")

            return {
                "success": False,
                "error": str(e),
                "candidates": [],
                "research": {},
                "travel_options": [],
            }

    # ============================================================
    # DESTINATION SELECTION
    # ============================================================

    def find_candidates(
        self,
        user_input,
        preferences=None,
        budget=None,
        trip_information=None,
    ):
        """
        Ask Gemini to select exactly 3 destinations.

        IMPORTANT:
        This method only selects destinations.
        It does not research them.
        """

        preferences = preferences or {}
        trip_information = trip_information or {}

        prompt = f"""
You are the destination-selection component of an AI travel planner.

Your ONLY job is to select EXACTLY 3 destinations that best fit the
traveler's requirements.

DO NOT perform detailed research.
DO NOT invent hotels, flights, prices, weather statistics, or schedules.
DO NOT return more or fewer than 3 destinations.

USER REQUEST:
{user_input}

MOOD / TRAVEL REQUIREMENTS:
{json.dumps(preferences, indent=2, ensure_ascii=False)}

BASIC TRIP INFORMATION:
{json.dumps(trip_information, indent=2, ensure_ascii=False)}

BUDGET:
{json.dumps(budget, indent=2, ensure_ascii=False)}

Return ONLY valid JSON.

Required format:

{{
    "candidates": [
        {{
            "name": "Destination name",
            "country": "Country",
            "description": "Short description",
            "reason": "Why this destination matches the traveler",
            "research_priority": 1
        }},
        {{
            "name": "Destination name",
            "country": "Country",
            "description": "Short description",
            "reason": "Why this destination matches the traveler",
            "research_priority": 2
        }},
        {{
            "name": "Destination name",
            "country": "Country",
            "description": "Short description",
            "reason": "Why this destination matches the traveler",
            "research_priority": 3
        }}
    ]
}}

Rules:

- Exactly 3 candidates.
- Every candidate MUST have a non-empty "name".
- Every candidate MUST have a non-empty "country".
- Do not use "destination" instead of "name".
- Keep descriptions concise.
- Do not fabricate detailed factual information.
"""

        response = self.client.models.generate_content(
            model=self.model,
            contents=prompt,
        )

        raw = self._extract_response_text(response)

        data = self._parse_json(raw)

        candidates = data.get("candidates", [])

        if not isinstance(candidates, list):
            raise ValueError(
                "Gemini response contains an invalid candidates field."
            )

        if len(candidates) != 3:
            raise ValueError(
                f"Gemini returned {len(candidates)} candidates instead of exactly 3."
            )

        normalized = []

        for index, candidate in enumerate(candidates, start=1):

            if not isinstance(candidate, dict):
                raise ValueError(
                    f"Candidate {index} is not a JSON object."
                )

            # Canonical field = name.
            name = (
                candidate.get("name")
                or candidate.get("destination")
                or ""
            ).strip()

            country = (
                candidate.get("country")
                or ""
            ).strip()

            if not name:
                raise ValueError(
                    f"Candidate {index} has no valid name."
                )

            if not country:
                raise ValueError(
                    f"Candidate {index} has no valid country."
                )

            normalized_candidate = {
                "name": name,
                "country": country,
                "description": (
                    candidate.get("description")
                    or ""
                ).strip(),
                "reason": (
                    candidate.get("reason")
                    or ""
                ).strip(),
                "research_priority": (
                    candidate.get("research_priority")
                    or index
                ),
            }

            # Compatibility alias.
            normalized_candidate["destination"] = name

            normalized.append(normalized_candidate)

        return normalized

    # ============================================================
    # RESEARCH
    # ============================================================

    def research_destinations(
        self,
        candidates,
        trip_requirements=None,
        trip_information=None,
    ):
        """
        Send exactly the 3 selected destinations to ResearchAgent.

        Pexels and research run concurrently.
        """

        if len(candidates) != 3:
            raise ValueError(
                "research_destinations requires exactly 3 candidates."
            )

        trip_requirements = trip_requirements or {}
        trip_information = trip_information or {}

        print("\n[TravelAgent] Starting ResearchAgent...")

        research_result = None
        image_results = {}

        # --------------------------------------------------------
        # ResearchAgent
        # --------------------------------------------------------

        try:
            research_result = self.research_agent.research(
                destinations=candidates,
                trip_requirements=trip_requirements,
                trip_information=trip_information,
            )

        except TypeError:
            # Compatibility with an older ResearchAgent signature.
            research_result = self.research_agent.research(
                candidates,
                trip_requirements,
            )

        except Exception as e:
            print(
                f"[TravelAgent] ResearchAgent failed: {e}"
            )

            research_result = {
                "success": False,
                "destinations": {},
                "workers": {},
                "verification": {},
                "errors": [str(e)],
            }

        # --------------------------------------------------------
        # Pexels
        # --------------------------------------------------------

        with ThreadPoolExecutor(max_workers=3) as executor:

            futures = {}

            for index, candidate in enumerate(candidates, start=1):

                future = executor.submit(
                    self._get_destination_image,
                    candidate["name"],
                    candidate["country"],
                )

                futures[index] = future

            for index, future in futures.items():

                try:
                    image_results[index] = future.result()

                except Exception as e:
                    print(
                        f"[TravelAgent] Pexels failed for destination "
                        f"{index}: {e}"
                    )

                    image_results[index] = None

        # --------------------------------------------------------
        # Combine
        # --------------------------------------------------------

        return self._combine_results(
            candidates=candidates,
            research_result=research_result,
            image_results=image_results,
        )

    # ============================================================
    # PEXELS
    # ============================================================

    def _get_destination_image(self, name, country):
        """
        Retrieve a Pexels image.

        Failure is non-fatal.
        """

        try:

            query = f"{name} {country}"

            # Support the existing pexels_service implementation.
            if hasattr(pexels_service, "search_destination_image"):
                return pexels_service.search_destination_image(query)

            if hasattr(pexels_service, "get_destination_image"):
                return pexels_service.get_destination_image(
                    name,
                    country,
                )

            if hasattr(pexels_service, "search_images"):
                results = pexels_service.search_images(query)

                if results:
                    return results[0]

            return None

        except Exception as e:
            print(
                f"[TravelAgent] Image lookup failed for "
                f"{name}: {e}"
            )

            return None

    # ============================================================
    # COMBINE
    # ============================================================

    def _combine_results(
        self,
        candidates,
        research_result,
        image_results,
    ):
        """
        Combine:

        Gemini candidate
        +
        Worker research
        +
        Pexels image

        into one canonical destination object.
        """

        workers = {}

        if isinstance(research_result, dict):
            workers = research_result.get("workers", {}) or {}

        final_destinations = []

        for index, candidate in enumerate(candidates, start=1):

            worker_key = f"worker_{index}"

            worker_result = workers.get(
                worker_key,
                {}
            )

            if not isinstance(worker_result, dict):
                worker_result = {}

            worker_success = bool(
                worker_result.get("success")
            )

            research_data = worker_result.get(
                "research"
            )

            if research_data is None:
                research_data = worker_result.get(
                    "data"
                )

            if research_data is None:
                research_data = {}

            # ----------------------------------------------------
            # CANONICAL SCHEMA
            # ----------------------------------------------------

            destination = {
                "rank": index,

                # CANONICAL NAME
                "name": candidate["name"],

                "country": candidate["country"],

                "description": candidate.get(
                    "description",
                    ""
                ),

                "reason": candidate.get(
                    "reason",
                    ""
                ),

                "research_priority": candidate.get(
                    "research_priority",
                    index
                ),

                "image": image_results.get(index),

                "research": research_data,

                "research_success": worker_success,

                "worker": worker_key,
            }

            # ----------------------------------------------------
            # BACKWARD COMPATIBILITY
            # ----------------------------------------------------

            destination["destination"] = destination["name"]

            final_destinations.append(destination)

        successful_workers = sum(
            1
            for destination in final_destinations
            if destination["research_success"]
        )

        research_success = (
            successful_workers == 3
        )

        overall_success = (
            len(final_destinations) == 3
        )

        result = {
            "success": overall_success,

            "candidates": final_destinations,

            # Same objects under travel_options for existing code.
            "travel_options": final_destinations,

            "research": research_result,

            "research_success": research_success,

            "successful_workers": successful_workers,

            "worker_count": 3,
        }

        return result

    # ============================================================
    # SELECTED TRIP
    # ============================================================

    def build_selected_trip(
        self,
        selected_destination,
        trip_requirements=None,
        trip_information=None,
    ):
        """
        Build the selected destination response.

        This does not perform another research cycle.
        """

        trip_requirements = trip_requirements or {}
        trip_information = trip_information or {}

        if isinstance(selected_destination, dict):

            selected = dict(selected_destination)

        else:

            selected = {
                "name": str(selected_destination),
                "country": "",
                "description": "",
                "reason": "",
                "research": {},
            }

        # Canonical name.
        if not selected.get("name"):
            selected["name"] = selected.get(
                "destination",
                ""
            )

        # Compatibility alias.
        selected["destination"] = selected["name"]

        selected["trip_information"] = trip_information
        selected["trip_requirements"] = trip_requirements

        return selected

    # ============================================================
    # UTILITIES
    # ============================================================

    @staticmethod
    def _extract_response_text(response):

        if response is None:
            raise ValueError(
                "Gemini returned no response."
            )

        # New Google GenAI response.
        text = getattr(
            response,
            "text",
            None,
        )

        if text:
            return text

        # Older response style.
        output_text = getattr(
            response,
            "output_text",
            None,
        )

        if output_text:
            return output_text

        # Last resort.
        if isinstance(response, str):
            return response

        raise ValueError(
            "Could not extract text from Gemini response."
        )

    @staticmethod
    def _parse_json(raw):

        if not raw:
            raise ValueError(
                "Gemini returned an empty response."
            )

        raw = raw.strip()

        # Remove markdown JSON fences.
        if raw.startswith("```"):
            raw = raw.replace(
                "```json",
                "",
                1,
            )

            raw = raw.replace(
                "```",
                "",
            )

            raw = raw.strip()

        try:
            return json.loads(raw)

        except json.JSONDecodeError:

            # Try to recover JSON object from surrounding text.
            start = raw.find("{")
            end = raw.rfind("}")

            if start != -1 and end != -1 and end > start:

                extracted = raw[
                    start:end + 1
                ]

                return json.loads(extracted)

            raise ValueError(
                "Gemini returned invalid JSON."
            )