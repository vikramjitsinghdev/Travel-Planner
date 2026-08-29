import json
import os

from dotenv import load_dotenv
from groq import Groq

from mood.mood_keywords import MoodKeywords
from mood.mood_score import MoodScore


class MoodAgent:
    """
    Travel preference interpretation agent.

    This agent receives BOTH:

        1. Basic trip information
        2. Natural-language travel preferences

    It converts them into one structured user profile.

    Architecture:

        main.py
            |
            +---- basic trip information
            |
            +---- user wishes
            |
            v
        MoodAgent
            |
           Groq
            |
            v
        Structured User Profile
            |
            +---- moods
            +---- scores
            +---- constraints
            +---- raw information
            +---- summary

    MoodAgent does NOT:
        - recommend destinations
        - search the web
        - search maps
        - search hotels
        - calculate actual trip costs
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

        # ------------------------------------------------------
        # Helper classes.
        # ------------------------------------------------------

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
        Interpret the user's travel request together with
        the basic trip information.

        Parameters:

            user_input:
                Natural-language description of what the
                user wants from the trip.

            trip_information:
                Basic trip constraints collected by main.py.

        Returns:

            Structured user profile.
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

        user_input = user_input.strip()

        if not user_input:

            raise ValueError(
                "user_input cannot be empty."
            )

        # ------------------------------------------------------
        # Default trip information.
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

        # ------------------------------------------------------
        # Convert basic information to JSON.
        # ------------------------------------------------------

        trip_information_json = json.dumps(
            trip_information,
            indent=4
        )

        # ======================================================
        # GROQ PROMPT
        # ======================================================

        prompt = f"""
You are the travel preference interpretation component
of an AI travel planning system.

Your job is to understand EVERYTHING the user has provided.

You have two sources of information:

1. BASIC TRIP INFORMATION
2. NATURAL-LANGUAGE TRAVEL WISHES

You must combine them into one structured representation
of what the user wants.

You are NOT responsible for recommending destinations.

You are NOT responsible for searching for destinations.

You are NOT responsible for prices.

You are NOT responsible for hotels or flights.

------------------------------------------------------------
BASIC TRIP INFORMATION
------------------------------------------------------------

{trip_information_json}

------------------------------------------------------------
USER'S NATURAL-LANGUAGE TRAVEL WISHES
------------------------------------------------------------

{user_input}

------------------------------------------------------------
YOUR TASK
------------------------------------------------------------

Extract:

1. wanted

Canonical moods/preferences the user wants.

Examples:

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

2. avoid

Canonical moods/preferences the user explicitly wants
to avoid.

IMPORTANT:

If the user says:

"I don't want crowded cities"

then:

avoid:
[
    "urban",
    "crowded"
]

Do NOT put "urban" or "crowded" in wanted.

If the user says:

"I don't want too much walking"

do NOT interpret this as wanting "walking".

Instead record it as a constraint or limitation.

3. summary

Give a short natural-language summary of the complete
user request.

4. raw_wanted

Keep important phrases from the user's original request.

5. raw_avoid

Keep important phrases that describe things the user
does not want.

6. constraints

Preserve the basic trip information.

Do NOT invent missing information.

------------------------------------------------------------
IMPORTANT INTERPRETATION RULES
------------------------------------------------------------

The user's original words are the source of truth.

Do not invent preferences.

Do not convert every noun into a mood.

For example:

"I don't want a tiring trip"

does NOT mean:

wanted = ["rest"]

Instead, understand it as a travel constraint.

For example:

"I don't want to walk much"

does NOT mean:

wanted = ["walking"]

It means the user wants a trip requiring limited walking.

Similarly:

"I want nature but also an urban experience"

means BOTH:

wanted = ["nature", "urban"]

Do not assume these preferences contradict each other.

------------------------------------------------------------
CONSTRAINT RULES
------------------------------------------------------------

The following information should be preserved exactly
when available:

trip_scope
country
region
travelers
duration_days
departure_location
maximum_total_travel_time
maximum_distance
safety_requirement
transportation_preference
accommodation_preference
travel_dates
other

Do not guess values.

If something is not provided, use null.

"other" must always be an array.

------------------------------------------------------------
OUTPUT
------------------------------------------------------------

Return ONLY one JSON OBJECT.

Never return a JSON array.

Never return Markdown.

Never return ```json.

Never add explanations outside the JSON object.

The response MUST follow this exact structure:

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

Remember:

The entire response must be ONE JSON OBJECT.
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

            response_format={
                "type": "json_object"
            }
        )

        # ======================================================
        # EXTRACT RESPONSE
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
        # NORMALIZE FIELDS
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
        # NORMALIZE MOOD NAMES
        # ======================================================

        wanted = [
            str(mood).strip().lower()
            for mood in wanted
            if str(mood).strip()
        ]

        avoid = [
            str(mood).strip().lower()
            for mood in avoid
            if str(mood).strip()
        ]

        # ------------------------------------------------------
        # Remove duplicates.
        # ------------------------------------------------------

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

        # ------------------------------------------------------
        # Prevent the same mood from being both wanted
        # and avoided.
        #
        # If there is ambiguity, avoid takes priority because
        # it represents an explicit rejection.
        # ------------------------------------------------------

        wanted = [
            mood
            for mood in wanted
            if mood not in avoid
        ]

        # ======================================================
        # MERGE BASIC TRIP INFORMATION
        # ======================================================

        constraint_keys = [

            "trip_scope",
            "country",
            "region",
            "travelers",
            "duration_days",
            "departure_location",
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

            if key in constraints:

                normalized_constraints[key] = (
                    constraints[key]
                )

            elif key in trip_information:

                normalized_constraints[key] = (
                    trip_information[key]
                )

            else:

                normalized_constraints[key] = (
                    [] if key == "other"
                    else None
                )

        # ------------------------------------------------------
        # main.py's collected information has priority.
        #
        # This prevents the LLM from accidentally changing
        # hard user-provided constraints.
        # ------------------------------------------------------

        for key in constraint_keys:

            if key in trip_information:

                normalized_constraints[key] = (
                    trip_information[key]
                )

        # ======================================================
        # MOOD SCORE CALCULATION
        # ======================================================

        score_profile = self.score_helper.analyze_profile(
            {
                "wanted": wanted,
                "avoid": avoid
            }
        )

        scores = score_profile.get(
            "combined",
            {}
        )

        # ======================================================
        # FINAL USER PROFILE
        # ======================================================

        final_profile = {

            "wanted": wanted,

            "avoid": avoid,

            "scores": scores,

            "score_details": score_profile,

            "constraints": normalized_constraints,

            "summary": str(
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

        return final_profile