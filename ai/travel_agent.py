import json
import os

from dotenv import load_dotenv
from google import genai


class TravelAgent:
    """
    Main AI travel planning agent.

    TravelAgent is responsible for reasoning and planning.

    It does NOT directly communicate with:

        - MoodAgent
        - ResearchAgent
        - MapService
        - Budget

    main.py is the communication/controller layer.

    ==========================================================
    WORKFLOW
    ==========================================================

        main.py
           |
           v
        find_candidates()
           |
           v
        Candidate Destinations
           |
           +----------------------+
           |                      |
           v                      v
       ResearchAgent          MapService
           |                      |
           +----------+-----------+
                      |
                      v
                   main.py
                      |
                      v
                    ask()
                      |
                      v
              Final Trip Options
                      |
                      v
                User Selection
                      |
                      v
            build_selected_trip()
                      |
                      v
              Detailed Trip Plan
                      |
                      v
                   main.py
                      |
                      v
                   Budget
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
                "GEMINI_API_KEY is not set "
                "in the .env file."
            )

        self.client = genai.Client(
            api_key=api_key
        )

        self.model = "gemini-3.6-flash"

    # ==========================================================
    # FIND CANDIDATE DESTINATIONS
    # ==========================================================

    def find_candidates(
        self,
        user_input,
        preferences,
        budget,
        trip_information=None
    ):
        """
        FIRST GEMINI STAGE.

        Select a small number of destinations that
        should be researched.

        This method does NOT:

            - select the final destination
            - search hotels
            - search flights
            - calculate final trip costs
            - create an itinerary

        Returns:

            {
                "candidates": [
                    {
                        "name": "...",
                        "country": "...",
                        "reason": "..."
                    }
                ]
            }
        """

        # ------------------------------------------------------
        # Validation
        # ------------------------------------------------------

        if not isinstance(
            user_input,
            str
        ):
            raise TypeError(
                "user_input must be a string."
            )

        if not user_input.strip():

            raise ValueError(
                "user_input cannot be empty."
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

        # ------------------------------------------------------
        # JSON
        # ------------------------------------------------------

        preferences_json = json.dumps(
            {
                "wanted": preferences.get("wanted", []),
                "avoid": preferences.get("avoid", []),
                "constraints": preferences.get("constraints", {})
            },
            separators=(",", ":")
        )

        budget_json = json.dumps(
            budget,
            separators=(",", ":")
        )

        trip_information_json = json.dumps(
            trip_information,
            separators=(",", ":")
        )

        # ------------------------------------------------------
        # Prompt
        # ------------------------------------------------------

        prompt = f"""
You are the candidate-selection stage of an AI travel planner.

USER REQUEST:
{user_input}

TRIP INFORMATION:
{trip_information_json}

PREFERENCES:
{preferences_json}

BUDGET:
{budget_json}

Select exactly 3 strong destinations for later research.
Respect hard constraints first, then wanted/avoided preferences.
Do not create an itinerary or claim live availability.
Return ONLY valid JSON:

