import json
import os
from concurrent.futures import ThreadPoolExecutor, as_completed

from dotenv import load_dotenv
from google import genai

from ai.research_agent import ResearchAgent
from pexels_service import get_destination_image


load_dotenv()


class TravelAgent:
    """
    WANDERLUST MAIN TRAVEL ORCHESTRATOR

    Flow
    ----

        User Input
             ↓
        MoodAgent
             ↓
        TripRequirements
             ↓
        TravelAgent / Gemini
             ↓
        EXACTLY 3 DESTINATIONS
             ↓
        ResearchAgent
          ├── Worker 1 → Destination 1
          ├── Worker 2 → Destination 2
          └── Worker 3 → Destination 3
             ↓
        Gemma verification
             ↓
        Pexels images
             ↓
        Combined results
             ↓
        main.py / Flask
             ↓
        Frontend

    TravelAgent does NOT:
        - directly call workers
        - research destinations
        - rank five destinations
        - perform a second destination-selection stage
        - create an itinerary during recommendations
    """

    # ==========================================================
    # INITIALIZATION
    # ==========================================================

    def __init__(self):

        load_dotenv()

        api_key = os.getenv(
            "GEMINI_API_KEY"
        )

        if not api_key:
            raise ValueError(
                "GEMINI_API_KEY is not set."
            )

        self.client = genai.Client(
            api_key=api_key
        )

        self.model = os.getenv(
            "GEMINI_MAIN_MODEL",
            "gemini-3.6-flash"
        )

        self.research_agent = ResearchAgent()

        self.pexels_enabled = bool(
            os.getenv(
                "PEXELS_API_KEY"
            )
        )

    # ==========================================================
    # GEMINI: FIND EXACTLY 3
    # ==========================================================

    def find_candidates(
        self,
        user_input,
        preferences,
        budget,
        trip_information=None,
    ):
        """
        Gemini selects exactly three destinations.

        Gemini does NOT research them.
        """

        if not isinstance(
            user_input,
            str
        ) or not user_input.strip():

            raise ValueError(
                "user_input must be a non-empty string."
            )

        if not isinstance(
            preferences,
            dict
        ):
            raise TypeError(
                "preferences must be a dictionary."
            )

        if not isinstance(
            budget,
            dict
        ):
            raise TypeError(
                "budget must be a dictionary."
            )

        if trip_information is None:
            trip_information = {}

        if not isinstance(
            trip_information,
            dict
        ):
            raise TypeError(
                "trip_information must be a dictionary."
            )

        prompt = f"""
You are the main destination-selection AI for Wanderlust.

Select EXACTLY THREE travel destinations.

You are NOT the research agent.

Do NOT browse the internet.

Do NOT provide current prices.
Do NOT provide current availability.
Do NOT claim anything is booked.
Do NOT create an itinerary.

Use the user's request and structured requirements to select
the three strongest destination options.

USER REQUEST:
{user_input}

TRIP REQUIREMENTS:
{json.dumps(
    preferences,
    ensure_ascii=False,
    default=str
)}

TRIP INFORMATION:
{json.dumps(
    trip_information,
    ensure_ascii=False,
    default=str
)}

BUDGET:
{json.dumps(
    budget,
    ensure_ascii=False,
    default=str
)}

Return ONLY JSON in this exact structure:

{{
    "research_strategy": "",
    "candidates": [
        {{
            "name": "",
            "country": "",
            "reason": "",
            "description": "",
            "research_priority": 1
        }},
        {{
            "name": "",
            "country": "",
            "reason": "",
            "description": "",
            "research_priority": 2
        }},
        {{
            "name": "",
            "country": "",
            "reason": "",
            "description": "",
            "research_priority": 3
        }}
    ]
}}

There MUST be exactly three unique destinations.
"""

        response = self.client.interactions.create(
            model=self.model,
            input=prompt,
        )

        content = getattr(
            response,
            "output_text",
            None
        )

        if not content:
            raise ValueError(
                "Gemini returned an empty response."
            )

        result = self._parse_json_object(
            content,
            "candidate destinations"
        )

        candidates = result.get(
            "candidates"
        )

        if not isinstance(
            candidates,
            list
        ):
            raise ValueError(
                "Gemini did not return a candidates list."
            )

        cleaned = []
        seen = set()

        for candidate in candidates:

            if not isinstance(
                candidate,
                dict
            ):
                continue

            name = str(
                candidate.get(
                    "name",
                    ""
                )
            ).strip()

            country = str(
                candidate.get(
                    "country",
                    ""
                )
            ).strip()

            if not name or not country:
                continue

            key = (
                name.lower(),
                country.lower()
            )

            if key in seen:
                continue

            seen.add(key)

            cleaned.append({
                "name": name,
                "country": country,
                "reason": str(
                    candidate.get(
                        "reason",
                        ""
                    )
                ).strip(),
                "description": str(
                    candidate.get(
                        "description",
                        ""
                    )
                ).strip(),
                "research_priority": len(
                    cleaned
                ) + 1,
            })

        if len(cleaned) != 3:
            raise ValueError(
                "Gemini must return exactly three unique "
                f"destinations. Got {len(cleaned)}."
            )

        return {
            "research_strategy": str(
                result.get(
                    "research_strategy",
                    ""
                )
            ).strip(),

            "candidates": cleaned,
        }

    # ==========================================================
    # RESEARCH + PEXELS
    # ==========================================================

    def research_destinations(
        self,
        candidates,
        trip_requirements=None,
    ):
        """
        Run:

            ResearchAgent
            +
            Pexels

        concurrently.

        ResearchAgent internally runs the three workers
        concurrently.
        """

        if not isinstance(
            candidates,
            list
        ):
            raise TypeError(
                "candidates must be a list."
            )

        if len(candidates) != 3:
            raise ValueError(
                "Exactly three candidates are required."
            )

        if trip_requirements is None:
            trip_requirements = {}

        normalized = []

        seen = set()

        for candidate in candidates:

            if not isinstance(
                candidate,
                dict
            ):
                raise ValueError(
                    "Each candidate must be a dictionary."
                )

            name = str(
                candidate.get(
                    "name",
                    ""
                )
            ).strip()

            country = str(
                candidate.get(
                    "country",
                    ""
                )
            ).strip()

            if not name:
                raise ValueError(
                    "Candidate has no destination name."
                )

            key = (
                name.lower(),
                country.lower()
            )

            if key in seen:
                raise ValueError(
                    f"Duplicate destination: {name}"
                )

            seen.add(key)

            normalized.append({
                "name": name,
                "country": country,
                "reason": str(
                    candidate.get(
                        "reason",
                        ""
                    )
                ).strip(),
                "description": str(
                    candidate.get(
                        "description",
                        ""
                    )
                ).strip(),
                "research_priority": candidate.get(
                    "research_priority"
                ),
            })

        # ------------------------------------------------------
        # Research and Pexels are independent.
        # ------------------------------------------------------

        with ThreadPoolExecutor(
            max_workers=2
        ) as executor:

            research_future = executor.submit(
                self.research_agent.research,
                normalized,
                trip_requirements,
            )

            image_future = executor.submit(
                self._get_destination_images,
                normalized,
            )

            try:
                research_result = (
                    research_future.result()
                )

            except Exception as error:

                research_result = {
                    "success": False,
                    "destinations": {},
                    "workers": {},
                    "verification": {},
                    "errors": [
                        f"ResearchAgent error: {error}"
                    ],
                }

            try:
                image_results = (
                    image_future.result()
                )

            except Exception as error:

                image_results = {}

                for candidate in normalized:

                    key = self._destination_key(
                        candidate["name"],
                        candidate["country"],
                    )

                    image_results[key] = {
                        "image_url": None,
                        "pexels_url": None,
                        "photographer": None,
                        "error": str(error),
                    }

        return self._combine_results(
            normalized,
            research_result,
            image_results,
        )

    # ==========================================================
    # PEXELS
    # ==========================================================

    def _get_destination_images(
        self,
        candidates,
    ):
        results = {}

        if not self.pexels_enabled:

            for candidate in candidates:

                key = self._destination_key(
                    candidate["name"],
                    candidate["country"],
                )

                results[key] = {
                    "image_url": None,
                    "pexels_url": None,
                    "photographer": None,
                    "error": "PEXELS_API_KEY is not set.",
                }

            return results

        with ThreadPoolExecutor(
            max_workers=3
        ) as executor:

            futures = {
                executor.submit(
                    self._get_single_image,
                    candidate,
                ): candidate
                for candidate in candidates
            }

            for future in as_completed(
                futures
            ):

                candidate = futures[future]

                key = self._destination_key(
                    candidate["name"],
                    candidate["country"],
                )

                try:
                    results[key] = future.result()

                except Exception as error:

                    results[key] = {
                        "image_url": None,
                        "pexels_url": None,
                        "photographer": None,
                        "error": str(error),
                    }

        return results

    @staticmethod
    def _get_single_image(
        candidate
    ):

        result = get_destination_image(
            destination_name=candidate["name"],
            country=candidate["country"],
        )

        if not isinstance(
            result,
            dict
        ):
            return {
                "image_url": None,
                "pexels_url": None,
                "photographer": None,
            }

        return {
            "image_url": result.get(
                "image_url"
            ),
            "pexels_url": result.get(
                "pexels_url"
            ),
            "photographer": result.get(
                "photographer"
            ),
        }

    # ==========================================================
    # COMBINE EVERYTHING
    # ==========================================================

    def _combine_results(
        self,
        candidates,
        research_result,
        image_results,
    ):
        """
        IMPORTANT FIX:

        ResearchAgent's worker results are stored as:

            research_result["workers"]["worker_1"]
            research_result["workers"]["worker_2"]
            research_result["workers"]["worker_3"]

        The old TravelAgent incorrectly expected the detailed
        worker reports to already be inside:

            research_result["destinations"]

        This version maps them correctly.
        """

        if not isinstance(
            research_result,
            dict
        ):
            research_result = {
                "success": False,
                "workers": {},
                "verification": {},
                "errors": [
                    "Invalid ResearchAgent result."
                ],
            }

        workers = research_result.get(
            "workers",
            {}
        )

        if not isinstance(
            workers,
            dict
        ):
            workers = {}

        combined = []

        for index, candidate in enumerate(
            candidates,
            start=1
        ):

            worker_key = (
                f"worker_{index}"
            )

            research = workers.get(
                worker_key,
                {}
            )

            if not isinstance(
                research,
                dict
            ):
                research = {}

            image_key = self._destination_key(
                candidate["name"],
                candidate["country"],
            )

            image = image_results.get(
                image_key,
                {
                    "image_url": None,
                    "pexels_url": None,
                    "photographer": None,
                },
            )

            combined.append({
                "rank": index,

                "destination": candidate[
                    "name"
                ],

                "country": candidate[
                    "country"
                ],

                "reason": candidate.get(
                    "reason",
                    ""
                ),

                "description": candidate.get(
                    "description",
                    ""
                ),

                "research_priority": candidate.get(
                    "research_priority",
                    index,
                ),

                "image": {
                    "image_url": image.get(
                        "image_url"
                    ),
                    "pexels_url": image.get(
                        "pexels_url"
                    ),
                    "photographer": image.get(
                        "photographer"
                    ),
                },

                # Actual worker research.
                "research": research,
            })

        # ------------------------------------------------------
        # IMPORTANT:
        #
        # success means the actual worker research completed.
        #
        # Gemma verification failure does NOT destroy research.
        # ------------------------------------------------------

        worker_success = all(
            isinstance(
                workers.get(
                    f"worker_{i}"
                ),
                dict,
            )
            and workers[
                f"worker_{i}"
            ].get(
                "success",
                False
            )
            for i in range(1, 4)
        )

        return {
            "success": worker_success,

            "destinations": combined,

            "research": {
                "success": worker_success,

                "workers": workers,

                "verification": research_result.get(
                    "verification",
                    {},
                ),

                "errors": research_result.get(
                    "errors",
                    [],
                ),
            },
        }

    # ==========================================================
    # COMPLETE RECOMMENDATION PIPELINE
    # ==========================================================

    def get_trip_recommendations(
        self,
        user_input,
        preferences,
        budget,
        trip_information=None,
    ):
        """
        Complete recommendation pipeline.

        1. Gemini selects exactly 3.
        2. ResearchAgent researches exactly those 3.
        3. Workers run concurrently.
        4. Gemma performs lightweight QC.
        5. Pexels gets images concurrently.
        6. Results are combined.
        """

        candidate_result = self.find_candidates(
            user_input=user_input,
            preferences=preferences,
            budget=budget,
            trip_information=trip_information,
        )

        candidates = candidate_result[
            "candidates"
        ]

        research_requirements = {
            "preferences": preferences,
            "budget": budget,
            "trip_information": (
                trip_information
                if isinstance(
                    trip_information,
                    dict
                )
                else {}
            ),
            "user_request": user_input,
        }

        enriched = self.research_destinations(
            candidates=candidates,
            trip_requirements=research_requirements,
        )

        return {
            "success": enriched.get(
                "success",
                False,
            ),

            "research_strategy": candidate_result.get(
                "research_strategy",
                "",
            ),

            "destinations": enriched.get(
                "destinations",
                [],
            ),

            "research": enriched.get(
                "research",
                {},
            ),
        }

    # ==========================================================
    # SELECTED TRIP
    # ==========================================================

    def build_selected_trip(
        self,
        selected_destination,
        user_input,
        preferences,
        budget,
        research=None,
        map_data=None,
        trip_information=None,
    ):
        """
        Generate cost information after the user selects
        one of the three destinations.

        This remains separate from recommendation generation.
        """

        research = (
            research
            if isinstance(research, dict)
            else {}
        )

        map_data = (
            map_data
            if isinstance(map_data, list)
            else []
        )

        trip_information = (
            trip_information
            if isinstance(trip_information, dict)
            else {}
        )

        if not isinstance(
            preferences,
            dict
        ):
            raise TypeError(
                "preferences must be a dictionary."
            )

        if not isinstance(
            budget,
            dict
        ):
            raise TypeError(
                "budget must be a dictionary."
            )

        prompt = f"""
You are the trip cost-analysis component of Wanderlust.

The user has already selected this destination:

{selected_destination}

USER REQUEST:
{user_input}

TRIP REQUIREMENTS:
{json.dumps(
    preferences,
    ensure_ascii=False,
    default=str
)}

BUDGET:
{json.dumps(
    budget,
    ensure_ascii=False,
    default=str
)}

RESEARCH:
{json.dumps(
    research,
    ensure_ascii=False,
    default=str
)}

MAP DATA:
{json.dumps(
    map_data,
    ensure_ascii=False,
    default=str
)}

TRIP INFORMATION:
{json.dumps(
    trip_information,
    ensure_ascii=False,
    default=str
)}

Rules:

- Use only supplied information.
- Do not browse.
- Do not invent prices.
- Unknown prices must be null.
- Do not claim bookings.
- Do not claim availability.
- Do not invent schedules.
- Calculate totals from known numeric values only.

Return ONLY JSON:

{{
    "destination": "",
    "costs": [
        {{
            "category": "",
            "amount": null,
            "description": ""
        }}
    ],
    "total_estimated_cost": 0,
    "unknown_costs": [],
    "within_budget": true,
    "notes": []
}}
"""

        response = self.client.interactions.create(
            model=self.model,
            input=prompt,
        )

        content = getattr(
            response,
            "output_text",
            None
        )

        if not content:
            raise ValueError(
                "Gemini returned an empty selected-trip response."
            )

        result = self._parse_json_object(
            content,
            "selected trip"
        )

        costs = result.get(
            "costs",
            []
        )

        if not isinstance(
            costs,
            list
        ):
            costs = []

        cleaned_costs = []

        for cost in costs:

            if not isinstance(
                cost,
                dict
            ):
                continue

            amount = cost.get(
                "amount"
            )

            if amount is not None:

                try:
                    amount = round(
                        float(amount),
                        2
                    )

                except (
                    TypeError,
                    ValueError
                ):
                    amount = None

            cleaned_costs.append({
                "category": str(
                    cost.get(
                        "category",
                        "other"
                    )
                ).strip(),

                "amount": amount,

                "description": str(
                    cost.get(
                        "description",
                        ""
                    )
                ).strip(),
            })

        total = round(
            sum(
                cost["amount"]
                for cost in cleaned_costs
                if cost["amount"] is not None
            ),
            2
        )

        unknown = result.get(
            "unknown_costs",
            []
        )

        if not isinstance(
            unknown,
            list
        ):
            unknown = []

        notes = result.get(
            "notes",
            []
        )

        if not isinstance(
            notes,
            list
        ):
            notes = []

        return {
            "destination": str(
                result.get(
                    "destination",
                    selected_destination
                )
            ).strip(),

            "costs": cleaned_costs,

            "total_estimated_cost": total,

            "unknown_costs": [
                str(item).strip()
                for item in unknown
                if str(item).strip()
            ],

            "within_budget": result.get(
                "within_budget",
                True
            ),

            "notes": [
                str(item).strip()
                for item in notes
                if str(item).strip()
            ],
        }

    # ==========================================================
    # DESTINATION KEY
    # ==========================================================

    @staticmethod
    def _destination_key(
        destination,
        country
    ):
        return (
            f"{str(destination).strip().lower()}"
            f"|"
            f"{str(country).strip().lower()}"
        )

    # ==========================================================
    # GEMINI JSON PARSER
    # ==========================================================

    @staticmethod
    def _parse_json_object(
        content,
        description="response"
    ):

        if not isinstance(
            content,
            str
        ):
            raise ValueError(
                f"Invalid Gemini {description}."
            )

        content = content.strip()

        if content.startswith(
            "```"
        ):

            lines = content.splitlines()

            if lines:
                lines = lines[1:]

            if (
                lines
                and lines[-1].strip() == "```"
            ):
                lines = lines[:-1]

            content = "\n".join(
                lines
            ).strip()

        try:

            result = json.loads(
                content
            )

            if isinstance(
                result,
                dict
            ):
                return result

        except json.JSONDecodeError:
            pass

        start = content.find(
            "{"
        )

        end = content.rfind(
            "}"
        )

        if (
            start == -1
            or end == -1
            or end <= start
        ):
            raise ValueError(
                f"Gemini did not return JSON for {description}."
            )

        try:

            result = json.loads(
                content[start:end + 1]
            )

        except json.JSONDecodeError as error:

            raise ValueError(
                f"Invalid JSON for {description}: {error}"
            ) from error

        if not isinstance(
            result,
            dict
        ):
            raise ValueError(
                f"Gemini {description} must be a JSON object."
            )

        return result