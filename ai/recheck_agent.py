import os
import json
import requests

from typing import Dict, Any

from dotenv import load_dotenv


load_dotenv()


class RecheckAgent:
    """
    Recheck Agent

    Model:
        Ollama Gemma4:26b

    Responsibility:
        1. Receive ONE worker result.
        2. Check the result for completeness and consistency.
        3. Correct obvious problems when possible.
        4. Return PASS or FAIL.
        5. Return the corrected worker result when PASS.

    RecheckAgent does NOT:
        - perform web searches
        - use Tavily
        - call workers
        - retry workers
        - select destinations
        - generate destinations
        - use Pexels
        - use MapTiler
        - calculate total budget
        - communicate with TravelAgent

    IMPORTANT:
        If the result is FAIL, main.py is responsible for
        calling the SAME worker again.

    Architecture:

        Worker
           |
           v
        RecheckAgent
           |
        +--+--+
        |     |
      PASS   FAIL
        |     |
        v     v
     Structure  main.py
                |
                v
              Worker
                |
                v
             Recheck
    """

    OLLAMA_API_URL = os.getenv(
        "OLLAMA_RECHECK_API_URL",
        "https://ollama.com/api/chat"
    )

    def __init__(self):
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
        Recheck ONE worker result.

        Returns:

            {
                "status": "PASS",
                "result": {...},
                "issues": []
            }

        OR:

            {
                "status": "FAIL",
                "result": null,
                "issues": [...]
            }

        RecheckAgent does not retry the worker.
        """

        # -----------------------------------------------------
        # Validate input
        # -----------------------------------------------------

        self._validate_worker_result(
            worker_result
        )

        # -----------------------------------------------------
        # Send result to Gemma4:26b
        # -----------------------------------------------------

        result = self._ask_ollama(
            worker_result
        )

        # -----------------------------------------------------
        # Validate Recheck response
        # -----------------------------------------------------

        return self._validate_recheck_response(
            result,
            worker_result
        )

    # =========================================================
    # OLLAMA
    # =========================================================

    def _ask_ollama(
        self,
        worker_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Ask Gemma4:26b to inspect one worker result.
        """

        worker_json = json.dumps(
            worker_result,
            ensure_ascii=False,
            indent=2,
            default=str
        )

        system_prompt = """
You are the Recheck Agent in a multi-agent travel
research system.

Your ONLY job is to inspect ONE research result produced
by a research worker.

You are a verification and correction layer.

You MUST:

1. Check that every required field exists.
2. Check that the destination is consistent.
3. Check that the country is consistent.
4. Check that there are exactly 3 major attractions.
5. Check that the attractions are valid strings.
6. Check that cost fields are numeric or null.
7. Check that cost values are not negative.
8. Check that the summary is valid.
9. Check for obvious contradictions or malformed values.
10. Correct an obvious formatting/value problem when it can
    be safely corrected from the supplied worker result.
11. Use null when a cost cannot be considered reliable.

You MUST NOT:

- search the web
- use Tavily
- call any worker
- retry the worker
- select another destination
- generate a destination
- use Pexels
- use MapTiler
- calculate total_budget
- add unsupported facts
- invent prices
- invent attractions
- return Markdown
- return explanations outside JSON
- return reasoning

IMPORTANT:

If the result is acceptable after validation/correction,
return status "PASS".

If the result contains a problem that cannot safely be
corrected from the supplied information, return status "FAIL".

A FAIL does NOT mean you should retry anything.
The external orchestrator will call the worker again.

Use EXACTLY this structure:

{
    "status": "PASS",
    "result": {
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
    },
    "issues": []
}

For FAIL:

{
    "status": "FAIL",
    "result": null,
    "issues": [
        "description of problem"
    ]
}

Rules:

- status must be exactly PASS or FAIL.
- PASS must contain a complete result.
- FAIL must contain result as null.
- issues must always be a list.
- Do not include total_budget.
"""

        user_prompt = f"""
WORKER RESULT
=============

{worker_json}

Inspect this result according to your rules.

Return ONLY the required JSON object.
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
                "temperature": 0.0
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
        ) as exc:

            raise RuntimeError(
                "Unexpected Ollama response from "
                "RecheckAgent."
            ) from exc

        return self._extract_json(
            content
        )

    # =========================================================
    # WORKER RESULT VALIDATION
    # =========================================================

    def _validate_worker_result(
        self,
        worker_result: Dict[str, Any]
    ) -> None:
        """
        Validate the basic worker schema before sending it
        to Gemma.
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

        if not isinstance(
            worker_result["destination"],
            str
        ):

            raise TypeError(
                "Worker destination must be a string."
            )

        if not isinstance(
            worker_result["country"],
            str
        ):

            raise TypeError(
                "Worker country must be a string."
            )

    # =========================================================
    # RECHECK RESPONSE VALIDATION
    # =========================================================

    def _validate_recheck_response(
        self,
        response: Dict[str, Any],
        original_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Validate and normalize Gemma's PASS/FAIL response.
        """

        if not isinstance(
            response,
            dict
        ):

            raise RuntimeError(
                "RecheckAgent expected a JSON object."
            )

        status = response.get(
            "status"
        )

        if status not in (
            "PASS",
            "FAIL"
        ):

            raise RuntimeError(
                "RecheckAgent status must be PASS or FAIL."
            )

        issues = response.get(
            "issues",
            []
        )

        if not isinstance(
            issues,
            list
        ):

            raise RuntimeError(
                "RecheckAgent issues must be a list."
            )

        # -----------------------------------------------------
        # FAIL
        # -----------------------------------------------------

        if status == "FAIL":

            return {
                "status": "FAIL",
                "result": None,
                "issues": [
                    str(issue)
                    for issue in issues
                ]
            }

        # -----------------------------------------------------
        # PASS
        # -----------------------------------------------------

        corrected_result = response.get(
            "result"
        )

        if not isinstance(
            corrected_result,
            dict
        ):

            raise RuntimeError(
                "PASS response must contain a result object."
            )

        self._validate_passed_result(
            corrected_result,
            original_result
        )

        # Never allow total_budget through.
        corrected_result.pop(
            "total_budget",
            None
        )

        return {
            "status": "PASS",
            "result": corrected_result,
            "issues": [
                str(issue)
                for issue in issues
            ]
        }

    # =========================================================
    # PASSED RESULT VALIDATION
    # =========================================================

    def _validate_passed_result(
        self,
        result: Dict[str, Any],
        original_result: Dict[str, Any]
    ) -> None:
        """
        Ensure the corrected result still belongs to the
        same destination and follows the worker schema.
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
                    f"RecheckAgent PASS result is missing "
                    f"field: {field}"
                )

        # -----------------------------------------------------
        # Destination cannot change
        # -----------------------------------------------------

        original_destination = (
            original_result["destination"]
            .strip()
            .lower()
        )

        returned_destination = (
            str(result["destination"])
            .strip()
            .lower()
        )

        if (
            original_destination
            != returned_destination
        ):

            raise RuntimeError(
                "RecheckAgent cannot change the destination."
            )

        # -----------------------------------------------------
        # Country cannot change
        # -----------------------------------------------------

        original_country = (
            original_result["country"]
            .strip()
            .lower()
        )

        returned_country = (
            str(result["country"])
            .strip()
            .lower()
        )

        if (
            original_country
            != returned_country
        ):

            raise RuntimeError(
                "RecheckAgent cannot change the country."
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
                "RecheckAgent result attractions "
                "must be a list."
            )

        if len(attractions) != 3:

            raise RuntimeError(
                "RecheckAgent result must contain "
                "exactly 3 attractions."
            )

        for attraction in attractions:

            if not isinstance(
                attraction,
                str
            ):

                raise RuntimeError(
                    "Every attraction must be a string."
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

                numeric_value = float(
                    value
                )

            except (
                ValueError,
                TypeError
            ) as exc:

                raise RuntimeError(
                    f"Invalid numeric value for {field}."
                ) from exc

            if numeric_value < 0:

                raise RuntimeError(
                    f"{field} cannot be negative."
                )

            result[field] = numeric_value

        # -----------------------------------------------------
        # Summary
        # -----------------------------------------------------

        if not isinstance(
            result["summary"],
            str
        ):

            raise RuntimeError(
                "summary must be a string."
            )

    # =========================================================
    # JSON EXTRACTION
    # =========================================================

    def _extract_json(
        self,
        content: str
    ) -> Dict[str, Any]:
        """
        Extract JSON from Gemma's response.
        """

        if not isinstance(
            content,
            str
        ):

            raise RuntimeError(
                "RecheckAgent received a non-string response."
            )

        content = content.strip()

        if not content:

            raise RuntimeError(
                "RecheckAgent received an empty response."
            )

        # -----------------------------------------------------
        # Remove Markdown fences
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

            if (
                start == -1
                or end == -1
            ):

                raise RuntimeError(
                    "RecheckAgent could not parse JSON."
                )

            try:

                result = json.loads(
                    content[
                        start:end + 1
                    ]
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