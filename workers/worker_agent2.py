import json
import os
from typing import Any, Dict

from dotenv import load_dotenv
from openai import OpenAI


class WorkerAgent2:
    """
    WANDERLUST WORKER AGENT 2

    Independent destination research worker.

    Each invocation researches exactly ONE destination.

    Reliability:
        - JSON mode when supported.
        - Strict JSON prompting.
        - Multiple attempts.
        - Truncation detection.
        - Balanced JSON extraction.
        - Destination validation.
        - Output normalization.
    """

    def __init__(self):

        load_dotenv()

        self.api_key = os.getenv("NVIDIA_API_KEY")

        if not self.api_key:
            raise ValueError(
                "NVIDIA_API_KEY is not set in the .env file."
            )

        self.model = os.getenv(
            "NVIDIA_WORKER2_MODEL",
            "openai/gpt-oss-20b"
        )

        self.base_url = os.getenv(
            "NVIDIA_BASE_URL",
            "https://integrate.api.nvidia.com/v1"
        )

        self.client = OpenAI(
            api_key=self.api_key,
            base_url=self.base_url
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
You are WANDERLUST WORKER AGENT 2.

You are an independent destination research worker.

ASSIGNED DESTINATION:
{destination}

COUNTRY:
{country}

Research ONLY the assigned destination.

USER REQUIREMENTS:
{requirements_json}

============================================================
DESTINATION BOUNDARY
============================================================

You MUST remain focused on {destination}.

Do NOT:

- select destinations
- compare destinations
- rank destinations
- recommend alternatives
- research alternative destinations
- create itineraries
- make final travel decisions

A nearby place can be mentioned only when it is directly
necessary context for {destination}, such as transportation
or geography.

============================================================
RESEARCH
============================================================

Research:

- overview
- geography
- destination character
- nature
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
- accessibility
- safety and logistics
- preference fit
- strengths
- limitations
- uncertainties
- evidence

Be comprehensive but concise.

Lists should normally contain 3-6 useful items.

============================================================
FACTUAL DISCIPLINE
============================================================

Never fabricate:

- attractions
- statistics
- exact prices
- schedules
- opening hours
- hotel availability
- flight availability
- current weather
- events
- visa rules
- exchange rates
- sources

Do not pretend general knowledge is live information.

If information is uncertain, state that it is uncertain.

============================================================
JSON OUTPUT
============================================================

Return exactly ONE valid JSON object.

The output MUST:

- begin with {{
- end with }}
- use double quotes
- contain no Markdown
- contain no code fences
- contain no comments
- contain no trailing commas
- contain no explanation outside JSON
- contain no extra top-level fields

It MUST be parseable by:

json.loads()

Keep descriptions concise enough to avoid response truncation.
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
  "worker": "worker_2",
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
    "availability_notes": [],
    "uncertainties": []
  }},

  "affordability": {{
    "overall_level": "",
    "description": "",
    "confidence": ""
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
  "evidence": [],
  "worker_summary": ""
}}

Do not add fields.

Do not remove fields.

Do not research another destination.

Return ONLY the JSON object.
"""

    # ==========================================================
    # GENERATION + RETRIES
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

Regenerate the complete report.

Make the JSON syntactically correct.
Pay special attention to commas, quotes, braces and brackets.

Return ONLY JSON.
"""

                else:

                    retry_instruction = """
Your previous response could not be parsed.

Generate a NEW concise version of the complete research.

Do not explain anything.
Do not use Markdown.
Do not use code fences.
Return ONLY valid JSON.

Shorten descriptions and lists so the response cannot be
truncated.
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
                    "max_tokens": 7000,
                    "response_format": {
                        "type": "json_object"
                    }
                }

                try:

                    response = self.client.chat.completions.create(
                        **kwargs
                    )

                except Exception as json_mode_error:

                    error_text = str(json_mode_error).lower()

                    if (
                        "response_format" not in error_text
                        and "json" not in error_text
                        and "unsupported" not in error_text
                        and "400" not in error_text
                    ):
                        raise

                    kwargs.pop("response_format", None)

                    response = self.client.chat.completions.create(
                        **kwargs
                    )

                if not response.choices:
                    raise ValueError(
                        "Worker 2 received no response choices."
                    )

                choice = response.choices[0]

                content = choice.message.content

                if not content:
                    raise ValueError(
                        "Worker 2 returned an empty response."
                    )

                finish_reason = getattr(
                    choice,
                    "finish_reason",
                    None
                )

                if finish_reason == "length":
                    raise ValueError(
                        "Worker 2 response was truncated."
                    )

                result = self._parse_json(content)

                if not isinstance(result, dict):
                    raise ValueError(
                        "Worker 2 JSON root must be an object."
                    )

                return result

            except Exception as error:

                last_error = error

                if attempt < self.max_attempts:
                    continue

        raise ValueError(
            "Worker 2 failed to produce valid JSON after "
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
                "Worker 2 response must be a string."
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
                    "Worker 2 JSON root is not an object."
                )

            return parsed

        except json.JSONDecodeError:
            pass

        candidate = WorkerAgent2._extract_json_object(text)

        if candidate is None:
            raise ValueError(
                "Worker 2 did not return a recoverable JSON object."
            )

        try:

            parsed = json.loads(candidate)

            if not isinstance(parsed, dict):
                raise ValueError(
                    "Worker 2 recovered JSON root is not an object."
                )

            return parsed

        except json.JSONDecodeError as error:

            raise ValueError(
                f"Worker 2 returned malformed JSON: {error}"
            ) from error

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
                "Worker 2 result must be a dictionary."
            )

        returned_destination = result.get("destination")

        if returned_destination:

            if (
                str(returned_destination).strip().lower()
                != destination.strip().lower()
            ):
                raise ValueError(
                    "Worker 2 researched a different destination."
                )

        result["worker"] = "worker_2"
        result["destination"] = destination
        result["country"] = country

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
    print("WORKER 2 DIRECT TEST")
    print("=" * 70)

    worker = WorkerAgent2()

    print("Model:", worker.model)
    print("Base URL:", worker.base_url)

    result = worker.research(
        destination="Kanazawa",
        country="Japan",
        trip_requirements={
            "interests": [
                "nature",
                "culture",
                "quiet places"
            ],
            "avoid": [
                "very crowded cities"
            ]
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