{{
  "candidates": [
    {{
      "name": "Destination",
      "country": "Country",
      "reason": "Concise reason this should be researched."
    }}
  ]
}}
"""
        # ------------------------------------------------------
        # Gemini
        # ------------------------------------------------------

        response = self.client.interactions.create(
            model=self.model,
            input=prompt
        )

        content = getattr(
            response,
            "output_text",
            None
        )

        if not content:

            raise ValueError(
                "Gemini returned an empty candidate response."
            )

        result = self._parse_json_object(
            content,
            "candidate destinations"
        )

        # ------------------------------------------------------
        # Validate candidates
        # ------------------------------------------------------

        candidates = result.get(
            "candidates"
        )

        if not isinstance(
            candidates,
            list
        ):
            raise ValueError(
                "Gemini candidate response is missing "
                "a valid 'candidates' list."
            )

        cleaned = []

        seen = set()

        for candidate in candidates:

            if not isinstance(
                candidate,
                dict
            ):
                continue

            name = candidate.get(
                "name"
            )

            country = candidate.get(
                "country"
            )

            reason = candidate.get(
                "reason",
                ""
            )

            if not isinstance(
                name,
                str
            ):
                continue

            if not isinstance(
                country,
                str
            ):
                continue

            name = name.strip()
            country = country.strip()

            if not name:
                continue

            key = (
                name.lower(),
                country.lower()
            )

            if key in seen:
                continue

            seen.add(
                key
            )

            cleaned.append(
                {
                    "name": name,

                    "country": country,

                    "reason": str(
                        reason
                    ).strip()
                }
            )

        if not cleaned:

            raise ValueError(
                "Gemini did not return any valid "
                "candidate destinations."
            )

        return {
            "candidates": cleaned[:3]
        }

    # ==========================================================
    # FINAL DESTINATION COMPARISON
    # ==========================================================

    def ask(
        self,
        user_input,
        preferences,
        budget,
        research=None,
        map_data=None,
        trip_information=None
    ):
        """
        SECOND GEMINI STAGE.

        Combine:

            - original user request
            - trip information
            - MoodAgent
            - budget
            - ResearchAgent
            - MapService

        and produce the final set of travel options.

        This is the information the user will review
        before selecting a trip.

        This method does NOT commit budget expenses.
        """

        # ------------------------------------------------------
        # Defaults
        # ------------------------------------------------------

        if research is None:
            research = {}

        if map_data is None:
            map_data = []

        if trip_information is None:
            trip_information = {}

        # ------------------------------------------------------
        # Validation
        # ------------------------------------------------------

        if not isinstance(
            user_input,
            str
        ):
            raise TypeError(
                "user_input must be a string."
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

        if not isinstance(
            research,
            dict
        ):
            raise TypeError(
                "research must be a dictionary."
            )

        if not isinstance(
            map_data,
            list
        ):
            raise TypeError(
                "map_data must be a list."
            )

        if not isinstance(
            trip_information,
            dict
        ):
            raise TypeError(
                "trip_information must be a dictionary."
            )

        # ------------------------------------------------------
        # Convert to JSON
        # ------------------------------------------------------

        user_json = json.dumps(
            user_input,
            separators=(",", ":")
        )

        preferences_json = json.dumps(
            preferences,
            separators=(",", ":")
        )

        budget_json = json.dumps(
            budget,
            separators=(",", ":")
        )

        research_json = json.dumps(
            research,
            separators=(",", ":")
        )

        map_json = json.dumps(
            map_data,
            separators=(",", ":")
        )

        trip_information_json = json.dumps(
            trip_information,
            separators=(",", ":")
        )

        # ------------------------------------------------------
        # Prompt
        # ------------------------------------------------------

        prompt = f"""
You are the MAIN AI travel planner performing final quality control.

USER REQUEST:
{user_json}

TRIP INFORMATION:
{trip_information_json}

PREFERENCES:
{preferences_json}

BUDGET:
{budget_json}

MAP DATA:
{map_json}

RESEARCH FROM SMALLER MODEL:
{research_json}

Critically review the research; it is supporting evidence, not ground truth.
Use the user's request and hard constraints as the source of truth.
Compare candidates on preference fit, nature/urban character, relaxation,
crowds, activities, accessibility, travel effort, transportation, geography,
budget suitability, advantages and limitations.

Do not invent current prices, bookings, or availability.
Do not create an itinerary or modify the budget.
The user must still choose a destination.

Give concise recommendations and explain the strongest fits.
"""
        response = self.client.interactions.create(
            model=self.model,
            input=prompt,
            generation_config={
                "temperature": 0.2,
                "max_output_tokens": 1400
            }
        )

        content = getattr(
            response,
            "output_text",
            None
        )

        if not content:

            raise ValueError(
                "Gemini returned an empty final response."
            )

        return content.strip()

    # ==========================================================
    # BUILD SELECTED TRIP
    # ==========================================================

    def build_selected_trip(
        self,
        selected_destination,
        user_input,
        preferences,
        budget,
        research=None,
        map_data=None,
        trip_information=None
    ):
        """
        THIRD GEMINI STAGE.

        Build the detailed structure for ONE destination
        selected by the user.

        This happens AFTER the user chooses a destination.

        The output is intended to be passed back to main.py,
        which can then place the returned costs into the
        Budget's temporary estimate system.

        IMPORTANT:

        This method does NOT directly modify Budget.

        It does NOT book anything.

        It does NOT claim that estimated prices are
        guaranteed.

        Cost values should only be included when supported
        by supplied MapService / research information.

        Unknown costs must be represented as null rather
        than invented.

        Expected output:

            {
                "destination": "...",

                "costs": [
                    {
                        "category": "transportation",
                        "amount": 0,
                        "description": "..."
                    }
                ],

                "total_estimated_cost": 0,

                "within_budget": true,

                "notes": []
            }
        """

        # ------------------------------------------------------
        # Defaults
        # ------------------------------------------------------

        if research is None:
            research = {}

        if map_data is None:
            map_data = []

        if trip_information is None:
            trip_information = {}

        # ------------------------------------------------------
        # Validation
        # ------------------------------------------------------

        if not isinstance(
            selected_destination,
            str
        ):
            raise TypeError(
                "selected_destination must be a string."
            )

        if not selected_destination.strip():

            raise ValueError(
                "selected_destination cannot be empty."
            )

        if not isinstance(
            user_input,
            str
        ):
            raise TypeError(
                "user_input must be a string."
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

        if not isinstance(
            research,
            dict
        ):
            raise TypeError(
                "research must be a dictionary."
            )

        if not isinstance(
            map_data,
            list
        ):
            raise TypeError(
                "map_data must be a list."
            )

        if not isinstance(
            trip_information,
            dict
        ):
            raise TypeError(
                "trip_information must be a dictionary."
            )

        # ------------------------------------------------------
        # JSON
        # ------------------------------------------------------

        budget_json = json.dumps(
            budget,
            indent=4
        )

        preferences_json = json.dumps(
            preferences,
            indent=4
        )

        research_json = json.dumps(
            research,
            indent=4
        )

        map_json = json.dumps(
            map_data,
            indent=4
        )

        trip_information_json = json.dumps(
            trip_information,
            indent=4
        )

        # ======================================================
        # SELECTED TRIP PROMPT
        # ======================================================

        prompt = f"""
