import json
import os
from typing import Any, Dict, Optional

from dotenv import load_dotenv
from openai import OpenAI


class WorkerAgent1:
    """
    WANDERLUST WORKER AGENT 1

    Independent destination researcher.

    Responsibilities:
        - Research exactly one assigned destination.
        - Return structured JSON.
        - Never select or compare destinations.
        - Never create an itinerary.

    Reliability features:
        - JSON-mode when supported.
        - Strict JSON prompting.
        - Multiple generation attempts.
        - JSON extraction.
        - JSON repair attempt.
        - Schema validation.
        - Destination validation.
        - Response truncation detection.
    """

    REQUIRED_FIELDS = [
        "worker",
        "destination",
        "country",
        "destination_overview",
        "destination_character",
        "nature",
        "attractions",
        "activities",
        "culture",
        "history",
        "food",
        "atmosphere",
        "transportation",
        "weather",
        "seasonal_conditions",
        "accommodation",
        "affordability",
        "accessibility",
        "safety_and_logistics",
        "preference_fit",
        "strengths",
        "limitations",
        "uncertainties",
        "evidence",
        "worker_summary",
    ]

    def __init__(self):

        load_dotenv()

        self.api_key = os.getenv("NVIDIA_API_KEY")

        if not self.api_key:
            raise ValueError(
                "NVIDIA_API_KEY is not set in the .env file."
            )

        self.model = os.getenv(
            "NVIDIA_WORKER1_MODEL",
            "openai/gpt-oss-120b"
        )

        self.base_url = os.getenv(
            "NVIDIA_BASE_URL",
            "https://integrate.api.nvidia.com/v1"
        )

        self.client = OpenAI(
            api_key=self.api_key,
            base_url=self.base_url
        )

        # Number of attempts to generate valid JSON.
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
            system_prompt=system_prompt,
            user_prompt=user_prompt
        )

        result = self._validate_and_normalize_result(
            result,
            destination,
            country
        )

        return result

    # ==========================================================
    # PROMPTS
    # ==========================================================

    @staticmethod
    def _build_system_prompt(
        destination,
        country,
        requirements_json
    ):

        return f"""
You are WANDERLUST WORKER AGENT 1.

You are an independent destination research worker.

ASSIGNED DESTINATION:
{destination}

COUNTRY:
{country}

Your ONLY research subject is {destination}.

The user's structured requirements are:

{requirements_json}

============================================================
DESTINATION BOUNDARY
============================================================

Research ONLY {destination}.

Do NOT:

- choose destinations
- recommend alternatives
- compare destinations
- rank destinations
- research other destinations
- create an itinerary
- make the final travel decision

A nearby location may be mentioned only when it is directly
necessary to explain transportation, geography, or another
fact about {destination}.

Do not turn nearby locations into separate research subjects.

============================================================
RESEARCH
============================================================

Research the following aspects of {destination}:

- overview
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
- accessibility
- safety
- preference fit
- strengths
- limitations
- uncertainties
- evidence

Keep every field concise.

Prefer 3-6 useful items in lists instead of long lists.

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

Do not pretend general information is live information.

For uncertain information, say that it is uncertain.

Do not invent a source merely to make the evidence section
look complete.

============================================================
JSON RULES
============================================================

Your entire response MUST be exactly ONE JSON object.

The response must:

- begin with {{
- end with }}
- contain no Markdown
- contain no ``` fences
- contain no explanation outside JSON
- use double quotes for keys
- use double quotes for strings
- use true, false, or null for JSON values
- contain no comments
- contain no trailing commas
- contain no single-quoted strings
- contain no additional top-level fields

The result must be directly parseable by Python:

json.loads()

Keep text concise enough that the complete JSON response fits
comfortably within the response limit.
"""

    @staticmethod
    def _build_user_prompt(
        destination,
        country,
        requirements_json
    ):

        return f"""
Research ONLY {destination}, {country}.

User requirements:

{requirements_json}

Return exactly this JSON structure:

{{
  "worker": "worker_1",
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

IMPORTANT:

Do not add fields.

Do not remove fields.

Do not research another destination.

Return ONLY the JSON object.
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

                extra_instruction = ""

                if attempt == 2:
                    extra_instruction = """
