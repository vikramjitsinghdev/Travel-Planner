import json
import os
from typing import Any, Dict

from dotenv import load_dotenv
from openai import OpenAI


class WorkerAgent3:
    """
    WANDERLUST WORKER AGENT 3

    Independent destination research worker.

    Researches exactly one assigned destination.

    It does NOT:
        - choose destinations
        - compare destinations
        - rank destinations
        - recommend alternatives
        - create itineraries
        - make final decisions

    Reliability:
        - Optional JSON mode.
        - Strict JSON prompting.
        - Three generation attempts.
        - Truncation detection.
        - Balanced JSON extraction.
        - Destination validation.
        - Result normalization.
    """

    def __init__(self):

        load_dotenv()

        self.api_key = os.getenv("LLM7_API_TOKEN")

        if not self.api_key:
            raise ValueError(
                "LLM7_API_TOKEN is not set in the .env file."
            )

        self.model = os.getenv(
            "LLM7_WORKER3_MODEL",
            "fast"
        )

        self.base_url = os.getenv(
            "LLM7_BASE_URL",
            "https://api.llm7.io/v1"
        )

        self.client = OpenAI(
            api_key=self.api_key,
            base_url=self.base_url
        )

        self.use_json_mode = (
            os.getenv(
                "LLM7_WORKER3_JSON_MODE",
                "false"
            )
            .strip()
            .lower()
            == "true"
        )

        self.max_attempts = 3

    # ==========================================================
    # MAIN RESEARCH
    # ==========================================================

    def research(
        self,
        destination,
        country="",
        trip_requirements=None
    ) -> Dict[str, Any]:

        destination = self._validate_destination(destination)
        country = self._validate_country(country)
        trip_requirements = self._validate_requirements(
            trip_requirements
        )

        requirements_json = json.dumps(
            trip_requirements,
            ensure_ascii=False,
            default=str
        )

        system_prompt = self._build_system_prompt(
            destination,
            country,
            requirements_json
        )

        user_prompt = self._build_user_prompt(
            destination,
            country,
            requirements_json
        )

        result = self._generate_valid_result(
            system_prompt,
            user_prompt
        )

        return self._normalize_result(
            result,
            destination,
            country
        )

    # ==========================================================
    # SYSTEM PROMPT
    # ==========================================================

    @staticmethod
    def _build_system_prompt(
        destination,
        country,
        requirements_json
    ):

        return f"""
You are WANDERLUST WORKER AGENT 3.

You are an independent destination research worker.

ASSIGNED DESTINATION:
{destination}

COUNTRY:
{country}

USER REQUIREMENTS:
{requirements_json}

============================================================
DESTINATION BOUNDARY
============================================================

Research EXACTLY:

{destination}

Do NOT:

- research another destination
- recommend another destination
- compare destinations
- rank destinations
- select destinations
- create itineraries
- make final travel decisions

Nearby locations may only be mentioned when they are directly
necessary context for transportation or geography.

Do not turn nearby locations into separate research subjects.

============================================================
RESEARCH
============================================================

Research:

- destination overview
- geography
- destination character
- nature
- mountains
- forests
- lakes
- rivers
- beaches
- wildlife
- parks
- scenic landscapes
- hiking
- outdoor experiences
- attractions
- activities
- culture
- history
- food
- atmosphere
- transportation
- weather
- seasonal conditions
- accommodation
- affordability
- costs
- budget compatibility
- accessibility
- safety and logistics
- preference fit
- strengths
- limitations
- uncertainties
- evidence

Keep information concise.

Use approximately 3-6 items for list fields unless more
information is genuinely necessary.

============================================================
FACTUAL DISCIPLINE
============================================================

Do not fabricate:

- attractions
- prices
- statistics
- opening hours
- schedules
- hotel availability
- flight availability
- current weather
- events
- visa rules
- exchange rates
- sources

Do not pretend general knowledge is live information.

When information is uncertain, explicitly mark it as uncertain.

============================================================
JSON OUTPUT
============================================================

Return exactly ONE JSON object.

Rules:

- First character must be {{
- Last character must be }}
- No Markdown
- No ```json
- No code fences
- No explanations
- No comments
- Double quotes only
- No trailing commas
- No additional top-level fields
- Valid JSON only

The response must be directly parseable using:

json.loads()

Keep descriptions concise enough to prevent truncation.
"""

    # ==========================================================
    # USER PROMPT
    # ==========================================================

    @staticmethod
    def _build_user_prompt(
        destination,
        country,
        requirements_json
    ):

        return f"""
Research ONLY:

Destination: {destination}
Country: {country}

User requirements:

{requirements_json}

Return EXACTLY this JSON structure:

{{
  "worker": "worker_3",
  "destination": "{destination}",
  "country": "{country}",

  "destination_overview": {{
    "description": "",
    "geography": "",
    "general_character": "",
    "known_for": []
  }},

  "destination_character": {{
    "urban": null,
    "suburban": null,
    "rural": null,
    "wilderness_oriented": null,
    "coastal": null,
    "mountainous": null,
    "remote": null,
    "highly_developed": null
  }},

  "nature": {{
    "mountains": [],
    "forests": [],
    "lakes": [],
    "rivers": [],
    "beaches": [],
    "wildlife": [],
    "parks": [],
    "scenic_landscapes": [],
    "hiking": [],
    "outdoor_experiences": []
  }},

  "attractions": [],

  "activities": {{
    "sightseeing": [],
    "nature": [],
    "hiking": [],
    "photography": [],
    "culture": [],
    "history": [],
    "food": [],
    "relaxation": [],
    "adventure": [],
    "entertainment": [],
    "nightlife": [],
    "shopping": []
  }},

  "culture": {{
    "description": "",
    "traditions": [],
    "cultural_experiences": []
  }},

  "history": {{
    "description": "",
    "historical_sites": [],
    "historical_significance": []
  }},

  "food": {{
    "description": "",
    "regional_cuisine": [],
    "food_experiences": []
  }},

  "atmosphere": {{
    "description": "",
    "peacefulness": "",
    "crowd_level": "",
    "tourism_intensity": "",
    "urban_intensity": ""
  }},

  "transportation": {{
    "getting_there": [],
    "airports": [],
    "trains": [],
    "buses": [],
    "roads": [],
    "public_transportation": [],
    "taxis": [],
    "rideshare": [],
    "rental_cars": [],
    "walking": [],
    "cycling": [],
    "car_dependence": "",
    "general_ease": ""
  }},

  "weather": {{
    "climate": "",
    "temperature": "",
    "rainfall": "",
    "humidity": "",
    "snow": "",
    "extreme_weather": []
  }},

  "seasonal_conditions": {{
    "spring": "",
    "summer": "",
    "autumn": "",
    "winter": ""
  }},

  "accommodation": {{
    "general_character": "",
    "types": [],
    "seasonal_variation": "",
    "availability_notes": [],
    "uncertainties": []
  }},

  "affordability": {{
    "overall_level": "",
    "description": "",
    "confidence": ""
  }},

  "costs": {{
    "accommodation": {{
      "budget": "",
      "mid_range": "",
      "higher_end": "",
      "notes": ""
    }},
    "food": {{
      "budget": "",
      "casual": "",
      "mid_range": "",
      "groceries": "",
      "notes": ""
    }},
    "transportation": {{
      "public_transport": "",
      "taxi": "",
      "rideshare": "",
      "rental_car": "",
      "other": "",
      "notes": ""
    }},
    "activities": {{
      "free": [],
      "low_cost": [],
      "moderate_cost": [],
      "expensive": []
    }},
    "daily_cost_character": {{
      "low_budget": "",
      "moderate_budget": "",
      "comfortable_budget": ""
    }},
    "major_cost_drivers": []
  }},

  "budget_compatibility": {{
    "matches": [],
    "partial_matches": [],
    "conflicts": []
  }},

  "accessibility": {{
    "general": "",
    "public_transport": "",
    "walking": "",
    "terrain": "",
    "remote_area_limitations": [],
    "mobility_considerations": []
  }},

  "safety_and_logistics": {{
    "considerations": [],
    "weather_risks": [],
    "terrain_risks": [],
    "transportation_risks": [],
    "seasonal_disruptions": []
  }},

  "preference_fit": {{
    "matches": [],
    "partial_matches": [],
    "conflicts": []
  }},

  "strengths": [],
  "limitations": [],
  "uncertainties": [],

  "evidence": [
    {{
      "claim": "",
      "source": "",
      "source_type": ""
    }}
  ],

  "worker_summary": ""
}}

IMPORTANT:

Do not add fields.

Do not remove fields.

Do not create root-level "matches",
"partial_matches", or "conflicts".

Those belong ONLY inside:

"budget_compatibility"

or:

"preference_fit"

Return ONLY JSON.
"""

    # ==========================================================
    # GENERATION
    # ==========================================================

    def _generate_valid_result(
        self,
        system_prompt,
        user_prompt
    ):

        last_error = None

        for attempt in range(1, self.max_attempts + 1):

            try:

                if attempt == 1:

                    retry_instruction = ""

                elif attempt == 2:

                    retry_instruction = """
Your previous response was invalid JSON.

Generate the complete research again.

Use strict JSON syntax.
Check every comma, quote, bracket and brace.

Return ONLY valid JSON.
"""

                else:

                    retry_instruction = """
Your previous response could not be parsed.

Generate a fresh and more concise complete report.

Do not explain.
Do not use Markdown.
Do not use code fences.

Return ONLY valid JSON.
"""

                messages = [
                    {
                        "role": "system",
                        "content": system_prompt
                    },
                    {
                        "role": "user",
                        "content": (
                            user_prompt
                            + "\n\n"
                            + retry_instruction
                        )
                    }
                ]

                kwargs = {
                    "model": self.model,
                    "messages": messages,
                    "temperature": 0,
                    "max_tokens": 7000
                }

                if self.use_json_mode:

                    kwargs["response_format"] = {
                        "type": "json_object"
                    }

                try:

                    response = self.client.chat.completions.create(
                        **kwargs
                    )

                except Exception as json_mode_error:

                    # If JSON mode isn't supported, automatically
                    # retry without it.
                    if (
                        self.use_json_mode
                        and (
                            "response_format"
                            in str(json_mode_error).lower()
                            or
                            "unsupported"
                            in str(json_mode_error).lower()
                            or
                            "json"
                            in str(json_mode_error).lower()
                            or
                            "400"
                            in str(json_mode_error)
                        )
                    ):

                        kwargs.pop(
                            "response_format",
                            None
                        )

                        response = (
                            self.client
                            .chat
                            .completions
                            .create(**kwargs)
                        )

                    else:
                        raise

                if not response.choices:

                    raise ValueError(
                        "Worker 3 received no response choices."
                    )

                choice = response.choices[0]

                content = choice.message.content

                if not content:

                    raise ValueError(
                        "Worker 3 returned an empty response."
                    )

                finish_reason = getattr(
                    choice,
                    "finish_reason",
                    None
                )

                if finish_reason == "length":

                    raise ValueError(
                        "Worker 3 response was truncated."
                    )

                result = self._parse_json(content)

                if not isinstance(result, dict):

                    raise ValueError(
                        "Worker 3 JSON root must be an object."
                    )

                return result

            except Exception as error:

                last_error = error

                if attempt < self.max_attempts:
                    continue

        raise ValueError(
            "Worker 3 failed to produce valid JSON after "
            f"{self.max_attempts} attempts.\n\n"
            f"Last error: {last_error}"
        )

    # ==========================================================
    # JSON PARSER
    # ==========================================================

    @staticmethod
    def _parse_json(content):

        if not isinstance(content, str):
            raise ValueError(
                "Worker 3 response must be a string."
            )

        text = content.strip()

        if text.startswith("```"):

            lines = text.splitlines()

            if lines and lines[0].strip().startswith("```"):
                lines = lines[1:]

            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]

            text = "\n".join(lines).strip()

        try:

            parsed = json.loads(text)

            if not isinstance(parsed, dict):
                raise ValueError(
                    "Worker 3 JSON root is not an object."
                )

            return parsed

        except json.JSONDecodeError:
            pass

        candidate = WorkerAgent3._extract_json_object(text)

        if candidate is None:

            raise ValueError(
                "Worker 3 did not return a recoverable JSON object."
            )

        try:

            parsed = json.loads(candidate)

            if not isinstance(parsed, dict):
                raise ValueError(
                    "Worker 3 recovered JSON root is not an object."
                )

            return parsed

        except json.JSONDecodeError as error:

            raise ValueError(
                f"Worker 3 returned malformed JSON: {error}"
            ) from error

    # ==========================================================
    # BALANCED JSON EXTRACTION
    # ==========================================================

    @staticmethod
    def _extract_json_object(text):

        start = text.find("{")

        if start == -1:
            return None

        depth = 0
        in_string = False
        escape = False

        for index in range(start, len(text)):

            char = text[index]

            if in_string:

                if escape:
                    escape = False
                    continue

                if char == "\\":
                    escape = True
                    continue

                if char == '"':
                    in_string = False

                continue

            if char == '"':
                in_string = True
                continue

            if char == "{":

                depth += 1

            elif char == "}":

                depth -= 1

                if depth == 0:

                    return text[start:index + 1]

        return None

    # ==========================================================
    # NORMALIZATION
    # ==========================================================

    def _normalize_result(
        self,
        result,
        destination,
        country
    ):

        if not isinstance(result, dict):

            raise ValueError(
                "Worker 3 result must be a dictionary."
            )

        returned_destination = result.get(
            "destination"
        )

        if returned_destination:

            if (
                str(returned_destination).strip().lower()
                != destination.strip().lower()
            ):

                raise ValueError(
                    "Worker 3 researched a different destination.\n"
                    f"Expected: {destination}\n"
                    f"Returned: {returned_destination}"
                )

        # ------------------------------------------------------
        # Normalize identity.
        # ------------------------------------------------------

        result["worker"] = "worker_3"
        result["destination"] = destination
        result["country"] = country

        # ------------------------------------------------------
        # Prevent accidental legacy root-level preference fields.
        #
        # If the model ignores the schema and places these at
        # root, move them into preference_fit rather than losing
        # useful information.
        # ------------------------------------------------------

        if any(
            key in result
            for key in (
                "matches",
                "partial_matches",
                "conflicts"
            )
        ):

            preference_fit = result.get(
                "preference_fit"
            )

            if not isinstance(preference_fit, dict):
                preference_fit = {}

            for key in (
                "matches",
                "partial_matches",
                "conflicts"
            ):

                if key in result:

                    if key not in preference_fit:
                        preference_fit[key] = result[key]

                    del result[key]

            result["preference_fit"] = preference_fit

        # ------------------------------------------------------
        # Defaults.
        # ------------------------------------------------------

        defaults = {

            "destination_overview": {},

            "destination_character": {},

            "nature": {},

            "attractions": [],

            "activities": {},

            "culture": {},

            "history": {},

            "food": {},

            "atmosphere": {},

            "transportation": {},

            "weather": {},

            "seasonal_conditions": {},

            "accommodation": {},

            "affordability": {},

            "costs": {},

            "budget_compatibility": {},

            "accessibility": {},

            "safety_and_logistics": {},

            "preference_fit": {},

            "strengths": [],

            "limitations": [],

            "uncertainties": [],

            "evidence": [],

            "worker_summary": ""
        }

        for key, default_value in defaults.items():

            if key not in result or result[key] is None:
                result[key] = default_value

        return result

    # ==========================================================
    # INPUT VALIDATION
    # ==========================================================

    @staticmethod
    def _validate_destination(destination):

        if not isinstance(destination, str):

            raise TypeError(
                "destination must be a string."
            )

        destination = destination.strip()

        if not destination:

            raise ValueError(
                "destination cannot be empty."
            )

        return destination

    @staticmethod
    def _validate_country(country):

        if country is None:
            return ""

        if not isinstance(country, str):
            country = str(country)

        return country.strip()

    @staticmethod
    def _validate_requirements(trip_requirements):

        if trip_requirements is None:
            return {}

        if not isinstance(trip_requirements, dict):

            raise TypeError(
                "trip_requirements must be a dictionary."
            )

        return trip_requirements


# ==============================================================
# DIRECT TEST
# ==============================================================

if __name__ == "__main__":

    print("=" * 70)
    print("WORKER 3 DIRECT TEST")
    print("=" * 70)

    worker = WorkerAgent3()

    print("Model:", worker.model)
    print("Base URL:", worker.base_url)
    print("JSON mode:", worker.use_json_mode)

    result = worker.research(
        destination="Takayama",
        country="Japan",
        trip_requirements={
            "interests": [
                "nature",
                "mountains",
                "peaceful places",
                "culture"
            ],
            "avoid": [
                "very crowded cities"
            ],
            "budget": {
                "level": "moderate"
            }
        }
    )

    print()
    print("SUCCESS")
    print("=" * 70)

    print(
        json.dumps(
            result,
            indent=2,
            ensure_ascii=False
        )
    )