You are the final trip-construction component of an
AI travel planning system.

The user has selected ONE destination.

Your task is to construct a detailed estimated trip
cost structure for that destination using ONLY the
information supplied to you.

------------------------------------------------------------
SELECTED DESTINATION
------------------------------------------------------------

{selected_destination}

------------------------------------------------------------
ORIGINAL USER REQUEST
------------------------------------------------------------

{user_input}

------------------------------------------------------------
BASIC TRIP INFORMATION
------------------------------------------------------------

{trip_information_json}

------------------------------------------------------------
TRAVEL PREFERENCES
------------------------------------------------------------

{preferences_json}

------------------------------------------------------------
CURRENT BUDGET
------------------------------------------------------------

{budget_json}

------------------------------------------------------------
MAP / LOCATION DATA
------------------------------------------------------------

{map_json}

------------------------------------------------------------
RESEARCH DATA
------------------------------------------------------------

{research_json}

------------------------------------------------------------
IMPORTANT COST RULES
------------------------------------------------------------

The application needs an estimated financial
breakdown before the user commits to the trip.

Possible categories include:

- transportation
- accommodation
- food
- activities
- local transportation
- other

IMPORTANT:

Do NOT invent precise current prices.

Only use monetary values that are explicitly supplied
in the provided information.

If a cost is unknown, use:

    null

rather than guessing.

Do not claim a booking has occurred.

Do not claim that a price is guaranteed.

Do not claim real-time availability unless it is
explicitly provided in the input data.

If the available information is insufficient to
calculate the complete trip cost, clearly identify
which costs are unknown.

------------------------------------------------------------
BUDGET
------------------------------------------------------------

The current remaining budget is provided above.

Compare the estimated known total against the
remaining budget.

The Budget class will perform the actual affordability
check.

Do not modify the budget yourself.

------------------------------------------------------------
OUTPUT
------------------------------------------------------------

Return ONLY valid JSON.

Use exactly:

{{
    "destination": "Selected destination",

    "costs": [
        {{
            "category": "transportation",
            "amount": 0,
            "description": "Description"
        }}
    ],

    "total_estimated_cost": 0,

    "unknown_costs": [],

    "within_budget": true,

    "notes": []
}}

Rules:

- "costs" must be an array.
- "amount" must be a number or null.
- Unknown costs must NOT be guessed.
- "total_estimated_cost" should only include known
  monetary amounts.
