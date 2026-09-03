import json
import os

from dotenv import load_dotenv
from groq import Groq

from mood.mood_keywords import MoodKeywords
from mood.mood_score import MoodScore


class MoodAgent:
    """
    STEP 2 — TRAVEL REQUIREMENTS EXTRACTION

    Receives:

        User natural-language request
        +
        Basic trip information

    Produces:

        TripRequirements JSON

    MoodAgent does NOT:

        - generate destinations
        - search the web
        - research destinations
        - evaluate destinations
        - rank destinations
        - build final trips
        - search maps
        - calculate trip costs

    Architecture:

        USER
          |
          v
        MoodAgent
          |
          v
        TripRequirements
    """

    def __init__(self):

        load_dotenv()

        api_key = os.getenv(
            "GROQ_API_KEY"
        )

        if not api_key:

            raise ValueError(
                "GROQ_API_KEY is not set in the .env file."
            )

        self.client = Groq(
            api_key=api_key
        )

        self.model = "openai/gpt-oss-20b"

        self.keyword_helper = MoodKeywords()
        self.score_helper = MoodScore()

    # ==========================================================
    # INTERPRET USER REQUEST
    # ==========================================================

    def interpret(
        self,
        user_input,
        trip_information=None
    ):
        """
        Convert the user's natural-language request into
        structured TripRequirements.

        This is the ONLY responsibility of MoodAgent.
        """

        # ------------------------------------------------------
        # VALIDATE USER INPUT
        # ------------------------------------------------------

        if not isinstance(
            user_input,
            str
        ):

            raise TypeError(
                "user_input must be a string."
            )

        user_input = user_input.strip()

        if not user_input:

            raise ValueError(
                "user_input cannot be empty."
            )

        # ------------------------------------------------------
        # DEFAULT TRIP INFORMATION
        # ------------------------------------------------------

        if trip_information is None:

            trip_information = {}

        if not isinstance(
            trip_information,
            dict
        ):

            raise TypeError(
                "trip_information must be a dictionary."
            )

        trip_information_json = json.dumps(
            trip_information,
            separators=(",", ":"),
            default=str
        )

        # ======================================================
        # EXTRACTION PROMPT
        # ======================================================

        prompt = f"""
You are the Travel Requirements Extraction Agent.

Your ONLY job is to understand what the user wants from
their trip and convert it into a structured TripRequirements
JSON object.

You MUST NOT recommend destinations.

You MUST NOT search for destinations.

You MUST NOT rank destinations.

You MUST NOT invent missing information.

The user's wording is the source of truth.

============================================================
BASIC TRIP INFORMATION
============================================================

{trip_information_json}

============================================================
USER REQUEST
============================================================

{user_input}

============================================================
EXTRACTION RULES
============================================================

1. Extract explicit requirements.

2. Extract clear preferences.

3. Put desired experiences in "wanted".

4. Put explicitly rejected experiences in "avoid".

5. Preserve hard constraints.

6. Do not turn weak or uncertain language into a hard
   constraint.

7. Do not invent budget, dates, countries, activities,
   weather preferences, transportation preferences, or
   accommodation preferences.

8. Basic trip information supplied by the application is
   authoritative.

9. If a value is unknown, use null.

10. "other" MUST always be an array.

11. Keep raw user wording in raw_wanted/raw_avoid when useful.

12. Return ONLY valid JSON.

============================================================
CANONICAL PREFERENCE TRAITS
============================================================

nature
mountains
beaches
wildlife
hiking
relaxation
quiet
culture
history
food
nightlife
urban
photography
adventure
warm_weather
cold_weather
snow
remote
family
solo
romance
shopping
luxury
crowded
budget_friendly

============================================================
REQUIRED JSON
============================================================

{{
    "wanted": [],
    "avoid": [],

    "constraints": {{
        "trip_scope": null,
        "country": null,
        "region": null,
        "travelers": null,
        "duration_days": null,
        "departure_location": null,
        "budget": null,
        "currency": null,
        "maximum_total_travel_time": null,
        "maximum_distance": null,
        "safety_requirement": null,
        "transportation_preference": null,
        "accommodation_preference": null,
        "travel_dates": null,
        "other": []
    }},

    "summary": "",

    "raw_wanted": [],

    "raw_avoid": []
}}
"""

        # ======================================================
        # GROQ REQUEST
        # ======================================================

        response = self.client.chat.completions.create(

            model=self.model,

            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a travel preference "
                        "extraction system. "
                        "Return exactly one valid JSON object "
                        "and nothing else."
                    )
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],

            reasoning_effort="low",

            reasoning_format="hidden",

            response_format={
                "type": "json_object"
            },

            max_completion_tokens=1200
        )
        # ======================================================
        # READ RESPONSE
        # ======================================================

        content = (
            response
            .choices[0]
            .message
            .content
        )

        if not content:

            raise ValueError(
                "Groq returned an empty response."
            )

        content = content.strip()

        # ======================================================
        # PARSE JSON
        # ======================================================

        try:

            result = json.loads(
                content
            )

        except json.JSONDecodeError as error:

            raise ValueError(
                "Groq returned invalid JSON."
            ) from error

        # ======================================================
        # VALIDATE TOP LEVEL
        # ======================================================

        if not isinstance(
            result,
            dict
        ):

            raise ValueError(
                "MoodAgent expected a JSON object."
            )

        # ======================================================
        # EXTRACT FIELDS
        # ======================================================

        wanted = result.get(
            "wanted",
            []
        )

        avoid = result.get(
            "avoid",
            []
        )

        constraints = result.get(
            "constraints",
            {}
        )

        summary = result.get(
            "summary",
            ""
        )

        raw_wanted = result.get(
            "raw_wanted",
            []
        )

        raw_avoid = result.get(
            "raw_avoid",
            []
        )

        # ======================================================
        # TYPE NORMALIZATION
        # ======================================================

        if not isinstance(
            wanted,
            list
        ):

            wanted = []

        if not isinstance(
            avoid,
            list
        ):

            avoid = []

        if not isinstance(
            constraints,
            dict
        ):

            constraints = {}

        if not isinstance(
            raw_wanted,
            list
        ):

            raw_wanted = []

        if not isinstance(
            raw_avoid,
            list
        ):

            raw_avoid = []

        # ======================================================
        # NORMALIZE PREFERENCES
        # ======================================================

        wanted = [
            str(value).strip().lower()
            for value in wanted
            if str(value).strip()
        ]

        avoid = [
            str(value).strip().lower()
            for value in avoid
            if str(value).strip()
        ]

        # Remove duplicates.

        wanted = list(
            dict.fromkeys(
                wanted
            )
        )

        avoid = list(
            dict.fromkeys(
                avoid
            )
        )

        # Explicitly avoided traits take priority.

        wanted = [
            value
            for value in wanted
            if value not in avoid
        ]

        # ======================================================
        # NORMALIZE CONSTRAINTS
        # ======================================================

        constraint_keys = [

            "trip_scope",
            "country",
            "region",
            "travelers",
            "duration_days",
            "departure_location",
            "budget",
            "currency",
            "maximum_total_travel_time",
            "maximum_distance",
            "safety_requirement",
            "transportation_preference",
            "accommodation_preference",
            "travel_dates",
            "other"
        ]

        normalized_constraints = {}

        for key in constraint_keys:

            if key in trip_information:

                normalized_constraints[key] = (
                    trip_information[key]
                )

            elif key in constraints:

                normalized_constraints[key] = (
                    constraints[key]
                )

            else:

                normalized_constraints[key] = (
                    []
                    if key == "other"
                    else None
                )

        # ------------------------------------------------------
        # Ensure other is always an array.
        # ------------------------------------------------------

        if not isinstance(
            normalized_constraints["other"],
            list
        ):

            normalized_constraints["other"] = [
                normalized_constraints["other"]
            ]

        # ======================================================
        # CALCULATE MOOD SCORES
        # ======================================================

        score_profile = (
            self.score_helper.analyze_profile(
                {
                    "wanted": wanted,
                    "avoid": avoid
                }
            )
        )

        scores = score_profile.get(
            "combined",
            {}
        )

        # ======================================================
        # FINAL TRIP REQUIREMENTS
        # ======================================================

        trip_requirements = {

            "wanted":
                wanted,

            "avoid":
                avoid,

            "scores":
                scores,

            "score_details":
                score_profile,

            "constraints":
                normalized_constraints,

            "summary":
                str(
                    summary
                ).strip(),

            "raw_wanted": [
                str(value).strip()
                for value in raw_wanted
                if str(value).strip()
            ],

            "raw_avoid": [
                str(value).strip()
                for value in raw_avoid
                if str(value).strip()
            ]
        }

        return trip_requirements