Your previous response was invalid JSON.

Regenerate the ENTIRE research report.

Pay special attention to:
- commas
- quotation marks
- brackets
- braces
- JSON booleans
- no trailing commas

Return ONLY valid JSON.
"""

                elif attempt == 3:
                    extra_instruction = """
The previous response could not be parsed as JSON.

Return a fresh, concise version of the complete report.

Do not attempt to explain the problem.
Do not use Markdown.
Do not output anything except valid JSON.

Keep descriptions short so the response cannot be truncated.
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
                            + extra_instruction
                        )
                    }
                ]

                kwargs = {
                    "model": self.model,
                    "messages": messages,
                    "temperature": 0,
                    "max_tokens": 7000
                }

                # Ask the provider for JSON when possible.
                kwargs["response_format"] = {
                    "type": "json_object"
                }

                try:
                    response = self.client.chat.completions.create(
                        **kwargs
                    )

                except Exception as json_mode_error:

                    # Some providers/models don't support
                    # response_format. Retry this same attempt
                    # without JSON mode.
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
                        "Worker 1 received no response choices."
                    )

                choice = response.choices[0]

                content = choice.message.content

                if not content:
                    raise ValueError(
                        "Worker 1 returned an empty response."
                    )

                # --------------------------------------------------
                # Detect token truncation.
                # --------------------------------------------------

                finish_reason = getattr(
                    choice,
                    "finish_reason",
                    None
                )

                if finish_reason == "length":
                    raise ValueError(
                        "Worker 1 response was truncated by "
                        "the model token limit."
                    )

                result = self._parse_json(content)

                if not isinstance(result, dict):
                    raise ValueError(
                        "Worker 1 JSON root is not an object."
                    )

                return result

            except Exception as error:

                last_error = error

                if attempt < self.max_attempts:
                    continue

        raise ValueError(
            "Worker 1 failed to produce valid JSON after "
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
                "Worker 1 response must be a string."
            )

        text = content.strip()

        # Remove code fences if a model ignores instructions.
        if text.startswith("```"):

            lines = text.splitlines()

            if lines and lines[0].strip().startswith("```"):
                lines = lines[1:]

            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]

            text = "\n".join(lines).strip()

        # First attempt: entire response.
        try:

            parsed = json.loads(text)

            if not isinstance(parsed, dict):
                raise ValueError(
                    "Worker 1 JSON root must be an object."
                )

            return parsed

        except json.JSONDecodeError:
            pass

        # Second attempt: extract balanced object.
        candidate = WorkerAgent1._extract_json_object(text)

        if candidate is None:
            raise ValueError(
                "Worker 1 did not return a recoverable JSON object."
            )

        try:

            parsed = json.loads(candidate)

            if not isinstance(parsed, dict):
                raise ValueError(
                    "Worker 1 recovered JSON root is not an object."
                )

            return parsed

        except json.JSONDecodeError as error:

            raise ValueError(
                f"Worker 1 returned malformed JSON: {error}"
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
    # VALIDATION
    # ==========================================================

    def _validate_and_normalize_result(
        self,
        result,
        destination,
        country
    ):

        if not isinstance(result, dict):
            raise ValueError(
                "Worker 1 result must be a dictionary."
            )

        returned_destination = result.get("destination")

        if returned_destination:

            if (
                str(returned_destination).strip().lower()
                != destination.strip().lower()
            ):
                raise ValueError(
                    "Worker 1 researched a different destination."
                )

        result["worker"] = "worker_1"
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
    print("WORKER 1 DIRECT TEST")
    print("=" * 70)

    worker = WorkerAgent1()

    print("Model:", worker.model)
    print("Base URL:", worker.base_url)

    result = worker.research(
        destination="Hakone",
        country="Japan",
        trip_requirements={
            "interests": [
                "nature",
                "mountains",
                "peace",
                "culture"
            ],
            "avoid": [
                "large crowded cities"
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