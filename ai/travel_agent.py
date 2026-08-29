import json
import os

from dotenv import load_dotenv
from google import genai


class TravelAgent:
    """
    Main AI travel planning agent.

    TravelAgent is the main reasoning system of the
    travel planner and uses Gemini.

    It operates in two major stages:

        STAGE 1
            User
              ↓
            main.py
              ↓
          TravelAgent
              ↓
            Gemini
              ↓
        Candidate Destinations

        STAGE 2
            main.py
              ↓
        MapService + ResearchAgent
              ↓
        main.py
              ↓
          TravelAgent
              ↓
            Gemini
              ↓
        Final Travel Recommendation

    IMPORTANT:

    TravelAgent does NOT directly communicate with:

        - MoodAgent
        - Budget
        - ResearchAgent
        - MapService

    main.py is the communication/controller layer.
    """

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
        Ask Gemini to select a small list of candidate
        destinations.

        This is the FIRST Gemini planning pass.

        It does NOT perform final trip planning.

        It only determines which destinations should be
        passed to MapService and ResearchAgent.

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

        # ==========================================================
        # VALIDATION
        # ==========================================================

        if not isinstance(user_input, str):
            raise TypeError(
                "user_input must be a string."
            )

        if not isinstance(preferences, dict):
            raise TypeError(
                "preferences must be a dictionary."
            )

        if not isinstance(budget, dict):
            raise TypeError(
                "budget must be a dictionary."
            )

        if trip_information is None:
            trip_information = {}

        if not isinstance(trip_information, dict):
            raise TypeError(
                "trip_information must be a dictionary."
            )

        # ==========================================================
        # JSON DATA
        # ==========================================================

        preferences_json = json.dumps(
            preferences,
            indent=4
        )

        budget_json = json.dumps(
            budget,
            indent=4
        )

        trip_information_json = json.dumps(
            trip_information,
            indent=4
        )

        # ==========================================================
        # GEMINI PROMPT
        # ==========================================================

        prompt = f"""
    You are the destination-selection component of an
    AI travel planning system.

    Your ONLY job in this request is to select a SMALL list
    of suitable candidate destinations.

    You are NOT creating the final itinerary.

    You are NOT researching hotels.

    You are NOT researching flights.

    You are NOT calculating exact prices.

    You are NOT creating a complete travel plan.

    Your output will be passed to:

        main.py
            ↓
        MapService
            ↓
        ResearchAgent
            ↓
        TravelAgent

    ------------------------------------------------------------
    ORIGINAL USER REQUEST
    ------------------------------------------------------------

    {user_input}

    ------------------------------------------------------------
    BASIC TRIP INFORMATION
    ------------------------------------------------------------

    {trip_information_json}

    ------------------------------------------------------------
    TRAVEL PREFERENCE PROFILE
    ------------------------------------------------------------

    {preferences_json}

    ------------------------------------------------------------
    CURRENT BUDGET
    ------------------------------------------------------------

    {budget_json}

    ------------------------------------------------------------
    IMPORTANT RULES
    ------------------------------------------------------------

    The original user request is the ultimate source of truth.

    Respect the basic trip constraints.

    Pay attention to:

    - departure location
    - country
    - domestic/international scope
    - number of travelers
    - trip duration
    - travel dates
    - maximum travel time
    - maximum distance
    - transportation preference
    - accommodation preference
    - safety requirements
    - other requirements

    Also consider:

    - wanted moods
    - avoided moods
    - mood scores
    - budget

    Do not recommend destinations that obviously violate
    the user's hard constraints.

    Select approximately 3 to 5 candidate destinations.

    The candidates should be meaningfully different when
    appropriate.

    Do not return more than 5 candidates.

    ------------------------------------------------------------
    OUTPUT REQUIREMENT
    ------------------------------------------------------------

    YOU MUST RETURN ONLY VALID JSON.

    DO NOT use Markdown.

    DO NOT use ```json.

    DO NOT write an explanation before the JSON.

    DO NOT write an explanation after the JSON.

    The response MUST begin with:

    {{

    and MUST end with:

    }}

    Use EXACTLY this structure:

    {{
        "candidates": [
            {{
                "name": "Destination name",
                "country": "Country name",
                "reason": "Short explanation of why this destination is a candidate."
            }}
        ]
    }}

    Every candidate MUST contain:

        name
        country
        reason

    The "candidates" array must contain between 3 and 5
    destinations.

    Do not include any additional top-level fields.

    Do not include markdown.

    Return ONLY the JSON object.
    """

        # ==========================================================
        # GEMINI REQUEST
        # ==========================================================

        response = self.client.interactions.create(
            model=self.model,
            input=prompt
        )

        # ==========================================================
        # EXTRACT TEXT
        # ==========================================================

        content = getattr(
            response,
            "output_text",
            None
        )

        if not content:

            raise ValueError(
                "Gemini returned an empty candidate response."
            )

        content = content.strip()

        # ==========================================================
        # CLEAN COMMON MARKDOWN WRAPPERS
        # ==========================================================

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

        # ==========================================================
        # FIND JSON OBJECT
        # ==========================================================

        start = content.find(
            "{"
        )

        end = content.rfind(
            "}"
        )

        if start == -1 or end == -1:

            raise ValueError(
                "Gemini did not return a JSON object "
                "while generating candidate destinations."
            )

        json_text = content[
            start:end + 1
        ]

        # ==========================================================
        # PARSE JSON
        # ==========================================================

        try:

            result = json.loads(
                json_text
            )

        except json.JSONDecodeError as error:

            raise ValueError(
                "Gemini returned invalid JSON while "
                "generating candidate destinations."
            ) from error

        # ==========================================================
        # VALIDATE TOP LEVEL
        # ==========================================================

        if not isinstance(
            result,
            dict
        ):

            raise ValueError(
                "Gemini candidate response must be a JSON object."
            )

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

        # ==========================================================
        # VALIDATE CANDIDATES
        # ==========================================================

        cleaned_candidates = []

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

            if not name.strip():

                continue

            cleaned_candidates.append(
                {
                    "name": name.strip(),

                    "country": country.strip(),

                    "reason": (
                        str(reason).strip()
                    )
                }
            )

        # ==========================================================
        # REMOVE DUPLICATES
        # ==========================================================

        unique_candidates = []

        seen = set()

        for candidate in cleaned_candidates:

            key = (
                candidate["name"].lower(),
                candidate["country"].lower()
            )

            if key in seen:

                continue

            seen.add(
                key
            )

            unique_candidates.append(
                candidate
            )

        # ==========================================================
        # FINAL VALIDATION
        # ==========================================================

        if not unique_candidates:

            raise ValueError(
                "Gemini did not return any valid "
                "candidate destinations."
            )

        # ----------------------------------------------------------
        # Keep the candidate list small.
        # ----------------------------------------------------------

        unique_candidates = (
            unique_candidates[:5]
        )

        return {
            "candidates": unique_candidates
        }


        # ======================================================
        # CANDIDATE DESTINATION PROMPT
        # ======================================================

        prompt = f"""
You are the main AI travel planning agent.

Your job in this stage is to identify a SMALL number
of suitable candidate travel destinations.

You are NOT making the final travel decision yet.

The candidate destinations will later be investigated
by separate mapping and research systems.

You have received:

1. The ORIGINAL USER REQUEST.
2. A structured TRAVEL PREFERENCE PROFILE created
   by the MoodAgent.
3. The CURRENT TRAVEL BUDGET maintained by the
   application's Budget system.

------------------------------------------------------------
STRUCTURED TRAVEL PREFERENCE PROFILE
------------------------------------------------------------

The profile may contain:

- wanted:
  Canonical preferences the user wants.

- avoid:
  Canonical preferences the user wants to avoid.

- scores:
  Numerical importance of preferences.

- score_details:
  Additional scoring information.

- summary:
  Natural-language summary.

- raw_wanted:
  Original preference phrases.

- raw_avoid:
  Original rejected preference phrases.

------------------------------------------------------------
IMPORTANT INTERPRETATION RULE
------------------------------------------------------------

The ORIGINAL USER REQUEST is the ultimate source
of truth.

The structured preference profile is supporting
information.

If there is a disagreement between them:

    carefully interpret the original user request.

Do not blindly follow the structured profile.

Positive mood scores represent desired characteristics.

Negative mood scores represent characteristics
the user wants to avoid.

A negative preference is NOT something the user wants.

Example:

    crowded: -1.0

means:

    The user wants to avoid crowded environments.

------------------------------------------------------------
BUDGET
------------------------------------------------------------

The current budget is:

{budget_json}

Use the budget as a planning constraint.

Prefer destinations that could reasonably fit within
the available budget.

Do NOT invent exact current prices.

Do NOT claim that flights or hotels are currently
available.

Do NOT assume anything has already been purchased.

------------------------------------------------------------
ORIGINAL USER REQUEST
------------------------------------------------------------

{user_input}

------------------------------------------------------------
TRAVEL PREFERENCE PROFILE
------------------------------------------------------------

{preferences_json}

------------------------------------------------------------
CANDIDATE SELECTION
------------------------------------------------------------

Identify between 3 and 5 strong candidate destinations.

Candidates should be selected based on:

1. Original user request.
2. Wanted preferences.
3. Avoided preferences.
4. Mood scores.
5. Budget.
6. Trip type.
7. Travel experience requested by the user.

Try to provide candidates that are meaningfully
different when appropriate.

For example, do not return five nearly identical
destinations unless the user's request strongly
requires that.

------------------------------------------------------------
IMPORTANT
------------------------------------------------------------

At this stage:

DO NOT:

- create a full itinerary
- create a day-by-day plan
- make a final winner
- perform live web searches
- claim current flight prices
- claim current hotel prices
- claim real-time availability
- invent precise transportation costs

The destinations will be researched separately.

Return ONLY valid JSON.

Use exactly this structure:

{{
    "candidates": [
        {{
            "name": "Destination name",
            "country": "Country",
            "reason": "Why this destination should be researched."
        }}
    ]
}}
"""

        # ------------------------------------------------------
        # Gemini request.
        # ------------------------------------------------------

        response = self.client.interactions.create(
            model=self.model,
            input=prompt
        )

        content = response.output_text

        # ------------------------------------------------------
        # Parse JSON.
        # ------------------------------------------------------

        try:

            result = json.loads(
                content
            )

        except json.JSONDecodeError as error:

            raise ValueError(
                "Gemini returned invalid JSON while "
                "generating candidate destinations."
            ) from error

        # ------------------------------------------------------
        # Validate response.
        # ------------------------------------------------------

        if not isinstance(
            result,
            dict
        ):

            raise ValueError(
                "Gemini candidate response must "
                "be a dictionary."
            )

        candidates = result.get(
            "candidates"
        )

        if not isinstance(
            candidates,
            list
        ):

            raise ValueError(
                "'candidates' must be a list."
            )

        if not candidates:

            raise ValueError(
                "Gemini returned an empty candidate list."
            )

        # ------------------------------------------------------
        # Validate individual candidates.
        # ------------------------------------------------------

        cleaned_candidates = []

        for index, candidate in enumerate(
            candidates,
            start=1
        ):

            if not isinstance(
                candidate,
                dict
            ):

                raise ValueError(
                    f"Candidate {index} must be a dictionary."
                )

            name = candidate.get(
                "name"
            )

            country = candidate.get(
                "country"
            )

            reason = candidate.get(
                "reason"
            )

            if not name:

                raise ValueError(
                    f"Candidate {index} is missing 'name'."
                )

            if not country:

                raise ValueError(
                    f"Candidate {index} is missing 'country'."
                )

            if not reason:

                raise ValueError(
                    f"Candidate {index} is missing 'reason'."
                )

            cleaned_candidates.append(
                {
                    "name": str(name).strip(),
                    "country": str(country).strip(),
                    "reason": str(reason).strip()
                }
            )

        # ------------------------------------------------------
        # Keep only a small candidate list.
        # ------------------------------------------------------

        cleaned_candidates = (
            cleaned_candidates[:5]
        )

        return {
            "candidates": cleaned_candidates
        }

    # ==========================================================
    # FINAL TRAVEL PLANNING
    # ==========================================================

    def ask(
        self,
        user_input,
        preferences,
        budget,
        research=None,
        map_data=None
    ):
        """
        Final Gemini travel-planning stage.

        main.py provides:

            1. Original user request
            2. MoodAgent preferences
            3. Current budget
            4. ResearchAgent information
            5. MapService information

        TravelAgent uses all available information to
        reason about the best travel options.

        TravelAgent does NOT directly communicate with
        any other system.
        """

        # ------------------------------------------------------
        # Validate user input.
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

        # ------------------------------------------------------
        # Validate preferences.
        # ------------------------------------------------------

        if not isinstance(
            preferences,
            dict
        ):

            raise TypeError(
                "preferences must be a dictionary."
            )

        # ------------------------------------------------------
        # Validate budget.
        # ------------------------------------------------------

        if not isinstance(
            budget,
            dict
        ):

            raise TypeError(
                "budget must be a dictionary."
            )

        # ------------------------------------------------------
        # Validate research.
        # ------------------------------------------------------

        if research is None:

            research = {}

        if not isinstance(
            research,
            dict
        ):

            raise TypeError(
                "research must be a dictionary."
            )

        # ------------------------------------------------------
        # Validate map data.
        # ------------------------------------------------------

        if map_data is None:

            map_data = []

        if not isinstance(
            map_data,
            list
        ):

            raise TypeError(
                "map_data must be a list."
            )

        # ------------------------------------------------------
        # Convert information to JSON.
        # ------------------------------------------------------

        preferences_json = json.dumps(
            preferences,
            indent=4
        )

        budget_json = json.dumps(
            budget,
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

        # ======================================================
        # FINAL GEMINI PROMPT
        # ======================================================

        prompt = f"""
You are the main AI travel planning agent.

You are now performing the FINAL reasoning stage
of the travel planning process.

The application has already:

1. Received the user's original request.
2. Interpreted the user's preferences using MoodAgent.
3. Checked the user's budget.
4. Generated candidate destinations.
5. Obtained geographic information from MapService.
6. Obtained destination research from ResearchAgent.

Your job is now to combine this information and
produce the most useful travel recommendation.

------------------------------------------------------------
INFORMATION YOU HAVE RECEIVED
------------------------------------------------------------

1. ORIGINAL USER REQUEST

2. STRUCTURED TRAVEL PREFERENCE PROFILE

3. CURRENT TRAVEL BUDGET

4. MAP / LOCATION INFORMATION

5. DESTINATION RESEARCH

------------------------------------------------------------
ORIGINAL USER REQUEST
------------------------------------------------------------

{user_input}

------------------------------------------------------------
STRUCTURED TRAVEL PREFERENCES
------------------------------------------------------------

{preferences_json}

------------------------------------------------------------
CURRENT TRAVEL BUDGET
------------------------------------------------------------

{budget_json}

------------------------------------------------------------
MAP / LOCATION INFORMATION
------------------------------------------------------------

{map_json}

------------------------------------------------------------
DESTINATION RESEARCH
------------------------------------------------------------

{research_json}

------------------------------------------------------------
PREFERENCE INTERPRETATION
------------------------------------------------------------

The original user request is the ultimate source
of truth.

The structured preference profile is supporting
information.

Positive mood scores represent desired
characteristics.

Negative mood scores represent characteristics
the user wants to avoid.

For example:

    nature: 1.0

means nature is strongly desired.

And:

    crowded: -1.0

means crowded environments should be avoided.

Do not interpret a negative score as a desired
characteristic.

------------------------------------------------------------
BUDGET RULES
------------------------------------------------------------

The budget is a HARD planning constraint.

The Budget class is responsible for maintaining
the actual budget.

You must NOT modify the budget.

You must NOT claim that money has been spent.

You must NOT assume a booking has been completed.

Use the remaining budget when evaluating destinations.

If exact costs are not available:

    clearly identify the cost as unknown.

Do not invent exact prices.

------------------------------------------------------------
MAP INFORMATION
------------------------------------------------------------

MapService provides geographic information.

Use it to:

- confirm destination identity
- confirm country
- identify latitude
- identify longitude
- distinguish similarly named places
- understand geographic relationships

Coordinates may later be used by the application's
3D map system.

Do not treat coordinates as a quality score.

Do not invent coordinates.

Do not claim MapService provides flight or hotel
prices unless such information is explicitly included
in the provided data.

------------------------------------------------------------
RESEARCH INFORMATION
------------------------------------------------------------

ResearchAgent provides supporting destination
information.

Use the research to understand:

- nature
- mountains
- beaches
- nightlife
- urban environment
- crowds
- relaxation
- activities
- accessibility
- fatigue
- budget considerations
- limitations

ResearchAgent does NOT make the final decision.

You must perform the final reasoning.

Do not invent facts that are missing from the research.

If information is unknown, say so.

------------------------------------------------------------
FINAL REASONING
------------------------------------------------------------

Evaluate the destinations using:

1. User preferences.
2. Avoided preferences.
3. Preference strength.
4. Budget.
5. Geographic information.
6. Destination characteristics.
7. Travel fatigue.
8. Accessibility.
9. Overall suitability.

A destination that technically matches one preference
but strongly violates another important preference
should not automatically be selected.

Consider trade-offs.

For example:

A destination may have excellent nightlife
but be extremely crowded.

If the user strongly dislikes crowds, this should
reduce its suitability.

Likewise, a destination may have beautiful nature
but require extensive transportation and hiking.

If the user wants a relaxing and non-tiring trip,
this should be considered a disadvantage.

------------------------------------------------------------
FINAL RESPONSE
------------------------------------------------------------

Provide a clear final travel recommendation.

For each strong option, explain:

- Destination
- Country
- Why it matches
- Desired characteristics satisfied
- Avoided characteristics
- Budget suitability
- Travel effort / fatigue
- Important geographic information
- Major advantages
- Major limitations

If one destination clearly fits better than the others,
identify it as the strongest option.

If there is no clear winner, explain the trade-offs.

Do not claim that a trip has been booked.

Do not claim that the user has spent money.

Do not invent live prices.

Do not invent hotel availability.

Do not invent flight availability.

Do not invent real-time transportation information.

Clearly distinguish known information from unknown
information.

The final response should be useful to a user who is
deciding which trip to pursue.
"""

        # ------------------------------------------------------
        # Gemini request.
        # ------------------------------------------------------

        response = self.client.interactions.create(
            model=self.model,
            input=prompt
        )

        return response.output_text