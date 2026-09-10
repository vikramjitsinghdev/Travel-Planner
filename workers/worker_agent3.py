import os
import json
import requests

from typing import Dict, Any, Optional

from dotenv import load_dotenv

from tavily_service import TavilyService


load_dotenv()


class Worker3:
    """
    Worker 3

    LLM:
        LLM7 - fast

    Web research:
        TavilyService

    Responsibility:
        Research exactly ONE destination and return a standardized
        destination research result.

    This worker does NOT:
        - Generate destinations
        - Research multiple destinations
        - Perform rechecking
        - Calculate total budget
        - Handle Pexels
        - Handle maps
        - Handle database operations

    Rechecking is performed externally by RecheckAgent after this
    worker finishes.
    """

    def __init__(self):

        # =========================================================
        # LLM7 CONFIGURATION
        # =========================================================

        self.llm7_api_key = os.getenv("LLM7_API_KEY")

        self.llm7_base_url = os.getenv(
            "LLM7_BASE_URL",
            "https://api.llm7.io/v1"
        ).rstrip("/")

        self.llm7_model = os.getenv(
            "LLM7_WORKER3_MODEL",
            "fast"
        )

        self.llm7_json_mode = (
            os.getenv(
                "LLM7_WORKER3_JSON_MODE",
                "false"
            ).lower()
            == "true"
        )

        if not self.llm7_api_key:
            raise ValueError(
                "LLM7_API_KEY was not found."
            )

        # =========================================================
        # TAVILY
        # =========================================================

        self.tavily = TavilyService()

    # =============================================================
    # PUBLIC METHOD
    # =============================================================

    def research(
        self,
        destination: str,
        country: Optional[str] = None,
        trip_days: int = 7,
        starting_location: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Research one destination.

        Parameters:
            destination:
                Destination selected by the Research Agent.

            country:
                Country containing the destination.

            trip_days:
                Requested trip duration.

            starting_location:
                User's departure location.

        Returns:
            Standardized destination research dictionary.
        """

        # ---------------------------------------------------------
        # Validate destination
        # ---------------------------------------------------------

        if not destination or not destination.strip():
            raise ValueError(
                "Destination cannot be empty."
            )

        destination = destination.strip()

        if country:
            country = country.strip()

        # ---------------------------------------------------------
        # 1. Tavily web research
        # ---------------------------------------------------------

        search_results = self._search_destination(
            destination=destination,
            country=country,
            starting_location=starting_location
        )

        # ---------------------------------------------------------
        # 2. LLM7 analysis
        # ---------------------------------------------------------

        result = self._analyze_with_llm7(
            destination=destination,
            country=country,
            search_results=search_results,
            trip_days=trip_days,
            starting_location=starting_location
        )

        # ---------------------------------------------------------
        # 3. Validate standardized result
        # ---------------------------------------------------------

        result = self._validate_result(
            result=result,
            destination=destination,
            country=country
        )

        # ---------------------------------------------------------
        # 4. Safety cleanup
        # ---------------------------------------------------------
        # Worker 3 must NOT return total_budget.
        # Budget calculation belongs outside the workers.

        result.pop("total_budget", None)

        return result

    # =============================================================
    # TAVILY SEARCH
    # =============================================================

    def _search_destination(
        self,
        destination: str,
        country: Optional[str],
        starting_location: Optional[str]
    ):
        """
        Search Tavily for information required by the worker.

        Country is included whenever available so that searches
        are more precise and less ambiguous.
        """

        destination_name = destination

        if country:
            destination_name = f"{destination}, {country}"

        queries = [
            (
                f"{destination_name} top major attractions "
                f"things to do"
            ),
            (
                f"{destination_name} average hotel "
                f"accommodation cost per night"
            ),
            (
                f"{destination_name} average food cost "
                f"per day tourist"
            ),
            (
                f"{destination_name} average local "
                f"transportation cost per day"
            )
        ]

        # ---------------------------------------------------------
        # Traveling cost from starting location
        # ---------------------------------------------------------

        if starting_location:
            queries.append(
                f"{starting_location} to {destination_name} "
                f"travel cost flight train bus"
            )
        else:
            queries.append(
                f"{destination_name} travel cost "
                f"flight train bus"
            )

        return self.tavily.search_many(
            queries,
            max_results=5
        )

    # =============================================================
    # LLM7 ANALYSIS
    # =============================================================

    def _analyze_with_llm7(
        self,
        destination: str,
        country: Optional[str],
        search_results,
        trip_days: int,
        starting_location: Optional[str]
    ):
        """
        Send Tavily research to LLM7 and request the standardized
        Worker 3 output.
        """

        research_text = self._format_search_results(
            search_results
        )

        origin = (
            starting_location
            if starting_location
            else "No starting location provided."
        )

        country_name = (
            country
            if country
            else "Country not explicitly provided."
        )

        # ---------------------------------------------------------
        # System prompt
        # ---------------------------------------------------------

        system_prompt = """
You are Worker 3 in a multi-agent travel research system.

Your job is to analyze web research about ONE destination.

The Research Agent has already selected the destination.
Do NOT select another destination.

Return ONLY one valid JSON object.

Do not return Markdown.
Do not return ```json.
Do not return explanations.
Do not return reasoning.
Do not return additional fields.

Use EXACTLY this structure:

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

traveling_cost:
    One-time estimated cost of reaching the destination
    from the provided starting location.

residence_cost:
    Total estimated accommodation cost for the requested
    trip duration.

average_food_cost:
    Average food cost PER DAY.

daily_average_travel_cost:
    Average local transportation cost PER DAY.

major_attractions:
    Exactly 3 major attractions in the destination.

Important rules:

1. Use the provided destination.
2. Use the provided country when available.
3. Use the web research as the primary source of information.
4. Do not invent unsupported prices.
5. If reliable information is unavailable, use null.
6. Numeric cost fields must contain numbers or null.
7. major_attractions must contain exactly 3 items.
8. Keep the summary concise and useful.
9. Do not calculate or return total_budget.
10. Do not add any fields outside the required structure.

Return ONLY the JSON object.
"""

        # ---------------------------------------------------------
        # User prompt
        # ---------------------------------------------------------

        user_prompt = f"""
Destination:
{destination}

Country:
{country_name}

Trip duration:
{trip_days} days

Starting location:
{origin}

WEB RESEARCH
============

{research_text}

Analyze the research and return ONLY the required JSON object.
"""

        # ---------------------------------------------------------
        # LLM7 request headers
        # ---------------------------------------------------------

        headers = {
            "Authorization": (
                f"Bearer {self.llm7_api_key}"
            ),
            "Content-Type": "application/json"
        }

        # ---------------------------------------------------------
        # Request payload
        # ---------------------------------------------------------

        payload = {
            "model": self.llm7_model,

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

            "temperature": 0.1,

            "stream": False
        }

        # ---------------------------------------------------------
        # Optional JSON mode
        # ---------------------------------------------------------

        if self.llm7_json_mode:
            payload["response_format"] = {
                "type": "json_object"
            }

        # ---------------------------------------------------------
        # Send request
        # ---------------------------------------------------------

        response = requests.post(
            f"{self.llm7_base_url}/chat/completions",
            headers=headers,
            json=payload,
            timeout=120
        )

        response.raise_for_status()

        data = response.json()

        # ---------------------------------------------------------
        # Extract LLM7 response
        # ---------------------------------------------------------

        try:
            content = (
                data["choices"][0]
                ["message"]["content"]
            )

        except (
            KeyError,
            IndexError,
            TypeError
        ) as exc:

            raise RuntimeError(
                "Unexpected LLM7 API response."
            ) from exc

        return self._extract_json(content)

    # =============================================================
    # FORMAT TAVILY RESULTS
    # =============================================================

    def _format_search_results(
        self,
        search_results
    ) -> str:
        """
        Convert Tavily results into a readable text block
        for LLM7.
        """

        sections = []

        for search in search_results:

            query = search.get(
                "query",
                ""
            )

            results = search.get(
                "results",
                []
            )

            section = [
                f"SEARCH QUERY: {query}"
            ]

            for index, result in enumerate(
                results,
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

        return "\n\n====================\n\n".join(
            sections
        )

    # =============================================================
    # JSON EXTRACTION
    # =============================================================

    def _extract_json(
        self,
        content: str
    ) -> Dict[str, Any]:
        """
        Extract a JSON object from the LLM7 response.

        Handles both clean JSON and accidental Markdown
        code fences.
        """

        if not isinstance(content, str):
            raise RuntimeError(
                "Worker 3 received a non-string LLM7 response."
            )

        content = content.strip()

        # ---------------------------------------------------------
        # Remove Markdown code fence
        # ---------------------------------------------------------

        if content.startswith("```"):

            lines = content.splitlines()

            # Remove first line such as ```json
            lines = lines[1:]

            # Remove closing ```
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]

            content = "\n".join(
                lines
            ).strip()

        # ---------------------------------------------------------
        # Try normal JSON parsing
        # ---------------------------------------------------------

        try:

            result = json.loads(
                content
            )

        except json.JSONDecodeError:

            # -----------------------------------------------------
            # Attempt to locate JSON object inside extra text
            # -----------------------------------------------------

            start = content.find("{")
            end = content.rfind("}")

            if start == -1 or end == -1:

                raise RuntimeError(
                    "Worker 3 could not parse LLM7 JSON."
                )

            try:

                result = json.loads(
                    content[start:end + 1]
                )

            except json.JSONDecodeError as exc:

                raise RuntimeError(
                    "Worker 3 received malformed JSON."
                ) from exc

        # ---------------------------------------------------------
        # JSON must be an object
        # ---------------------------------------------------------

        if not isinstance(result, dict):

            raise RuntimeError(
                "Worker 3 expected a JSON object."
            )

        return result

    # =============================================================
    # VALIDATION
    # =============================================================

    def _validate_result(
        self,
        result: Dict[str, Any],
        destination: str,
        country: Optional[str]
    ) -> Dict[str, Any]:
        """
        Validate and normalize the standardized Worker 3 result.
        """

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

        # ---------------------------------------------------------
        # Required fields
        # ---------------------------------------------------------

        for field in required_fields:

            if field not in result:

                raise RuntimeError(
                    f"Worker 3 missing field: {field}"
                )

        # ---------------------------------------------------------
        # Destination
        # ---------------------------------------------------------
        # The Research Agent is authoritative about which
        # destination Worker 3 was assigned.

        result["destination"] = destination

        # ---------------------------------------------------------
        # Country
        # ---------------------------------------------------------

        if country:
            result["country"] = country

        elif not isinstance(
            result["country"],
            str
        ):

            result["country"] = ""

        # ---------------------------------------------------------
        # Attractions
        # ---------------------------------------------------------

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
                "Worker 3 must return exactly 3 attractions."
            )

        # ---------------------------------------------------------
        # Validate attraction values
        # ---------------------------------------------------------

        for attraction in attractions:

            if not isinstance(
                attraction,
                str
            ):

                raise RuntimeError(
                    "Each major attraction must be a string."
                )

        # ---------------------------------------------------------
        # Numeric fields
        # ---------------------------------------------------------

        numeric_fields = [
            "traveling_cost",
            "residence_cost",
            "average_food_cost",
            "daily_average_travel_cost"
        ]

        for field in numeric_fields:

            value = result[field]

            if value is None:
                continue

            try:

                numeric_value = float(
                    value
                )

                # Reject NaN / infinity
                if not (
                    numeric_value
                    == numeric_value
                ):

                    result[field] = None

                elif numeric_value < 0:

                    result[field] = None

                else:

                    result[field] = numeric_value

            except (
                ValueError,
                TypeError
            ):

                result[field] = None

        # ---------------------------------------------------------
        # Summary
        # ---------------------------------------------------------

        if not isinstance(
            result["summary"],
            str
        ):

            result["summary"] = str(
                result["summary"]
            )

        # ---------------------------------------------------------
        # Remove any accidental extra field
        # ---------------------------------------------------------

        result.pop(
            "total_budget",
            None
        )

        return result