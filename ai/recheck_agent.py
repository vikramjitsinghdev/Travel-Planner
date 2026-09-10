import json
import os
import requests

from typing import Dict, Any

from dotenv import load_dotenv


class RecheckAgent:
    """
    Recheck Agent

    LLM:
        Ollama Gemma 4:26b

    Responsibility:
        1. Receive a completed worker result.
        2. Check the research result for completeness,
           consistency, and obvious errors.
        3. Correct the result itself when necessary.
        4. Return the corrected standardized result.

    RecheckAgent does NOT:
        - perform web searches
        - use Tavily
        - search for images
        - search maps
        - calculate the final budget
        - access databases
        - generate destinations
        - communicate with other workers

    Architecture:

        Worker 1 ──┐
        Worker 2 ──┼──> RecheckAgent
        Worker 3 ──┘
                       |
                       v
                Corrected Results
                       |
                       v
                 Budget / Structure
    """

    OLLAMA_API_URL = os.getenv(
        "OLLAMA_RECHECK_API_URL",
        "https://ollama.com/api/chat"
    )

    def __init__(self):

        load_dotenv()

        # =====================================================
        # OLLAMA
        # =====================================================

        self.ollama_api_key = os.getenv(
            "OLLAMA_API_KEY_RECHECK"
        )

        self.ollama_model = os.getenv(
            "OLLAMA_RECHECK_MODEL",
            "gemma4:26b"
        )

        if not self.ollama_api_key:
            raise ValueError(
                "OLLAMA_API_KEY_RECHECK was not found."
            )

    # =========================================================
    # PUBLIC METHOD
    # =========================================================

    def recheck(
        self,
        worker_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Recheck and correct one completed worker result.

        Args:
            worker_result:
                Standardized result returned by Worker 1,
                Worker 2, or Worker 3.

        Returns:
            Corrected standardized worker result.
        """

        self._validate_worker_result(
            worker_result
        )

        result = self._recheck_with_ollama(
            worker_result
        )

        return self._validate_rechecked_result(
            result,
            worker_result["destination"]
        )

    # =========================================================
    # VALIDATE WORKER RESULT
    # =========================================================

    def _validate_worker_result(
        self,
        worker_result: Dict[str, Any]
    ) -> None:
        """
        Validate that the worker produced the expected
        standardized research structure.

        This is structural validation only.
        """

        if not isinstance(
            worker_result,
            dict
        ):
            raise TypeError(
                "worker_result must be a dictionary."
            )

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

        for field in required_fields:

            if field not in worker_result:

                raise ValueError(
                    f"Worker result is missing field: {field}"
                )

    # =========================================================
    # OLLAMA RECHECK
    # =========================================================

    def _recheck_with_ollama(
        self,
        worker_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Ask Gemma 4:26b to verify and correct the worker result.
        """

        worker_json = json.dumps(
            worker_result,
            ensure_ascii=False,
            separators=(",", ":"),
            default=str
        )

        system_prompt = """
You are the Recheck Agent in a multi-agent travel
research system.

Your ONLY job is to recheck ONE completed research
result produced by a worker.

The worker result has already been researched.

You must inspect it for:

1. Missing information.
2. Invalid or suspicious values.
3. Incorrect data types.
4. Inconsistent information.
5. Incorrect destination or country.
6. Invalid major attractions.
7. Clearly unreasonable cost values.
8. Incorrect interpretation of the required fields.
9. Obvious contradictions between fields.

If something is wrong, YOU must correct it.

If something is already correct, preserve it.

Do not unnecessarily change valid information.

IMPORTANT:

You are a correction and validation agent.

You MUST NOT:

- perform web searches
- use Tavily
- invent unsupported facts
- generate a different destination
- change the destination simply because another
  destination might be better
- add new fields
- remove required fields
- calculate total_budget
- return explanations
- return reasoning
- return Markdown
- return ```json
- return anything except JSON

If reliable information is unavailable for a cost field,
use null rather than inventing a number.

The final result MUST use EXACTLY this structure:

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

Rules:

- major_attractions MUST contain exactly 3 items.
- All monetary values must be numbers or null.
- Do not include currency symbols inside numbers.
- average_food_cost means average food cost PER DAY.
- daily_average_travel_cost means local transportation
  cost PER DAY.
- residence_cost means total accommodation cost for
  the requested trip.
- traveling_cost means the one-time cost of reaching
  the destination.
- Do not include total_budget.

Return ONLY the corrected JSON object.
"""

        user_prompt = f"""
WORKER RESEARCH RESULT
======================

{worker_json}

Recheck this result and correct it where necessary.

Return ONLY the corrected JSON object.
"""

        headers = {
            "Authorization": (
                f"Bearer {self.ollama_api_key}"
            ),
            "Content-Type": "application/json"
        }

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
                "temperature": 0.1
            }
        }

        response = requests.post(
            self.OLLAMA_API_URL,
            headers=headers,
            json=payload,
            timeout=180
        )

        response.raise_for_status()

        data = response.json()

        try:

            content = (
                data["message"]["content"]
            )

        except (
            KeyError,
            TypeError
        ):

            raise RuntimeError(
                "Unexpected Ollama response from "
                "RecheckAgent."
            )

        return self._extract_json(
            content
        )

    # =========================================================
    # JSON EXTRACTION
    # =========================================================

    def _extract_json(
        self,
        content: str
    ) -> Dict[str, Any]:
        """
        Parse JSON returned by Ollama.
        """

        if not content:

            raise RuntimeError(
                "RecheckAgent received an empty "
                "Ollama response."
            )

        content = content.strip()

        # -----------------------------------------------------
        # Remove Markdown fences if necessary
        # -----------------------------------------------------

        if content.startswith("```"):

            lines = content.splitlines()

            lines = lines[1:]

            if (
                lines
                and lines[-1].strip() == "```"
            ):

                lines = lines[:-1]

            content = "\n".join(
                lines
            ).strip()

        # -----------------------------------------------------
        # Parse JSON
        # -----------------------------------------------------

        try:

            result = json.loads(
                content
            )

        except json.JSONDecodeError:

            start = content.find("{")
            end = content.rfind("}")

            if start == -1 or end == -1:

                raise RuntimeError(
                    "RecheckAgent could not parse "
                    "Ollama JSON."
                )

            try:

                result = json.loads(
                    content[start:end + 1]
                )

            except json.JSONDecodeError as exc:

                raise RuntimeError(
                    "RecheckAgent received malformed JSON."
                ) from exc

        if not isinstance(
            result,
            dict
        ):

            raise RuntimeError(
                "RecheckAgent expected a JSON object."
            )

        return result

    # =========================================================
    # FINAL VALIDATION
    # =========================================================

    def _validate_rechecked_result(
        self,
        result: Dict[str, Any],
        original_destination: str
    ) -> Dict[str, Any]:
        """
        Validate the corrected result before returning it.
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

        for field in required_fields:

            if field not in result:

                raise RuntimeError(
                    f"RecheckAgent removed required "
                    f"field: {field}"
                )

        # -----------------------------------------------------
        # Destination must not change
        # -----------------------------------------------------

        result["destination"] = (
            original_destination
        )

        # -----------------------------------------------------
        # Attractions
        # -----------------------------------------------------

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
                "RecheckAgent must return exactly "
                "3 attractions."
            )

        # -----------------------------------------------------
        # Numeric fields
        # -----------------------------------------------------

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

                result[field] = float(
                    value
                )

            except (
                ValueError,
                TypeError
            ):

                result[field] = None

        # -----------------------------------------------------
        # Ensure no total_budget is returned
        # -----------------------------------------------------

        result.pop(
            "total_budget",
            None
        )

        return result