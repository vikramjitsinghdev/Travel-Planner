import os
import json
import requests

from typing import Dict, Any, Optional

from dotenv import load_dotenv
from tavily_service import TavilyService


load_dotenv()


class Worker2:
    """
    Worker 2

    LLM:
        Ollama
        gemma4:latest

    Web research:
        TavilyService

    Responsibility:
        Research ONE destination and return the
        standardized research structure.

    Worker 2 does NOT:
        - generate destinations
        - calculate total_budget
        - perform rechecking
        - search for images
        - search maps
        - access databases
        - communicate with other workers
    """

    OLLAMA_API_URL = os.getenv(
        "OLLAMA_API_URL",
        "https://ollama.com/api/chat"
    )

    def __init__(self):

        # =====================================================
        # OLLAMA
        # =====================================================

        self.ollama_api_key = os.getenv(
            "OLLAMA_API_KEY_WORKER"
        )

        self.ollama_model = os.getenv(
            "OLLAMA_WORKER2_MODEL",
            "gemma4:latest"
        )

        if not self.ollama_api_key:
            raise ValueError(
                "OLLAMA_API_KEY_WORKER was not found."
            )

        # =====================================================
        # TAVILY
        # =====================================================

        self.tavily = TavilyService()

    # =========================================================
    # PUBLIC METHOD
    # =========================================================

    def research(
        self,
        destination: str,
        country: Optional[str] = None,
        trip_days: int = 7,
        starting_location: Optional[str] = None
    ) -> Dict[str, Any]:

        if not destination or not destination.strip():
            raise ValueError(
                "Destination cannot be empty."
            )

        destination = destination.strip()

        if country:
            country = country.strip()

        # -----------------------------------------------------
        # 1. Tavily research
        # -----------------------------------------------------

        search_results = self._search_destination(
            destination=destination,
            country=country,
            starting_location=starting_location
        )

        # -----------------------------------------------------
        # 2. Ollama analysis
        # -----------------------------------------------------

        result = self._analyze_with_ollama(
            destination=destination,
            country=country,
            search_results=search_results,
            trip_days=trip_days,
            starting_location=starting_location
        )

        # -----------------------------------------------------
        # 3. Validate
        # -----------------------------------------------------

        result = self._validate_result(
            result=result,
            destination=destination,
            country=country
        )

        return result

    # =========================================================
    # TAVILY RESEARCH
    # =========================================================

    def _search_destination(
        self,
        destination: str,
        country: Optional[str],
        starting_location: Optional[str]
    ):

        if country:
            location = f"{destination}, {country}"
        else:
            location = destination

        queries = [
            f"{location} top major attractions things to do",

            f"{location} average hotel accommodation "
            f"cost per night",

            f"{location} average food cost per day tourist",

            f"{location} average local transportation "
            f"cost per day"
        ]

        if starting_location:
            queries.append(
                f"{starting_location} to {location} "
                f"travel cost flight train bus"
            )
        else:
            queries.append(
                f"{location} travel cost flight train bus"
            )

        return self.tavily.search_many(
            queries=queries,
            max_results=5
        )

    # =========================================================
    # OLLAMA
    # =========================================================

    def _analyze_with_ollama(
        self,
        destination: str,
        country: Optional[str],
        search_results,
        trip_days: int,
        starting_location: Optional[str]
    ):

        research_text = self._format_search_results(
            search_results
        )

        if starting_location:
            origin = starting_location
        else:
            origin = "No starting location provided."

        if country:
            country_text = country
        else:
            country_text = "Determine from the research."

        system_prompt = """
You are Worker 2 in a multi-agent travel research system.

Your task is to analyze web research about ONE destination.

You are a research worker, not the final travel planner.

Return ONLY valid JSON.

Do not return Markdown.
Do not return ```json.
Do not return explanations.
Do not return reasoning.
Do not return additional fields.

Use exactly this structure:

{
    "destination": "string",
    "country": "string",
    "major_attractions": [
        "string",
        "string",
        "string"
    ],
    "traveling_cost": number_or_null,
    "residence_cost": number_or_null,
    "average_food_cost": number_or_null,
    "daily_average_travel_cost": number_or_null,
    "summary": "string"
}

Definitions:

destination:
    The destination being researched.

country:
    The country containing the destination.

major_attractions:
    Exactly 3 major attractions.

traveling_cost:
    One-time estimated cost of reaching the destination
    from the starting location.

residence_cost:
    Total accommodation cost for the requested trip.

average_food_cost:
    Average food cost PER DAY.

daily_average_travel_cost:
    Average local transportation cost PER DAY.

summary:
    Concise useful description of the destination.

Rules:

- All monetary values must be numeric.
- Do not put currency symbols inside numbers.
- Use null when reliable information is unavailable.
- Do not invent unsupported information.
- Do not include total_budget.
- Do not calculate a total budget.
- Return exactly the fields shown above.
"""

        user_prompt = f"""
DESTINATION
===========
{destination}

COUNTRY
=======
{country_text}

TRIP DURATION
============
{trip_days} days

STARTING LOCATION
=================
{origin}

WEB RESEARCH
============

{research_text}

Using the supplied web research, produce the
required standardized JSON object.

Return ONLY the JSON object.
"""

        headers = {
            "Authorization": (
                f"Bearer {self.ollama_api_key}"
            ),
            "Content-Type": "application/json"
        }

        payload = {
            "model": self.ollama_model,

            "messages": [
                {
                    "role": "system",
                    "content": system_prompt
                },
                {
                    "role": "user",
                    "content": user_prompt
                }
            ],

            "format": "json",
            "stream": False,

            "options": {
                "temperature": 0.1
            }
        }

        response = requests.post(
            self.OLLAMA_API_URL,
            headers=headers,
            json=payload,
            timeout=120
        )

        response.raise_for_status()

        data = response.json()

        try:
            content = (
                data["message"]["content"]
            )

        except (
            KeyError,
            TypeError
        ):
            raise RuntimeError(
                "Unexpected Ollama API response."
            )

        return self._extract_json(content)

    # =========================================================
    # FORMAT SEARCH RESULTS
    # =========================================================

    def _format_search_results(
        self,
        search_results
    ):

        sections = []

        for search in search_results:

            section = [
                f"SEARCH QUERY: {search['query']}"
            ]

            for index, result in enumerate(
                search["results"],
                start=1
            ):

                section.append(
                    f"""
RESULT {index}
Title: {result.get("title", "")}
URL: {result.get("url", "")}
Content: {result.get("content", "")}
"""
                )

            sections.append(
                "\n".join(section)
            )

        return (
            "\n\n====================\n\n"
            .join(sections)
        )

    # =========================================================
    # JSON EXTRACTION
    # =========================================================

    def _extract_json(
        self,
        content
    ):

        if not content:
            raise RuntimeError(
                "Worker 2 received an empty Ollama response."
            )

        content = content.strip()

        # -----------------------------------------------------
        # Remove Markdown code fences if returned.
        # -----------------------------------------------------

        if content.startswith("```"):

            lines = content.splitlines()

            lines = lines[1:]

            if (
                lines
                and lines[-1].strip() == "```"
            ):
                lines = lines[:-1]

            content = "\n".join(
                lines
            ).strip()

        # -----------------------------------------------------
        # Direct JSON parsing
        # -----------------------------------------------------

        try:

            result = json.loads(
                content
            )

        except json.JSONDecodeError:

            # -------------------------------------------------
            # Attempt to recover JSON object.
            # -------------------------------------------------

            start = content.find("{")
            end = content.rfind("}")

            if start == -1 or end == -1:

                raise RuntimeError(
                    "Worker 2 could not parse Ollama JSON."
                )

            try:

                result = json.loads(
                    content[start:end + 1]
                )

            except json.JSONDecodeError as exc:

                raise RuntimeError(
                    "Worker 2 received malformed JSON."
                ) from exc

        if not isinstance(result, dict):

            raise RuntimeError(
                "Worker 2 expected a JSON object."
            )

        return result

    # =========================================================
    # VALIDATION
    # =========================================================

    def _validate_result(
        self,
        result,
        destination,
        country
    ):

        required_fields = [
            "destination",
            "country",
            "major_attractions",
            "traveling_cost",
            "residence_cost",
            "average_food_cost",
            "daily_average_travel_cost",
            "summary"
        ]

        # -----------------------------------------------------
        # Check required fields
        # -----------------------------------------------------

        for field in required_fields:

            if field not in result:

                raise RuntimeError(
                    f"Worker 2 missing field: {field}"
                )

        # -----------------------------------------------------
        # Destination comes from ResearchAgent.
        # -----------------------------------------------------

        result["destination"] = destination

        # -----------------------------------------------------
        # Country comes from ResearchAgent when available.
        # -----------------------------------------------------

        if country:
            result["country"] = country

        # -----------------------------------------------------
        # Attractions
        # -----------------------------------------------------

        attractions = result[
            "major_attractions"
        ]

        if not isinstance(
            attractions,
            list
        ):

            raise RuntimeError(
                "major_attractions must be a list."
            )

        if len(attractions) != 3:

            raise RuntimeError(
                "Worker 2 must return exactly "
                "3 attractions."
            )

        # -----------------------------------------------------
        # Numeric fields
        # -----------------------------------------------------

        numeric_fields = [
            "traveling_cost",
            "residence_cost",
            "average_food_cost",
            "daily_average_travel_cost"
        ]

        for field in numeric_fields:

            if result[field] is None:
                continue

            try:

                result[field] = float(
                    result[field]
                )

            except (
                ValueError,
                TypeError
            ):

                result[field] = None

        # -----------------------------------------------------
        # Compatibility protection.
        #
        # Older versions of Worker 2 calculated total_budget.
        # RecheckAgent does not need it at this stage.
        # -----------------------------------------------------

        result.pop(
            "total_budget",
            None
        )

        return result