- "unknown_costs" should identify missing categories.
- "within_budget" should be based only on known costs.
- Do not include Markdown.
- Do not include explanatory text outside JSON.
"""

        response = self.client.interactions.create(
            model=self.model,
            input=prompt
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

        # ------------------------------------------------------
        # Basic validation
        # ------------------------------------------------------

        if not isinstance(
            result,
            dict
        ):
            raise ValueError(
                "Selected trip response must be a JSON object."
            )

        destination = result.get(
            "destination"
        )

        costs = result.get(
            "costs"
        )

        if not isinstance(
            destination,
            str
        ):
            raise ValueError(
                "Selected trip response is missing "
                "a valid destination."
            )

        if not isinstance(
            costs,
            list
        ):
            raise ValueError(
                "Selected trip response is missing "
                "a valid costs list."
            )

        cleaned_costs = []

        for cost in costs:

            if not isinstance(
                cost,
                dict
            ):
                continue

            category = str(
                cost.get(
                    "category",
                    "other"
                )
            ).strip()

            description = str(
                cost.get(
                    "description",
                    ""
                )
            ).strip()

            amount = cost.get(
                "amount"
            )

            # --------------------------------------------------
            # Unknown costs are allowed.
            # --------------------------------------------------

            if amount is None:

                cleaned_costs.append(
                    {
                        "category": category,

                        "amount": None,

                        "description": description
                    }
                )

                continue

            # --------------------------------------------------
            # Validate known amount.
            # --------------------------------------------------

            try:

                amount = round(
                    float(amount),
                    2
                )

            except (
                TypeError,
                ValueError
            ):

                continue

            if amount < 0:
                continue

            cleaned_costs.append(
                {
                    "category": category,

                    "amount": amount,

                    "description": description
                }
            )

        # ------------------------------------------------------
        # Recalculate known total ourselves.
        #
        # This prevents Gemini from accidentally returning
        # a total that does not match its own cost list.
        # ------------------------------------------------------

        known_total = 0.0

        for cost in cleaned_costs:

            if cost["amount"] is not None:

                known_total += cost["amount"]

        known_total = round(
            known_total,
            2
        )

        # ------------------------------------------------------
        # Unknown costs
        # ------------------------------------------------------

        unknown_costs = result.get(
            "unknown_costs",
            []
        )

        if not isinstance(
            unknown_costs,
            list
        ):
            unknown_costs = []

        unknown_costs = [
            str(item).strip()
            for item in unknown_costs
            if str(item).strip()
        ]

        # ------------------------------------------------------
        # Notes
        # ------------------------------------------------------

        notes = result.get(
            "notes",
            []
        )

        if not isinstance(
            notes,
            list
        ):
            notes = []

        notes = [
            str(item).strip()
            for item in notes
            if str(item).strip()
        ]

        # ------------------------------------------------------
        # Determine affordability using the supplied budget.
        #
        # Gemini does not get to override the actual
        # affordability calculation.
        # ------------------------------------------------------

        try:

            remaining_budget = float(
                budget.get(
                    "remaining",
                    0
                )
            )

        except (
            TypeError,
            ValueError
        ):

            remaining_budget = 0.0

        within_budget = (
            known_total <= remaining_budget
        )

        # ------------------------------------------------------
        # Final structured result
        # ------------------------------------------------------

        return {
            "destination": destination.strip(),

            "costs": cleaned_costs,

            "total_estimated_cost": known_total,

            "unknown_costs": unknown_costs,

            "within_budget": within_budget,

            "notes": notes
        }

    # ==========================================================
    # JSON PARSER
    # ==========================================================

    @staticmethod
    def _parse_json_object(
        content,
        description="response"
    ):
        """
        Safely parse a Gemini JSON response.

        Handles common Markdown wrappers such as:

            ```json
            {...}
            ```

        and also extracts the outer JSON object
        if Gemini adds accidental surrounding text.
        """

        if not isinstance(
            content,
            str
        ):
            raise ValueError(
                f"Gemini returned an invalid {description}."
            )

        content = content.strip()

        # ------------------------------------------------------
        # Remove Markdown fences.
        # ------------------------------------------------------

        if content.startswith(
            "```json"
        ):

            content = content[
                len("```json"):
            ].strip()

        elif content.startswith(
            "```"
        ):

            content = content[
                len("```"):
            ].strip()

        if content.endswith(
            "```"
        ):

            content = content[
                :-3
            ].strip()

        # ------------------------------------------------------
        # Locate JSON object.
        # ------------------------------------------------------

        start = content.find(
            "{"
        )

        end = content.rfind(
            "}"
        )

        if start == -1 or end == -1:

            raise ValueError(
                f"Gemini did not return a JSON object "
                f"while generating {description}."
            )

        json_text = content[
            start:end + 1
        ]

        try:

            result = json.loads(
                json_text
            )

        except json.JSONDecodeError as error:

            raise ValueError(
                f"Gemini returned invalid JSON while "
                f"generating {description}."
            ) from error

        if not isinstance(
            result,
            dict
        ):

            raise ValueError(
                f"Gemini {description} must be a JSON object."
            )

        return result