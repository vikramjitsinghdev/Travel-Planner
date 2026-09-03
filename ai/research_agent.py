import json
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Dict, Optional

from dotenv import load_dotenv
from ollama import Client

from workers.worker_agent1 import WorkerAgent1
from workers.worker_agent2 import WorkerAgent2
from workers.worker_agent3 import WorkerAgent3


load_dotenv()


class ResearchAgent:
    """
    WANDERLUST RESEARCH SUPERVISOR

    Architecture
    ------------

        TravelAgent
             |
             | exactly 3 destinations
             v
        ResearchAgent
             |
        +----+----+----+
        |    |    |
        v    v    v
       W1   W2   W3
        |    |    |
       D1   D2   D3
        |    |    |
        +----+----+
             |
             v
       Gemma verification
             |
             v
       verified research

    IMPORTANT
    ---------

    Worker 1 receives ONLY destination 1.
    Worker 2 receives ONLY destination 2.
    Worker 3 receives ONLY destination 3.

    ResearchAgent does NOT:
        - select destinations
        - rank destinations
        - choose a winner
        - create an itinerary
        - call workers directly from TravelAgent

    Gemma is ONLY a quality-control verifier.

    Gemma does NOT:
        - perform research
        - rewrite worker reports
        - rank destinations
        - select destinations
        - create itineraries
    """

    # ==========================================================
    # INITIALIZATION
    # ==========================================================

    def __init__(
        self,
        ollama_host: Optional[str] = None,
        research_model: Optional[str] = None,
    ):
        load_dotenv()

        self.ollama_host = (
            ollama_host
            or os.getenv("OLLAMA_HOST")
            or "http://localhost:11434"
        )

        self.research_model = (
            research_model
            or os.getenv("OLLAMA_RESEARCH_MODEL")
            or os.getenv("OLLAMA_MODEL")
            or "gemma4:26b"
        )

        # ------------------------------------------------------
        # Gemma performance settings
        # ------------------------------------------------------

        self.verification_enabled = (
            os.getenv(
                "OLLAMA_VERIFICATION_ENABLED",
                "true"
            ).lower()
            not in {"false", "0", "no", "off"}
        )

        self.verification_max_chars = int(
            os.getenv(
                "OLLAMA_VERIFICATION_MAX_CHARS",
                "18000"
            )
        )

        self.verification_num_predict = int(
            os.getenv(
                "OLLAMA_VERIFICATION_NUM_PREDICT",
                "300"
            )
        )

        self.verification_timeout = float(
            os.getenv(
                "OLLAMA_VERIFICATION_TIMEOUT",
                "180"
            )
        )

        # ------------------------------------------------------
        # Ollama client
        # ------------------------------------------------------

        try:
            self.client = Client(
                host=self.ollama_host,
                timeout=self.verification_timeout,
            )
        except TypeError:
            # Compatibility with older Ollama Python clients.
            self.client = Client(
                host=self.ollama_host
            )

        # ------------------------------------------------------
        # Workers
        # ------------------------------------------------------

        self.worker1 = WorkerAgent1()
        self.worker2 = WorkerAgent2()
        self.worker3 = WorkerAgent3()

        # Exactly 3 workers.
        self.max_workers = 3

    # ==========================================================
    # MAIN RESEARCH FUNCTION
    # ==========================================================

    def research(
        self,
        destinations,
        trip_requirements=None,
    ) -> Dict[str, Any]:
        """
        Research exactly three destinations.

        Returns:

        {
            "success": true,
            "destinations": {
                "destination_1": {
                    ...worker 1 research...
                },
                "destination_2": {
                    ...worker 2 research...
                },
                "destination_3": {
                    ...worker 3 research...
                }
            },
            "workers": {
                "worker_1": {...},
                "worker_2": {...},
                "worker_3": {...}
            },
            "verification": {...},
            "errors": []
        }
        """

        normalized = self._normalize_destinations(
            destinations
        )

        requirements = (
            trip_requirements
            if isinstance(trip_requirements, dict)
            else {}
        )

        d1 = normalized[0]
        d2 = normalized[1]
        d3 = normalized[2]

        print()
        print("=" * 70)
        print("WANDERLUST RESEARCH AGENT")
        print("=" * 70)

        print(
            f"Worker 1 → {d1['name']}, {d1['country']}"
        )
        print(
            f"Worker 2 → {d2['name']}, {d2['country']}"
        )
        print(
            f"Worker 3 → {d3['name']}, {d3['country']}"
        )

        print("=" * 70)
        print()

        # ------------------------------------------------------
        # Run all three workers concurrently.
        # ------------------------------------------------------

        workers = self._run_workers(
            d1,
            d2,
            d3,
            requirements
        )

        print()
        print("[ResearchAgent] All workers completed.")

        # ------------------------------------------------------
        # Gemma verification
        # ------------------------------------------------------

        if self.verification_enabled:
            print(
                "[ResearchAgent] Starting lightweight "
                "Gemma verification..."
            )

            verification = self._verify_worker_results(
                destinations=normalized,
                trip_requirements=requirements,
                worker_results=workers,
            )
        else:
            print(
                "[ResearchAgent] Gemma verification disabled."
            )

            verification = {
                "verification_enabled": False,
                "verification_success": True,
                "status": "skipped",
                "overall_notes": (
                    "Gemma verification disabled."
                ),
                "workers": {},
                "cross_worker_issues": [],
                "live_verification_required": [],
            }

        # ------------------------------------------------------
        # Worker errors
        # ------------------------------------------------------

        errors = []

        for worker_name in (
            "worker_1",
            "worker_2",
            "worker_3",
        ):
            result = workers.get(worker_name, {})

            if not result.get("success", True):
                errors.append({
                    "worker": worker_name,
                    "destination": result.get(
                        "destination"
                    ),
                    "error": result.get(
                        "error",
                        "Unknown worker error."
                    )
                })

        # ------------------------------------------------------
        # IMPORTANT:
        #
        # Gemma verification failure does NOT erase valid
        # worker research.
        #
        # This is intentional.
        # ------------------------------------------------------

        workers_successful = (
            len(errors) == 0
        )

        return {
            "success": workers_successful,

            "destinations": {
                "destination_1": workers.get(
                    "worker_1",
                    {}
                ),
                "destination_2": workers.get(
                    "worker_2",
                    {}
                ),
                "destination_3": workers.get(
                    "worker_3",
                    {}
                ),
            },

            "workers": workers,

            "verification": verification,

            "errors": errors,
        }

    # ==========================================================
    # RUN WORKERS
    # ==========================================================

    def _run_workers(
        self,
        destination_1,
        destination_2,
        destination_3,
        trip_requirements,
    ):
        """
        Run Worker 1, Worker 2 and Worker 3 concurrently.

        Each worker gets exactly ONE destination.
        """

        results = {}

        def run_worker_1():
            print(
                f"[ResearchAgent] Starting Worker 1 → "
                f"{destination_1['name']}"
            )

            result = self.worker1.research(
                destination=destination_1["name"],
                country=destination_1["country"],
                trip_requirements=trip_requirements,
            )

            return self._normalize_worker_result(
                result,
                "worker_1",
                destination_1
            )

        def run_worker_2():
            print(
                f"[ResearchAgent] Starting Worker 2 → "
                f"{destination_2['name']}"
            )

            result = self.worker2.research(
                destination=destination_2["name"],
                country=destination_2["country"],
                trip_requirements=trip_requirements,
            )

            return self._normalize_worker_result(
                result,
                "worker_2",
                destination_2
            )

        def run_worker_3():
            print(
                f"[ResearchAgent] Starting Worker 3 → "
                f"{destination_3['name']}"
            )

            result = self.worker3.research(
                destination=destination_3["name"],
                country=destination_3["country"],
                trip_requirements=trip_requirements,
            )

            return self._normalize_worker_result(
                result,
                "worker_3",
                destination_3
            )

        functions = {
            "worker_1": run_worker_1,
            "worker_2": run_worker_2,
            "worker_3": run_worker_3,
        }

        with ThreadPoolExecutor(
            max_workers=3
        ) as executor:

            futures = {
                executor.submit(function): name
                for name, function in functions.items()
            }

            for future in as_completed(futures):

                worker_name = futures[future]

                try:
                    result = future.result()

                    results[worker_name] = result

                    print(
                        f"[ResearchAgent] "
                        f"{worker_name} completed."
                    )

                except Exception as error:

                    destination = {
                        "worker_1": destination_1,
                        "worker_2": destination_2,
                        "worker_3": destination_3,
                    }[worker_name]

                    results[worker_name] = {
                        "worker": worker_name,
                        "destination": destination["name"],
                        "country": destination["country"],
                        "success": False,
                        "error": str(error),
                    }

                    print(
                        f"[ResearchAgent] "
                        f"{worker_name} FAILED: {error}"
                    )

        # Ensure all three keys exist.
        for worker_name in (
            "worker_1",
            "worker_2",
            "worker_3",
        ):
            results.setdefault(
                worker_name,
                {
                    "worker": worker_name,
                    "success": False,
                    "error": "Worker returned no result."
                }
            )

        return results

    # ==========================================================
    # NORMALIZE WORKER RESULT
    # ==========================================================

    @staticmethod
    def _normalize_worker_result(
        result,
        worker_name,
        destination
    ):
        """
        Make worker output consistent regardless of minor
        differences in worker implementation.
        """

        if isinstance(result, dict):

            normalized = dict(result)

        else:

            normalized = {
                "data": result
            }

        normalized.setdefault(
            "worker",
            worker_name
        )

        normalized.setdefault(
            "destination",
            destination["name"]
        )

        normalized.setdefault(
            "country",
            destination["country"]
        )

        normalized.setdefault(
            "success",
            True
        )

        return normalized

    # ==========================================================
    # LIGHTWEIGHT GEMMA VERIFICATION
    # ==========================================================

    def _verify_worker_results(
        self,
        destinations,
        trip_requirements,
        worker_results,
    ):
        """
        Lightweight quality-control pass.

        IMPORTANT PERFORMANCE CHANGE:

        Gemma does NOT receive the entire raw worker reports
        with unlimited context.

        The reports are compacted and truncated to a reasonable
        size.

        Gemma also has a very small output budget.

        This makes verification much faster.
        """

        compact_workers = {}

        for worker_name in (
            "worker_1",
            "worker_2",
            "worker_3",
        ):

            compact_workers[worker_name] = (
                self._compact_for_verification(
                    worker_results.get(
                        worker_name,
                        {}
                    ),
                    self.verification_max_chars // 3
                )
            )

        assignments = {
            "worker_1": {
                "destination": destinations[0]["name"],
                "country": destinations[0]["country"],
            },
            "worker_2": {
                "destination": destinations[1]["name"],
                "country": destinations[1]["country"],
            },
            "worker_3": {
                "destination": destinations[2]["name"],
                "country": destinations[2]["country"],
            },
        }

        # ------------------------------------------------------
        # Very short system prompt.
        # ------------------------------------------------------

        system_prompt = """
You are a strict quality-control verifier.

Check three travel research reports.

Do NOT research.
Do NOT rewrite reports.
Do NOT rank destinations.
Do NOT choose a destination.
Do NOT create an itinerary.

Only identify obvious problems.

Check:
- destination mismatch
- assignment violation
- major contradiction
- obvious factual problem
- missing critical information
- suspicious unsupported claims

Return ONLY valid JSON.
"""

        user_prompt = (
            "ASSIGNMENTS:\n"
            + json.dumps(
                assignments,
                ensure_ascii=False,
                separators=(",", ":"),
            )
            + "\n\nRESEARCH:\n"
            + json.dumps(
                compact_workers,
                ensure_ascii=False,
                separators=(",", ":"),
                default=str,
            )
            + "\n\nReturn exactly this structure:\n"
            + json.dumps(
                {
                    "verification_success": True,
                    "overall_notes": "",
                    "workers": {
                        "worker_1": {
                            "destination_correct": True,
                            "assignment_boundary_respected": True,
                            "quality": "good",
                            "issues": [],
                            "warnings": [],
                        },
                        "worker_2": {
                            "destination_correct": True,
                            "assignment_boundary_respected": True,
                            "quality": "good",
                            "issues": [],
                            "warnings": [],
                        },
                        "worker_3": {
                            "destination_correct": True,
                            "assignment_boundary_respected": True,
                            "quality": "good",
                            "issues": [],
                            "warnings": [],
                        },
                    },
                    "cross_worker_issues": [],
                    "live_verification_required": [],
                },
                ensure_ascii=False,
                separators=(",", ":"),
            )
        )

        try:

            response = self.client.chat(
                model=self.research_model,

                messages=[
                    {
                        "role": "system",
                        "content": system_prompt,
                    },
                    {
                        "role": "user",
                        "content": user_prompt,
                    },
                ],

                # --------------------------------------------------
                # FORCE JSON.
                # --------------------------------------------------

                format="json",

                options={
                    "temperature": 0,
                    "num_predict": self.verification_num_predict,
                },
            )

            content = self._extract_ollama_content(
                response
            )

            if not content:
                raise ValueError(
                    "Gemma returned an empty response."
                )

            verification = self._parse_json(
                content
            )

            if not isinstance(
                verification,
                dict
            ):
                raise ValueError(
                    "Gemma did not return a JSON object."
                )

            verification.setdefault(
                "verification_success",
                True
            )

            verification.setdefault(
                "overall_notes",
                ""
            )

            verification.setdefault(
                "workers",
                {}
            )

            verification.setdefault(
                "cross_worker_issues",
                []
            )

            verification.setdefault(
                "live_verification_required",
                []
            )

            verification["status"] = "completed"

            print(
                "[ResearchAgent] "
                "Gemma verification completed."
            )

            return verification

        except Exception as error:

            print(
                "[ResearchAgent] "
                f"Gemma verification FAILED: {error}"
            )

            # --------------------------------------------------
            # CRITICAL:
            #
            # Worker research remains valid.
            #
            # Verification simply becomes unavailable.
            # --------------------------------------------------

            return {
                "verification_success": False,
                "status": "failed",
                "overall_notes": (
                    "Gemma verification failed. "
                    "Worker research was preserved."
                ),
                "workers": {},
                "cross_worker_issues": [],
                "live_verification_required": [],
                "error": str(error),
            }

    # ==========================================================
    # COMPACT DATA FOR GEMMA
    # ==========================================================

    @classmethod
    def _compact_for_verification(
        cls,
        value,
        max_chars
    ):
        """
        Reduce a potentially huge worker result before sending
        it to Gemma.

        This is one of the main performance improvements.
        """

        if isinstance(value, dict):

            compact = {}

            for key, item in value.items():

                # Skip huge metadata fields.
                if key.lower() in {
                    "raw_response",
                    "full_response",
                    "prompt",
                    "messages",
                    "debug",
                    "trace",
                }:
                    continue

                compact[key] = cls._compact_value(
                    item,
                    depth=0
                )

            text = json.dumps(
                compact,
                ensure_ascii=False,
                separators=(",", ":"),
                default=str,
            )

        else:

            text = str(value)

        if len(text) <= max_chars:
            return compact if isinstance(
                value,
                dict
            ) else text

        # Preserve valid JSON where possible.
        truncated = text[:max_chars]

        return {
            "verification_excerpt": truncated,
            "truncated": True,
            "original_character_count": len(text),
        }

    @classmethod
    def _compact_value(
        cls,
        value,
        depth=0
    ):
        """
        Recursively limit deeply nested worker output.
        """

        if depth >= 4:

            if isinstance(value, str):
                return value[:1500]

            return str(value)[:1500]

        if isinstance(value, dict):

            result = {}

            for key, item in value.items():

                if key.lower() in {
                    "raw_response",
                    "full_response",
                    "prompt",
                    "messages",
                    "debug",
                    "trace",
                }:
                    continue

                result[key] = cls._compact_value(
                    item,
                    depth + 1
                )

            return result

        if isinstance(value, list):

            return [
                cls._compact_value(
                    item,
                    depth + 1
                )
                for item in value[:20]
            ]

        if isinstance(value, str):

            return value[:3000]

        return value

    # ==========================================================
    # NORMALIZE DESTINATIONS
    # ==========================================================

    @staticmethod
    def _normalize_destinations(
        destinations
    ):
        if not isinstance(
            destinations,
            list
        ):
            raise TypeError(
                "destinations must be a list."
            )

        if len(destinations) != 3:
            raise ValueError(
                "ResearchAgent requires exactly "
                "THREE destinations."
            )

        normalized = []
        seen = set()

        for index, destination in enumerate(
            destinations,
            start=1
        ):

            if isinstance(
                destination,
                str
            ):
                name = destination.strip()
                country = ""

            elif isinstance(
                destination,
                dict
            ):
                name = (
                    destination.get("name")
                    or destination.get("destination")
                    or ""
                )

                country = (
                    destination.get("country")
                    or ""
                )

                name = str(name).strip()
                country = str(country).strip()

            else:
                raise TypeError(
                    f"Destination #{index} must be "
                    "a string or dictionary."
                )

            if not name:
                raise ValueError(
                    f"Destination #{index} has no name."
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
                "index": index,
                "name": name,
                "country": country,
            })

        return normalized

    # ==========================================================
    # OLLAMA RESPONSE EXTRACTION
    # ==========================================================

    @staticmethod
    def _extract_ollama_content(
        response
    ):
        if response is None:
            return ""

        if isinstance(
            response,
            dict
        ):

            message = response.get(
                "message"
            )

            if isinstance(
                message,
                dict
            ):

                content = message.get(
                    "content"
                )

                if content:
                    return str(content)

            content = response.get(
                "content"
            )

            if content:
                return str(content)

        message = getattr(
            response,
            "message",
            None
        )

        if message is not None:

            content = getattr(
                message,
                "content",
                None
            )

            if content:
                return str(content)

        return str(response)

    # ==========================================================
    # JSON PARSER
    # ==========================================================

    @staticmethod
    def _parse_json(
        text
    ):
        if not isinstance(
            text,
            str
        ):
            raise ValueError(
                "Expected text JSON."
            )

        text = text.strip()

        # Markdown fence.
        if text.startswith("```"):

            lines = text.splitlines()

            if lines:
                lines = lines[1:]

            if (
                lines
                and lines[-1].strip() == "```"
            ):
                lines = lines[:-1]

            text = "\n".join(
                lines
            ).strip()

        # Direct parse.
        try:
            result = json.loads(text)

            if isinstance(
                result,
                dict
            ):
                return result

        except json.JSONDecodeError:
            pass

        # Balanced object.
        candidate = (
            ResearchAgent
            ._extract_json_object(text)
        )

        if candidate is None:
            raise ValueError(
                "Could not find JSON object."
            )

        try:
            result = json.loads(
                candidate
            )

        except json.JSONDecodeError as error:
            raise ValueError(
                f"Malformed Gemma JSON: {error}"
            ) from error

        if not isinstance(
            result,
            dict
        ):
            raise ValueError(
                "JSON result must be an object."
            )

        return result

    # ==========================================================
    # BALANCED JSON EXTRACTION
    # ==========================================================

    @staticmethod
    def _extract_json_object(
        text
    ):
        start = text.find("{")

        if start == -1:
            return None

        depth = 0
        in_string = False
        escaped = False

        for index in range(
            start,
            len(text)
        ):

            char = text[index]

            if in_string:

                if escaped:
                    escaped = False
                    continue

                if char == "\\":
                    escaped = True
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
                    return text[
                        start:index + 1
                    ]

        return None

    # ==========================================================
    # OLLAMA HEALTH CHECK
    # ==========================================================

    def check_ollama(
        self
    ):
        result = {
            "host": self.ollama_host,
            "research_model": self.research_model,
            "connected": False,
            "model_available": False,
        }

        try:

            response = self.client.list()

            result["connected"] = True

            models = getattr(
                response,
                "models",
                []
            )

            available = []

            for model in models:

                name = getattr(
                    model,
                    "model",
                    None
                )

                if name:
                    available.append(name)

            result["available_models"] = available

            result["model_available"] = (
                self.research_model in available
            )

        except Exception as error:

            result["error"] = str(error)

        return result

    # ==========================================================
    # DIRECT TEST
    # ==========================================================

    def test(
        self,
        destinations=None
    ):

        if destinations is None:

            destinations = [
                {
                    "name": "Hakone",
                    "country": "Japan"
                },
                {
                    "name": "Kanazawa",
                    "country": "Japan"
                },
                {
                    "name": "Takayama",
                    "country": "Japan"
                },
            ]

        requirements = {
            "interests": [
                "nature",
                "mountains",
                "culture",
                "peaceful places",
            ],
            "avoid": [
                "very crowded cities"
            ],
            "trip_length": "7 days",
            "travel_style": "balanced",
            "budget": "moderate",
        }

        return self.research(
            destinations=destinations,
            trip_requirements=requirements,
        )


if __name__ == "__main__":

    print("=" * 70)
    print("WANDERLUST RESEARCH AGENT")
    print("=" * 70)

    agent = ResearchAgent()

    print()
    print("Ollama status:")
    print(
        json.dumps(
            agent.check_ollama(),
            indent=2,
            ensure_ascii=False,
        )
    )

    print()
    print("Starting research...")

    result = agent.test()

    print()
    print("=" * 70)
    print("FINAL RESEARCH RESULT")
    print("=" * 70)

    print(
        json.dumps(
            result,
            indent=2,
            ensure_ascii=False,
            default=str,
        )
    )