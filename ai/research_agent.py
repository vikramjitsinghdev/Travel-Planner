import json
from concurrent.futures import ThreadPoolExecutor, as_completed

from ollama import Client

# ai/research_agent.py

import json
import os
import re
import traceback
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv
import ollama


load_dotenv()


class ResearchAgent:
    """
    Ollama-powered research system.

    This agent is designed for the new TravelAgent architecture:

        Gemini / TravelAgent
                |
                | destination + research questions
                v
        ResearchAgent
                |
        +-------+-------+
        |       |       |
      Worker1 Worker2 Worker3
        |       |       |
        v       v       v
      Facts   Travel   Costs
        |       |       |
        +-------+-------+
                |
                v
        Structured research
                |
                v
        Gemini / TravelAgent

    Worker 1:
        Destination facts, attractions, culture, activities,
        suitability and practical destination information.

    Worker 2:
        Transportation, travel time, logistics, weather,
        local transportation and accessibility.

    Worker 3:
        Costs, accommodation, food, activities,
        affordability and budget estimates.
    """

    def __init__(
        self,
        ollama_host: Optional[str] = None,
        worker1_model: Optional[str] = None,
        worker2_model: Optional[str] = None,
        worker3_model: Optional[str] = None,
        max_concurrency: Optional[int] = None,
    ):
        self.ollama_host = (
            ollama_host
            or os.getenv("OLLAMA_HOST")
            or "http://localhost:11434"
        )

        self.worker1_model = (
            worker1_model
            or os.getenv("OLLAMA_WORKER1_MODEL")
            or os.getenv("OLLAMA_MODEL")
            or "gemma3:4b"
        )

        self.worker2_model = (
            worker2_model
            or os.getenv("OLLAMA_WORKER2_MODEL")
            or os.getenv("OLLAMA_MODEL")
            or "gemma3:4b"
        )

        self.worker3_model = (
            worker3_model
            or os.getenv("OLLAMA_WORKER3_MODEL")
            or os.getenv("OLLAMA_MODEL")
            or "gemma3:4b"
        )

        self.max_concurrency = int(
            max_concurrency
            or os.getenv("OLLAMA_RESEARCH_MAX_CONCURRENCY", "6")
        )

        self.client = ollama.Client(host=self.ollama_host)

        self.worker_models = {
            "worker_1": self.worker1_model,
            "worker_2": self.worker2_model,
            "worker_3": self.worker3_model,
        }

    # ============================================================
    # PUBLIC API
    # ============================================================

    def research(
        self,
        destination: Any,
        preferences: Optional[Dict[str, Any]] = None,
        budget: Optional[Dict[str, Any]] = None,
        map_data: Optional[Any] = None,
        research_questions: Optional[Dict[str, Any]] = None,
        trip_requirements: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Compatibility method.

        Can research one destination or a list of destinations.

        This method is useful for older code.

        For the NEW architecture, prefer:

            research_worker(...)

        or use TravelAgent.research_candidates().
        """

        if isinstance(destination, list):
            destinations = destination
        else:
            destinations = [destination]

        requirements = trip_requirements or {}

        if preferences:
            requirements = {
                **requirements,
                "preferences": preferences,
            }

        if budget:
            requirements = {
                **requirements,
                "budget": budget,
            }

        results = {}

        with ThreadPoolExecutor(
            max_workers=min(self.max_concurrency, len(destinations))
        ) as executor:

            futures = {}

            for item in destinations:
                if isinstance(item, dict):
                    name = item.get("name") or item.get("destination")
                    country = item.get("country", "")
                else:
                    name = str(item)
                    country = ""

                futures[
                    executor.submit(
                        self.research_destination,
                        destination=name,
                        country=country,
                        trip_requirements=requirements,
                        research_questions=research_questions,
                    )
                ] = name

            for future in as_completed(futures):
                name = futures[future]

                try:
                    results[name] = future.result()
                except Exception as exc:
                    results[name] = {
                        "success": False,
                        "destination": name,
                        "error": str(exc),
                    }

        return results

    def research_destination(
        self,
        destination: str,
        country: str = "",
        trip_requirements: Optional[Dict[str, Any]] = None,
        research_questions: Optional[Any] = None,
    ) -> Dict[str, Any]:
        """
        Compatibility wrapper for researching a destination.

        IMPORTANT:
        This does not use one generic Ollama prompt.

        It executes all three specialized Ollama workers.
        """

        requirements = trip_requirements or {}

        results = {}

        worker_calls = {
            "worker_1": (
                self._worker_1_destination,
                self.worker1_model,
            ),
            "worker_2": (
                self._worker_2_transport,
                self.worker2_model,
            ),
            "worker_3": (
                self._worker_3_budget,
                self.worker3_model,
            ),
        }

        with ThreadPoolExecutor(max_workers=3) as executor:

            futures = {}

            for worker_name, (function, model) in worker_calls.items():

                worker_questions = self._get_worker_questions(
                    research_questions,
                    worker_name,
                    destination,
                )

                futures[
                    executor.submit(
                        function,
                        destination,
                        country,
                        requirements,
                        worker_questions,
                    )
                ] = worker_name

            for future in as_completed(futures):
                worker_name = futures[future]

                try:
                    results[worker_name] = future.result()
                except Exception as exc:
                    results[worker_name] = {
                        "success": False,
                        "worker": worker_name,
                        "destination": destination,
                        "error": str(exc),
                    }

        return {
            "success": True,
            "destination": destination,
            "country": country,
            "workers": results,
        }

    # ============================================================
    # NEW ARCHITECTURE API
    # ============================================================

    def research_worker(
        self,
        worker: str,
        destination: str,
        country: str = "",
        trip_requirements: Optional[Dict[str, Any]] = None,
        research_questions: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Run one specialized Ollama worker.

        worker:
            worker_1
            worker_2
            worker_3
        """

        requirements = trip_requirements or {}
        questions = research_questions or []

        if worker == "worker_1":
            return self._worker_1_destination(
                destination,
                country,
                requirements,
                questions,
            )

        if worker == "worker_2":
            return self._worker_2_transport(
                destination,
                country,
                requirements,
                questions,
            )

        if worker == "worker_3":
            return self._worker_3_budget(
                destination,
                country,
                requirements,
                questions,
            )

        raise ValueError(
            f"Unknown research worker: {worker}"
        )

    def research_all_workers(
        self,
        destination: str,
        country: str = "",
        trip_requirements: Optional[Dict[str, Any]] = None,
        research_plan: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Run Worker 1, Worker 2 and Worker 3 simultaneously.
        """

        requirements = trip_requirements or {}

        jobs = []

        for worker_name in (
            "worker_1",
            "worker_2",
            "worker_3",
        ):
            questions = self._get_worker_questions(
                research_plan,
                worker_name,
                destination,
            )

            jobs.append(
                (
                    worker_name,
                    questions,
                )
            )

        results = {}

        with ThreadPoolExecutor(max_workers=3) as executor:

            futures = {
                executor.submit(
                    self.research_worker,
                    worker_name,
                    destination,
                    country,
                    requirements,
                    questions,
                ): worker_name
                for worker_name, questions in jobs
            }

            for future in as_completed(futures):

                worker_name = futures[future]

                try:
                    results[worker_name] = future.result()

                except Exception as exc:

                    results[worker_name] = {
                        "success": False,
                        "worker": worker_name,
                        "destination": destination,
                        "error": str(exc),
                    }

        return results

    # ============================================================
    # WORKER 1
    # ============================================================

    def _worker_1_destination(
        self,
        destination: str,
        country: str,
        trip_requirements: Dict[str, Any],
        questions: List[str],
    ) -> Dict[str, Any]:

        system_prompt = """
You are Worker 1 of a travel research system.

Your ONLY responsibility is destination knowledge.

Research and reason about:

- major attractions
- interesting places
- activities
- culture
- food culture
- nature
- nightlife
- entertainment
- family friendliness
- solo travel suitability
- couples suitability
- general atmosphere
- accessibility
- destination strengths
- destination weaknesses
- suitability for the user's stated preferences

Do NOT focus on:
- flight prices
- hotel prices
- detailed transportation costs
- detailed budget calculations
- booking anything

You are NOT the final travel decision maker.

You provide evidence and analysis to another AI.

IMPORTANT:

Do not invent precise facts.

If you are uncertain, explicitly mark the information as uncertain.

Return ONLY valid JSON.
"""

        user_prompt = self._build_worker_prompt(
            destination=destination,
            country=country,
            requirements=trip_requirements,
            questions=questions,
            worker_role="destination information",
        )

        schema = {
            "worker": "worker_1",
            "destination": destination,
            "country": country,
            "summary": "",
            "attractions": [],
            "activities": [],
            "culture": [],
            "food": [],
            "nature": [],
            "nightlife": [],
            "suitability": {},
            "strengths": [],
            "limitations": [],
            "evidence": [],
            "uncertainties": [],
        }

        return self._run_ollama_worker(
            model=self.worker1_model,
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            worker_name="worker_1",
            destination=destination,
            fallback_schema=schema,
        )

    # ============================================================
    # WORKER 2
    # ============================================================

    def _worker_2_transport(
        self,
        destination: str,
        country: str,
        trip_requirements: Dict[str, Any],
        questions: List[str],
    ) -> Dict[str, Any]:

        system_prompt = """
You are Worker 2 of a travel research system.

Your ONLY responsibility is travel logistics.

Research and reason about:

- approximate flight/travel time
- typical routes
- airports
- airport-to-city logistics
- trains
- buses
- local public transportation
- taxis/rideshare
- walking practicality
- transportation convenience
- travel effort
- weather
- seasonal conditions
- likely weather during the requested travel period
- weather risks
- accessibility
- jet lag considerations
- realistic transportation difficulties

Do NOT make the final destination decision.

Do NOT focus heavily on:
- attractions
- culture
- hotel prices
- food prices

You provide evidence and analysis to another AI.

IMPORTANT:

Do not invent live schedules.

Do not pretend that a current flight or train is confirmed.

Clearly distinguish:
- generally known information
- estimates
- information that requires live verification

Return ONLY valid JSON.
"""

        user_prompt = self._build_worker_prompt(
            destination=destination,
            country=country,
            requirements=trip_requirements,
            questions=questions,
            worker_role="transportation, logistics and weather",
        )

        schema = {
            "worker": "worker_2",
            "destination": destination,
            "country": country,
            "travel_time": {},
            "airports": [],
            "international_transport": [],
            "local_transport": [],
            "weather": {},
            "seasonal_conditions": [],
            "logistics": [],
            "accessibility": [],
            "travel_effort": {},
            "risks": [],
            "evidence": [],
            "uncertainties": [],
        }

        return self._run_ollama_worker(
            model=self.worker2_model,
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            worker_name="worker_2",
            destination=destination,
            fallback_schema=schema,
        )

    # ============================================================
    # WORKER 3
    # ============================================================

    def _worker_3_budget(
        self,
        destination: str,
        country: str,
        trip_requirements: Dict[str, Any],
        questions: List[str],
    ) -> Dict[str, Any]:

        system_prompt = """
You are Worker 3 of a travel research system.

Your ONLY responsibility is travel costs and affordability.

Analyze:

- accommodation
- food
- local transportation
- attractions
- activities
- estimated daily spending
- estimated trip spending
- budget friendliness
- expensive areas
- inexpensive alternatives
- major hidden costs
- currency considerations
- whether the destination appears compatible with the user's budget

Separate:

1. Known/general price ranges
2. Estimates
3. Information requiring live verification

Do NOT make the final destination decision.

Do NOT invent exact current prices.

If the user has not supplied a complete budget,
make reasonable estimates but clearly label them.

Return ONLY valid JSON.
"""

        user_prompt = self._build_worker_prompt(
            destination=destination,
            country=country,
            requirements=trip_requirements,
            questions=questions,
            worker_role="cost, budget and affordability research",
        )

        schema = {
            "worker": "worker_3",
            "destination": destination,
            "country": country,
            "currency": "",
            "accommodation": {},
            "food": {},
            "transportation": {},
            "activities": {},
            "daily_cost": {},
            "trip_cost": {},
            "budget_fit": {},
            "expensive_items": [],
            "budget_alternatives": [],
            "hidden_costs": [],
            "evidence": [],
            "uncertainties": [],
        }

        return self._run_ollama_worker(
            model=self.worker3_model,
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            worker_name="worker_3",
            destination=destination,
            fallback_schema=schema,
        )

    # ============================================================
    # OLLAMA ENGINE
    # ============================================================

    def _run_ollama_worker(
        self,
        model: str,
        system_prompt: str,
        user_prompt: str,
        worker_name: str,
        destination: str,
        fallback_schema: Dict[str, Any],
    ) -> Dict[str, Any]:

        try:

            response = self.client.chat(
                model=model,
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
                options={
                    "temperature": 0.2,
                },
            )

            content = self._extract_ollama_content(response)

            if not content:
                raise RuntimeError(
                    f"Ollama returned an empty response for {worker_name}"
                )

            parsed = self._parse_json(content)

            if not isinstance(parsed, dict):
                raise ValueError(
                    f"Ollama response for {worker_name} was not a JSON object"
                )

            parsed.setdefault("worker", worker_name)
            parsed.setdefault("destination", destination)
            parsed["model"] = model
            parsed["success"] = True

            return parsed

        except Exception as exc:

            print(
                f"[ResearchAgent] {worker_name} failed "
                f"for {destination}: {exc}"
            )

            return {
                **fallback_schema,
                "worker": worker_name,
                "destination": destination,
                "model": model,
                "success": False,
                "error": str(exc),
            }

    # ============================================================
    # PROMPT BUILDING
    # ============================================================

    def _build_worker_prompt(
        self,
        destination: str,
        country: str,
        requirements: Dict[str, Any],
        questions: List[str],
        worker_role: str,
    ) -> str:

        requirements_json = json.dumps(
            requirements,
            indent=2,
            ensure_ascii=False,
            default=str,
        )

        questions_text = "\n".join(
            f"- {question}"
            for question in questions
        )

        if not questions_text:
            questions_text = "- Perform the most important research for your assigned role."

        return f"""
Destination:
{destination}

Country:
{country}

Your research role:
{worker_role}

USER TRIP REQUIREMENTS:
{requirements_json}

SPECIFIC RESEARCH QUESTIONS:
{questions_text}

Instructions:

1. Analyze the destination specifically for the user's requirements.
2. Answer the research questions.
3. Prioritize useful information over generic travel descriptions.
4. Clearly identify estimates and uncertainty.
5. Do not make the final destination selection.
6. Return structured JSON.
"""

    # ============================================================
    # QUESTION EXTRACTION
    # ============================================================

    def _get_worker_questions(
        self,
        research_plan: Optional[Dict[str, Any]],
        worker_name: str,
        destination: str,
    ) -> List[str]:

        if not research_plan:
            return []

        if not isinstance(research_plan, dict):
            return []

        worker_questions = research_plan.get(
            worker_name
            if worker_name.endswith("_questions")
            else f"{worker_name}_questions"
        )

        if worker_questions is None:

            worker_questions = research_plan.get(
                f"{worker_name}_questions"
            )

        if isinstance(worker_questions, dict):

            questions = worker_questions.get(destination)

            if isinstance(questions, list):
                return [
                    str(question)
                    for question in questions
                ]

        if isinstance(worker_questions, list):
            return [
                str(question)
                for question in worker_questions
            ]

        return []

    # ============================================================
    # JSON PARSING
    # ============================================================

    def _extract_ollama_content(
        self,
        response: Any,
    ) -> str:

        if response is None:
            return ""

        if isinstance(response, dict):

            message = response.get("message")

            if isinstance(message, dict):
                content = message.get("content")

                if content:
                    return str(content)

            content = response.get("content")

            if content:
                return str(content)

        try:

            message = getattr(
                response,
                "message",
                None,
            )

            if message:

                content = getattr(
                    message,
                    "content",
                    None,
                )

                if content:
                    return str(content)

        except Exception:
            pass

        return str(response)

    def _parse_json(
        self,
        text: str,
    ) -> Dict[str, Any]:

        text = text.strip()

        # Remove markdown code fences.
        text = re.sub(
            r"^```(?:json)?\s*",
            "",
            text,
            flags=re.IGNORECASE,
        )

        text = re.sub(
            r"\s*```$",
            "",
            text,
        )

        text = text.strip()

        # Direct parse.
        try:
            parsed = json.loads(text)

            if isinstance(parsed, dict):
                return parsed

        except json.JSONDecodeError:
            pass

        # Try to find a JSON object inside the response.
        start = text.find("{")
        end = text.rfind("}")

        if start != -1 and end > start:

            candidate = text[start:end + 1]

            try:
                parsed = json.loads(candidate)

                if isinstance(parsed, dict):
                    return parsed

            except json.JSONDecodeError:
                pass

        raise ValueError(
            "Could not parse Ollama response as JSON"
        )

    # ============================================================
    # HEALTH / DEBUGGING
    # ============================================================

    def check_ollama(
        self,
    ) -> Dict[str, Any]:
        """
        Check whether Ollama is reachable and configured models exist.
        """

        result = {
            "host": self.ollama_host,
            "connected": False,
            "models": {},
        }

        try:

            models_response = self.client.list()

            result["connected"] = True

            available = []

            if isinstance(models_response, dict):
                model_list = models_response.get("models", [])

                for model in model_list:

                    if isinstance(model, dict):
                        name = model.get("name")

                        if name:
                            available.append(name)

            else:

                model_list = getattr(
                    models_response,
                    "models",
                    [],
                )

                for model in model_list:

                    name = getattr(
                        model,
                        "model",
                        None,
                    )

                    if name:
                        available.append(name)

            for worker, model in self.worker_models.items():

                result["models"][worker] = {
                    "configured": model,
                    "available": model in available,
                }

            result["available_models"] = available

        except Exception as exc:

            result["error"] = str(exc)

        return result

    def test_worker(
        self,
        worker: str,
        destination: str = "Tokyo",
        country: str = "Japan",
    ) -> Dict[str, Any]:
        """
        Simple manual test for one worker.
        """

        return self.research_worker(
            worker=worker,
            destination=destination,
            country=country,
            trip_requirements={
                "trip_length": "7 days",
                "budget": "budget friendly",
                "travel_style": "balanced",
            },
            research_questions=[
                "Provide the most useful information for this destination."
            ],
        )


# ================================================================
# SIMPLE STANDALONE TEST
# ================================================================

if __name__ == "__main__":

    print("=" * 60)
    print("OLLAMA RESEARCH AGENT TEST")
    print("=" * 60)

    agent = ResearchAgent()

    print("\nOllama status:")
    print(
        json.dumps(
            agent.check_ollama(),
            indent=2,
            ensure_ascii=False,
        )
    )

    print("\nTesting Worker 1...")

    result = agent.test_worker(
        worker="worker_1",
        destination="Tokyo",
        country="Japan",
    )

    print(
        json.dumps(
            result,
            indent=2,
            ensure_ascii=False,
        )
    )