import json
import os
import requests

from typing import Dict, Any, List, Optional

from dotenv import load_dotenv

from workers.worker_agent1 import Worker1
from workers.worker_agent2 import Worker2
from workers.worker_agent3 import Worker3


load_dotenv()


class ResearchAgent:
    """
    Research Agent

    Model:
        Ollama Qwen3:14b

    Responsibility:
        1. Receive TripRequirements from MoodAgent.
        2. Generate exactly 3 suitable destinations.
        3. Assign one destination to each research worker.
        4. Return the three worker research results.

    ResearchAgent does NOT:
        - perform web searches
        - use Tavily directly
        - search for images
        - search maps
        - calculate total budgets
        - access databases
        - perform rechecking
        - call RecheckAgent
        - structure final frontend output

    Rechecking is handled externally by the main orchestrator.

    Architecture:

        MoodAgent
             |
             v
        TripRequirements
             |
             v
        ResearchAgent
        Qwen3:14b
          /    |    \
         /     |     \
        v      v      v
     Worker1 Worker2 Worker3
     NVIDIA  Gemma    LLM7
         \     |     /
          \    |    /
           v   v   v
        Worker Results
             |
             v
        External Orchestrator
             |
        +----+----+----+
        |    |    |    |
        v    v    v
      Recheck Recheck Recheck
      Gemma26B Gemma26B Gemma26B
    """

    OLLAMA_API_URL = os.getenv(
        "OLLAMA_RESEARCH_API_URL",
        "https://ollama.com/api/chat"
    )

    def __init__(self):
        # =====================================================
        # OLLAMA CONFIGURATION
        # =====================================================

        self.ollama_api_key = os.getenv(
            "OLLAMA_API_KEY_RESEARCH"
        )

        self.ollama_model = os.getenv(
            "OLLAMA_RESEARCH_MODEL",
            "qwen3:14b"
        )

        if not self.ollama_api_key:
            raise ValueError(
                "OLLAMA_API_KEY_RESEARCH was not found."
            )

        # =====================================================
        # WORKERS
        # =====================================================

        self.worker1 = Worker1()
        self.worker2 = Worker2()
        self.worker3 = Worker3()

    # =========================================================
    # PUBLIC METHOD
    # =========================================================

    def research(
        self,
        trip_requirements: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate exactly three destinations from the
        TripRequirements produced by MoodAgent.

        Then assign one destination to each worker.

        Rechecking is NOT performed here.

        Args:
            trip_requirements:
                Output returned by MoodAgent.interpret()

        Returns:
            {
                "destinations": [
                    {
                        "destination": "...",
                        "country": "..."
                    },
                    ...
                ],
                "worker_results": [
                    {...},
                    {...},
                    {...}
                ]
            }
        """

        # -----------------------------------------------------
        # Validate MoodAgent output
        # -----------------------------------------------------

        self._validate_trip_requirements(
            trip_requirements
        )

        # -----------------------------------------------------
        # Generate exactly three destinations
        # -----------------------------------------------------

        destinations = self._generate_destinations(
            trip_requirements
        )

        # -----------------------------------------------------
        # Dispatch destinations to workers
        # -----------------------------------------------------

        worker_results = self._run_workers(
            destinations,
            trip_requirements
        )

        # -----------------------------------------------------
        # Return worker results
        # -----------------------------------------------------

        return {
            "destinations": destinations,
            "worker_results": worker_results
        }

    # =========================================================
    # TRIP REQUIREMENTS VALIDATION
    # =========================================================

    def _validate_trip_requirements(
        self,
        trip_requirements: Dict[str, Any]
    ) -> None:
        """
        Validate the basic structure received from MoodAgent.

        ResearchAgent does not reinterpret or modify the
        TripRequirements.
        """

        if not isinstance(
            trip_requirements,
            dict
        ):
            raise TypeError(
                "trip_requirements must be a dictionary."
            )

        required_fields = [
            "wanted",
            "avoid",
            "constraints",
            "summary"
        ]

        for field in required_fields:

            if field not in trip_requirements:

                raise ValueError(
                    f"TripRequirements missing field: {field}"
                )

        if not isinstance(
            trip_requirements["wanted"],
            list
        ):
            raise TypeError(
                "TripRequirements 'wanted' must be a list."
            )

        if not isinstance(
            trip_requirements["avoid"],
            list
        ):
            raise TypeError(
                "TripRequirements 'avoid' must be a list."
            )

        if not isinstance(
            trip_requirements["constraints"],
            dict
        ):
            raise TypeError(
                "TripRequirements 'constraints' "
                "must be a dictionary."
            )

    # =========================================================
    # DESTINATION GENERATION
    # =========================================================

    def _generate_destinations(
        self,
        trip_requirements: Dict[str, Any]
    ) -> List[Dict[str, str]]:
        """
        Ask Qwen3 to select exactly three destinations
        based on the TripRequirements.

        This method does NOT:
            - search the web
            - use Tavily
            - research destinations
            - calculate costs
            - create itineraries

        Returns:

            [
                {
                    "destination": "...",
                    "country": "..."
                },
                ...
            ]
        """

        requirements_json = json.dumps(
            trip_requirements,
            ensure_ascii=False,
            separators=(",", ":"),
            default=str
        )

        # -----------------------------------------------------
        # System prompt
        # -----------------------------------------------------

        system_prompt = """
You are the Research Agent in a multi-agent travel system.

Your ONLY responsibility is to select exactly THREE
travel destinations based on the TripRequirements provided
by the Mood Agent.

The TripRequirements are authoritative.

You MUST:

1. Respect the user's wanted preferences.
2. Respect the user's avoid preferences.
3. Respect hard constraints.
4. Respect country or region constraints when provided.
5. Respect trip duration when provided.
6. Respect budget constraints when explicitly provided.
7. Respect safety requirements when explicitly provided.
8. Respect transportation preferences when explicitly provided.
9. Respect accommodation preferences when explicitly provided.
10. Select three DIFFERENT destinations.
11. Return exactly three destinations.
12. Include the country for every destination.

You MUST NOT:

- perform web searches
- use Tavily
- claim that you searched the web
- calculate travel costs
- calculate accommodation costs
- calculate food costs
- calculate total budgets
- search for images
- search maps
- create itineraries
- research attractions
- modify the TripRequirements
- invent user preferences
- perform rechecking
- call another agent
- return explanations
- return reasoning
- return Markdown
- return additional fields

The destination selection should be based ONLY on the
TripRequirements provided by the Mood Agent.

Return ONLY valid JSON.

Use EXACTLY this structure:

{
    "destinations": [
        {
            "destination": "string",
            "country": "string"
        },
        {
            "destination": "string",
            "country": "string"
        },
        {
            "destination": "string",
            "country": "string"
        }
    ]
}

There MUST be exactly three destination objects.

The three destinations MUST be different.
"""

        # -----------------------------------------------------
        # User prompt
        # -----------------------------------------------------

        user_prompt = f"""
TRIP REQUIREMENTS FROM MOOD AGENT
=================================

{requirements_json}

Select exactly three suitable destinations.

Return ONLY the required JSON object.
"""

        # -----------------------------------------------------
        # Headers
        # -----------------------------------------------------

        headers = {
            "Authorization": (
                f"Bearer {self.ollama_api_key}"
            ),
            "Content-Type": "application/json"
        }

        # -----------------------------------------------------
        # Payload
        # -----------------------------------------------------

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
                "temperature": 0.2
            }
        }

        # -----------------------------------------------------
        # Ollama request
        # -----------------------------------------------------

        response = requests.post(
            self.OLLAMA_API_URL,
            headers=headers,
            json=payload,
            timeout=120
        )

        response.raise_for_status()

        data = response.json()

        # -----------------------------------------------------
        # Extract response
        # -----------------------------------------------------

        try:

            content = data[
                "message"
            ][
                "content"
            ]

        except (
            KeyError,
            TypeError
        ) as exc:

            raise RuntimeError(
                "Unexpected Ollama response from "
                "ResearchAgent."
            ) from exc

        # -----------------------------------------------------
        # Parse JSON
        # -----------------------------------------------------

        result = self._extract_json(
            content
        )

        # -----------------------------------------------------
        # Validate destinations
        # -----------------------------------------------------

        return self._validate_destinations(
            result
        )

    # =========================================================
    # WORKER DISPATCH
    # =========================================================

    def _run_workers(
        self,
        destinations: List[Dict[str, str]],
        trip_requirements: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Give exactly one destination to each worker.

        Worker 1 -> Destination 1
        Worker 2 -> Destination 2
        Worker 3 -> Destination 3

        Country is passed separately so that each worker can
        use it to make more precise Tavily searches.
        """

        constraints = trip_requirements.get(
            "constraints",
            {}
        )

        # -----------------------------------------------------
        # Trip duration
        # -----------------------------------------------------

        trip_days = constraints.get(
            "duration_days"
        )

        if trip_days is None:
            trip_days = 7

        try:
            trip_days = int(
                trip_days
            )

        except (
            ValueError,
            TypeError
        ):

            trip_days = 7

        if trip_days <= 0:
            trip_days = 7

        # -----------------------------------------------------
        # Starting location
        # -----------------------------------------------------

        starting_location = constraints.get(
            "departure_location"
        )

        # =====================================================
        # WORKER 1
        # =====================================================

        destination1 = destinations[0]

        result1 = self.worker1.research(
            destination=destination1["destination"],
            country=destination1["country"],
            trip_days=trip_days,
            starting_location=starting_location
        )

        # =====================================================
        # WORKER 2
        # =====================================================

        destination2 = destinations[1]

        result2 = self.worker2.research(
            destination=destination2["destination"],
            country=destination2["country"],
            trip_days=trip_days,
            starting_location=starting_location
        )

        # =====================================================
        # WORKER 3
        # =====================================================

        destination3 = destinations[2]

        result3 = self.worker3.research(
            destination=destination3["destination"],
            country=destination3["country"],
            trip_days=trip_days,
            starting_location=starting_location
        )

        return [
            result1,
            result2,
            result3
        ]

    # =========================================================
    # DESTINATION VALIDATION
    # =========================================================

    def _validate_destinations(
        self,
        result: Dict[str, Any]
    ) -> List[Dict[str, str]]:
        """
        Validate the three destinations returned by Qwen3.
        """

        if not isinstance(
            result,
            dict
        ):
            raise RuntimeError(
                "ResearchAgent expected a JSON object."
            )

        destinations = result.get(
            "destinations"
        )

        if not isinstance(
            destinations,
            list
        ):
            raise RuntimeError(
                "ResearchAgent expected a destinations list."
            )

        # -----------------------------------------------------
        # Exactly 3 destinations
        # -----------------------------------------------------

        if len(destinations) != 3:

            raise RuntimeError(
                "ResearchAgent must generate exactly "
                "3 destinations."
            )

        validated = []

        seen = set()

        # -----------------------------------------------------
        # Validate every destination
        # -----------------------------------------------------

        for destination in destinations:

            if not isinstance(
                destination,
                dict
            ):
                raise RuntimeError(
                    "Each destination must be an object."
                )

            # -------------------------------------------------
            # Destination name
            # -------------------------------------------------

            name = destination.get(
                "destination"
            )

            if not isinstance(
                name,
                str
            ) or not name.strip():

                raise RuntimeError(
                    "Destination name cannot be empty."
                )

            # -------------------------------------------------
            # Country
            # -------------------------------------------------

            country = destination.get(
                "country"
            )

            if not isinstance(
                country,
                str
            ) or not country.strip():

                raise RuntimeError(
                    "Destination country cannot be empty."
                )

            name = name.strip()
            country = country.strip()

            # -------------------------------------------------
            # Duplicate detection
            # -------------------------------------------------

            unique_key = (
                f"{name.lower()}|"
                f"{country.lower()}"
            )

            if unique_key in seen:

                raise RuntimeError(
                    "ResearchAgent generated duplicate "
                    "destinations."
                )

            seen.add(
                unique_key
            )

            # -------------------------------------------------
            # Keep ONLY the fields ResearchAgent owns
            # -------------------------------------------------

            validated.append(
                {
                    "destination": name,
                    "country": country
                }
            )

        return validated

    # =========================================================
    # JSON EXTRACTION
    # =========================================================

    def _extract_json(
        self,
        content: str
    ) -> Dict[str, Any]:
        """
        Extract a JSON object from the Qwen3 response.

        Handles:
            - normal JSON
            - Markdown code fences
            - JSON surrounded by accidental text
        """

        if not isinstance(
            content,
            str
        ):

            raise RuntimeError(
                "ResearchAgent received a non-string "
                "Ollama response."
            )

        content = content.strip()

        if not content:

            raise RuntimeError(
                "ResearchAgent received an empty "
                "Ollama response."
            )

        # -----------------------------------------------------
        # Remove Markdown code fence
        # -----------------------------------------------------

        if content.startswith("```"):

            lines = content.splitlines()

            # Remove first line, e.g. ```json
            lines = lines[1:]

            # Remove closing ```
            if (
                lines
                and lines[-1].strip() == "```"
            ):

                lines = lines[:-1]

            content = "\n".join(
                lines
            ).strip()

        # -----------------------------------------------------
        # Normal JSON parsing
        # -----------------------------------------------------

        try:

            result = json.loads(
                content
            )

        except json.JSONDecodeError:

            # -------------------------------------------------
            # Attempt to find JSON object
            # -------------------------------------------------

            start = content.find("{")
            end = content.rfind("}")

            if start == -1 or end == -1:

                raise RuntimeError(
                    "ResearchAgent could not parse "
                    "Ollama JSON."
                )

            try:

                result = json.loads(
                    content[
                        start:end + 1
                    ]
                )

            except json.JSONDecodeError as exc:

                raise RuntimeError(
                    "ResearchAgent received malformed JSON."
                ) from exc

        # -----------------------------------------------------
        # Result must be an object
        # -----------------------------------------------------

        if not isinstance(
            result,
            dict
        ):

            raise RuntimeError(
                "ResearchAgent expected a JSON object."
            )

        return result