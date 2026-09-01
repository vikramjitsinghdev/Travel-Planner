import json
import os
from concurrent.futures import ThreadPoolExecutor, as_completed

from dotenv import load_dotenv
from google import genai

from workers.worker_agent1 import WorkerAgent1
from workers.worker_agent2 import WorkerAgent2
from workers.worker_agent3 import WorkerAgent3


class TravelAgent:
    """
    MAIN TRAVEL ORCHESTRATOR

    Architecture:

        MoodAgent
            |
            v
        TripRequirements
            |
            v
        Main Gemini
            |
            +---- 5 candidate destinations
            |
            +---- research plan
            |
            v
        +-----------------------+
        | Parallel Workers     |
        |                       |
        | Worker 1: Experience  |
        | Worker 2: Logistics   |
        | Worker 3: Cost        |
        +-----------------------+
            |
            v
        Evaluator
            |
            v
        Main Gemini
            |
            v
        Best 3 destinations

    TravelAgent is the ONLY component responsible for
    coordinating the three workers.

    Workers perform research.
    TravelAgent performs orchestration.
    Main Gemini performs candidate generation and final
    decision making.
    """

    # ==========================================================
    # INITIALIZATION
    # ==========================================================

    def __init__(self):

        load_dotenv()

        api_key = os.getenv(
            "GEMINI_API_KEY"
        )

        if not api_key:

            raise ValueError(
                "GEMINI_API_KEY is not set in the .env file."
            )

        self.client = genai.Client(
            api_key=api_key
        )

        self.model = os.getenv(
            "GEMINI_MAIN_MODEL",
            "gemini-3.6-flash"
        )

        # ------------------------------------------------------
        # Workers
        # ------------------------------------------------------

        self.worker1 = WorkerAgent1()
        self.worker2 = WorkerAgent2()
        self.worker3 = WorkerAgent3()

        # ------------------------------------------------------
        # Parallel worker limit
        # ------------------------------------------------------

        try:

            self.max_worker_jobs = max(
                1,
                int(
                    os.getenv(
                        "TRAVEL_WORKER_MAX_CONCURRENCY",
                        "15"
                    )
                )
            )

        except (
            TypeError,
            ValueError
        ):

            self.max_worker_jobs = 15

    # ==========================================================
    # STEP 1
    # GENERATE CANDIDATES
    # ==========================================================

    def find_candidates(
        self,
        user_input,
        preferences,
        budget,
        trip_information=None
    ):

        if not isinstance(
            user_input,
            str
        ) or not user_input.strip():

            raise ValueError(
                "user_input must be a non-empty string."
            )

        if not isinstance(
            preferences,
            dict
        ):

            raise TypeError(
                "preferences must be a dictionary."
            )

        if not isinstance(
            budget,
            dict
        ):

            raise TypeError(
                "budget must be a dictionary."
            )

        if trip_information is None:

            trip_information = {}

        if not isinstance(
            trip_information,
            dict
        ):

            raise TypeError(
                "trip_information must be a dictionary."
            )

        prompt = f"""
You are the MAIN AI ORCHESTRATOR of a travel planning
system.

Your job is to select EXACTLY FIVE destinations that deserve
further research.

You are NOT the research layer.

DO NOT browse the internet.
DO NOT claim live prices.
DO NOT claim live availability.
DO NOT search for flights.
DO NOT search for hotels.
DO NOT create an itinerary.

Use the user's requirements to create five strong research
candidates.

============================================================
USER REQUEST
============================================================

{user_input}

============================================================
TRIP REQUIREMENTS
============================================================

{json.dumps(preferences, indent=2, default=str)}

============================================================
TRIP INFORMATION
============================================================

{json.dumps(trip_information, indent=2, default=str)}

============================================================
BUDGET
============================================================

{json.dumps(budget, indent=2, default=str)}

============================================================
RULES
============================================================

1. Respect hard constraints.

2. Respect:
   - country
   - region
   - trip scope
   - travelers
   - duration
   - departure location
   - travel dates
   - budget
   - transportation preferences
   - accommodation preferences
   - safety requirements

3. Then maximize preference compatibility.

4. Make the five candidates meaningfully different.

5. Avoid choosing destinations simply because they are famous.

6. Give every candidate a research reason.

============================================================
OUTPUT
============================================================

Return ONLY valid JSON:

{{
    "research_strategy": "",
    "candidates": [
        {{
            "name": "",
            "country": "",
            "reason": "",
            "research_priority": 1
        }}
    ]
}}

Exactly five candidates are required.
"""

        response = self.client.interactions.create(
            model=self.model,
            input=prompt
        )

        content = getattr(
            response,
            "output_text",
            None
        )

        if not content:

            raise ValueError(
                "Gemini returned an empty candidate response."
            )

        result = self._parse_json_object(
            content,
            "candidate destinations"
        )

        raw_candidates = result.get(
            "candidates"
        )

        if not isinstance(
            raw_candidates,
            list
        ):

            raise ValueError(
                "Gemini candidate response does not contain "
                "a candidates list."
            )

        cleaned = []
        seen = set()

        for candidate in raw_candidates:

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

            name = name.strip()
            country = country.strip()

            if not name or not country:

                continue

            key = (
                name.lower(),
                country.lower()
            )

            if key in seen:

                continue

            seen.add(
                key
            )

            try:

                priority = int(
                    candidate.get(
                        "research_priority",
                        len(cleaned) + 1
                    )
                )

            except (
                TypeError,
                ValueError
            ):

                priority = len(cleaned) + 1

            cleaned.append({
                "name": name,
                "country": country,
                "reason": str(
                    candidate.get(
                        "reason",
                        ""
                    )
                ).strip(),
                "research_priority": priority
            })

        if len(cleaned) != 5:

            raise ValueError(
                "Main Gemini must return exactly five "
                f"unique candidates. Got {len(cleaned)}."
            )

        return {
            "research_strategy": str(
                result.get(
                    "research_strategy",
                    ""
                )
            ).strip(),

            "candidates": cleaned
        }

    # ==========================================================
    # STEP 2
    # CREATE RESEARCH PLAN
    # ==========================================================

    def create_research_plan(
        self,
        user_input,
        trip_requirements,
        candidates,
        trip_information=None
    ):

        if not isinstance(
            trip_requirements,
            dict
        ):

            raise TypeError(
                "trip_requirements must be a dictionary."
            )

        if not isinstance(
            candidates,
            list
        ):

            raise TypeError(
                "candidates must be a list."
            )

        if len(candidates) != 5:

            raise ValueError(
                "Exactly five candidates are required."
            )

        if trip_information is None:

            trip_information = {}

        prompt = f"""
You are the research-planning component of a travel AI.

Create a research plan for THREE specialized workers.

DO NOT perform the research yourself.

============================================================
USER REQUEST
============================================================

{user_input}

============================================================
TRIP REQUIREMENTS
============================================================

{json.dumps(trip_requirements, indent=2, default=str)}

============================================================
TRIP INFORMATION
============================================================

{json.dumps(trip_information, indent=2, default=str)}

============================================================
CANDIDATES
============================================================

{json.dumps(candidates, indent=2, default=str)}

============================================================
WORKERS
============================================================

WORKER 1:
Destination experience, attractions, activities,
nature, culture and suitability.

WORKER 2:
Transportation, travel time, logistics and weather.

WORKER 3:
Costs, affordability, accommodation, food and budget.

============================================================
OUTPUT
============================================================

Return ONLY valid JSON:

{{
    "worker_1_questions": {{
        "Destination": []
    }},

    "worker_2_questions": {{
        "Destination": []
    }},

    "worker_3_questions": {{
        "Destination": []
    }},

    "required_evidence": []
}}

Every candidate MUST appear in all three worker dictionaries.
"""

        response = self.client.interactions.create(
            model=self.model,
            input=prompt
        )

        content = getattr(
            response,
            "output_text",
            None
        )

        if not content:

            raise ValueError(
                "Gemini returned an empty research plan."
            )

        result = self._parse_json_object(
            content,
            "research plan"
        )

        for key in (
            "worker_1_questions",
            "worker_2_questions",
            "worker_3_questions"
        ):

            if not isinstance(
                result.get(key),
                dict
            ):

                result[key] = {}

        if not isinstance(
            result.get(
                "required_evidence"
            ),
            list
        ):

            result[
                "required_evidence"
            ] = []

        return result

    # ==========================================================
    # STEP 3
    # PARALLEL WORKER RESEARCH
    # ==========================================================

    def research_candidates(
        self,
        candidates,
        trip_requirements,
        research_plan=None
    ):

        if not isinstance(
            candidates,
            list
        ):

            raise TypeError(
                "candidates must be a list."
            )

        if len(candidates) != 5:

            raise ValueError(
                "Exactly five candidates are required."
            )

        if not isinstance(
            trip_requirements,
            dict
        ):

            raise TypeError(
                "trip_requirements must be a dictionary."
            )

        if research_plan is None:

            research_plan = {}

        worker1_questions = research_plan.get(
            "worker_1_questions",
            {}
        )

        worker2_questions = research_plan.get(
            "worker_2_questions",
            {}
        )

        worker3_questions = research_plan.get(
            "worker_3_questions",
            {}
        )

        jobs = []

        for candidate in candidates:

            destination = str(
                candidate.get(
                    "name",
                    ""
                )
            ).strip()

            country = str(
                candidate.get(
                    "country",
                    ""
                )
            ).strip()

            if not destination:

                continue

            jobs.append((
                "worker_1",
                destination,
                country,
                worker1_questions.get(
                    destination,
                    []
                )
            ))

            jobs.append((
                "worker_2",
                destination,
                country,
                worker2_questions.get(
                    destination,
                    []
                )
            ))

            jobs.append((
                "worker_3",
                destination,
                country,
                worker3_questions.get(
                    destination,
                    []
                )
            ))

        results = {
            "worker_1": {},
            "worker_2": {},
            "worker_3": {},
            "errors": []
        }

        def run_worker(job):

            worker_name = job[0]
            destination = job[1]
            country = job[2]
            questions = job[3]

            if worker_name == "worker_1":

                output = self.worker1.research(
                    destination=destination,
                    country=country,
                    trip_requirements=trip_requirements,
                    research_questions=questions
                )

            elif worker_name == "worker_2":

                output = self.worker2.research(
                    destination=destination,
                    country=country,
                    trip_requirements=trip_requirements,
                    research_questions=questions
                )

            else:

                output = self.worker3.research(
                    destination=destination,
                    country=country,
                    trip_requirements=trip_requirements,
                    research_questions=questions
                )

            return (
                worker_name,
                destination,
                output
            )

        if not jobs:

            raise ValueError(
                "No worker jobs were created."
            )

        worker_count = min(
            self.max_worker_jobs,
            len(jobs)
        )

        with ThreadPoolExecutor(
            max_workers=worker_count
        ) as executor:

            future_map = {
                executor.submit(
                    run_worker,
                    job
                ): job

                for job in jobs
            }

            for future in as_completed(
                future_map
            ):

                job = future_map[
                    future
                ]

                try:

                    worker_name, destination, output = (
                        future.result()
                    )

                    results[
                        worker_name
                    ][
                        destination
                    ] = output

                except Exception as error:

                    worker_name = job[0]
                    destination = job[1]
                    country = job[2]

                    results[
                        "errors"
                    ].append({
                        "worker":
                            worker_name,

                        "destination":
                            destination,

                        "error":
                            str(error)
                    })

                    results[
                        worker_name
                    ][
                        destination
                    ] = {
                        "destination":
                            destination,

                        "country":
                            country,

                        "error":
                            str(error)
                    }

        return results

    # ==========================================================
    # STEP 4
    # EVALUATOR
    # ==========================================================

    def evaluate_candidates(
        self,
        candidates,
        trip_requirements,
        research_results
    ):

        if not isinstance(
            candidates,
            list
        ):

            raise TypeError(
                "candidates must be a list."
            )

        if not isinstance(
            research_results,
            dict
        ):

            raise TypeError(
                "research_results must be a dictionary."
            )

        worker1 = research_results.get(
            "worker_1",
            {}
        )

        worker2 = research_results.get(
            "worker_2",
            {}
        )

        worker3 = research_results.get(
            "worker_3",
            {}
        )

        evaluations = []

        for candidate in candidates:

            destination = str(
                candidate.get(
                    "name",
                    ""
                )
            ).strip()

            country = str(
                candidate.get(
                    "country",
                    ""
                )
            ).strip()

            r1 = worker1.get(
                destination,
                {}
            )

            r2 = worker2.get(
                destination,
                {}
            )

            r3 = worker3.get(
                destination,
                {}
            )

            preference = self._fit_score(
                r1.get(
                    "preference_fit",
                    {}
                )
            )

            weather = self._fit_score(
                r2.get(
                    "weather_preference_fit",
                    {}
                )
            )

            budget = self._budget_score(
                r3
            )

            practicality = self._practicality_score(
                r2
            )

            travel_effort = self._travel_effort_score(
                r2
            )

            evidence = self._evidence_score(
                r1,
                r2,
                r3
            )

            overall = round(
                budget * 0.25
                + preference * 0.25
                + practicality * 0.20
                + weather * 0.15
                + travel_effort * 0.10
                + evidence * 0.05,
                2
            )

            evaluations.append({
                "destination":
                    destination,

                "country":
                    country,

                "scores": {
                    "budget":
                        budget,

                    "preference":
                        preference,

                    "practicality":
                        practicality,

                    "weather":
                        weather,

                    "travel_effort":
                        travel_effort,

                    "evidence_quality":
                        evidence,

                    "overall":
                        overall
                }
            })

        evaluations.sort(
            key=lambda item:
                item["scores"]["overall"],
            reverse=True
        )

        for rank, item in enumerate(
            evaluations,
            start=1
        ):

            item["rank"] = rank

        return {
            "weights": {
                "budget": 0.25,
                "preference": 0.25,
                "practicality": 0.20,
                "weather": 0.15,
                "travel_effort": 0.10,
                "evidence_quality": 0.05
            },

            "candidates":
                evaluations
        }

    # ==========================================================
    # STEP 5
    # FINAL MAIN GEMINI
    # ==========================================================

    def select_best_trips(
        self,
        user_input,
        trip_requirements,
        research_results,
        evaluation_results,
        trip_information=None,
        budget=None
    ):

        if trip_information is None:
            trip_information = {}

        if budget is None:
            budget = {}

        prompt = f"""
You are the FINAL DECISION-MAKER for a travel planning
system.

Five destinations were researched by three specialized
workers.

An independent evaluator scored the destinations.

Select EXACTLY THREE final travel options.

============================================================
USER
============================================================

{user_input}

============================================================
TRIP REQUIREMENTS
============================================================

{json.dumps(trip_requirements, indent=2, default=str)}

============================================================
TRIP INFORMATION
============================================================

{json.dumps(trip_information, indent=2, default=str)}

============================================================
BUDGET
============================================================

{json.dumps(budget, indent=2, default=str)}

============================================================
WORKER RESEARCH
============================================================

{json.dumps(research_results, indent=2, default=str)}

============================================================
EVALUATION
============================================================

{json.dumps(evaluation_results, indent=2, default=str)}

============================================================
RULES
============================================================

1. Hard constraints must be respected.

2. Use evaluator scores.

3. Use worker evidence.

4. Never invent facts.

5. Never invent prices.

6. Never claim availability.

7. Never browse.

8. Explain why each option fits.

9. Mention important limitations.

10. Return exactly three options.

============================================================
OUTPUT
============================================================

Return ONLY valid JSON:

{{
    "selected_trips": [
        {{
            "rank": 1,
            "destination": "",
            "country": "",
            "why_it_fits": "",
            "highlights": [],
            "limitations": [],
            "budget_summary": "",
            "practicality_summary": "",
            "weather_summary": "",
            "confidence": ""
        }},
        {{
            "rank": 2,
            "destination": "",
            "country": "",
            "why_it_fits": "",
            "highlights": [],
            "limitations": [],
            "budget_summary": "",
            "practicality_summary": "",
            "weather_summary": "",
            "confidence": ""
        }},
        {{
            "rank": 3,
            "destination": "",
            "country": "",
            "why_it_fits": "",
            "highlights": [],
            "limitations": [],
            "budget_summary": "",
            "practicality_summary": "",
            "weather_summary": "",
            "confidence": ""
        }}
    ]
}}
"""

        response = self.client.interactions.create(
            model=self.model,
            input=prompt
        )

        content = getattr(
            response,
            "output_text",
            None
        )

        if not content:

            raise ValueError(
                "Gemini returned an empty final selection."
            )

        result = self._parse_json_object(
            content,
            "final trip selection"
        )

        selected = result.get(
            "selected_trips"
        )

        if not isinstance(
            selected,
            list
        ):

            raise ValueError(
                "Final Gemini response is missing "
                "selected_trips."
            )

        if len(selected) != 3:

            raise ValueError(
                "Final Gemini must return exactly "
                f"3 trips. Got {len(selected)}."
            )

        return {
            "selected_trips":
                selected
        }

    # ==========================================================
    # COMPLETE PIPELINE
    # ==========================================================

    def orchestrate(
        self,
        user_input,
        trip_requirements,
        trip_information,
        budget
    ):

        candidate_result = self.find_candidates(
            user_input=user_input,
            preferences=trip_requirements,
            budget=budget,
            trip_information=trip_information
        )

        candidates = candidate_result[
            "candidates"
        ]

        research_plan = self.create_research_plan(
            user_input=user_input,
            trip_requirements=trip_requirements,
            candidates=candidates,
            trip_information=trip_information
        )

        research_results = self.research_candidates(
            candidates=candidates,
            trip_requirements=trip_requirements,
            research_plan=research_plan
        )

        evaluation_results = self.evaluate_candidates(
            candidates=candidates,
            trip_requirements=trip_requirements,
            research_results=research_results
        )

        final_result = self.select_best_trips(
            user_input=user_input,
            trip_requirements=trip_requirements,
            research_results=research_results,
            evaluation_results=evaluation_results,
            trip_information=trip_information,
            budget=budget
        )

        return {
            "candidate_result":
                candidate_result,

            "candidates":
                candidates,

            "research_plan":
                research_plan,

            "research":
                research_results,

            "evaluation":
                evaluation_results,

            "ranked_candidates":
                evaluation_results.get(
                    "candidates",
                    []
                ),

            "travel_options":
                final_result.get(
                    "selected_trips",
                    []
                )
        }

    # ==========================================================
    # SELECTED TRIP DETAIL
    # ==========================================================

    def build_selected_trip(
        self,
        selected_destination,
        user_input,
        preferences,
        budget,
        research=None,
        map_data=None,
        trip_information=None
    ):

        if research is None:
            research = {}

        if map_data is None:
            map_data = []

        if trip_information is None:
            trip_information = {}

        prompt = f"""
Create a detailed trip cost summary for the destination
selected by the user.

SELECTED DESTINATION:
{selected_destination}

USER REQUEST:
{user_input}

TRIP REQUIREMENTS:
{json.dumps(preferences, indent=2, default=str)}

BUDGET:
{json.dumps(budget, indent=2, default=str)}

RESEARCH:
{json.dumps(research, indent=2, default=str)}

MAP DATA:
{json.dumps(map_data, indent=2, default=str)}

TRIP INFORMATION:
{json.dumps(trip_information, indent=2, default=str)}

Rules:

- Do not invent prices.
- Unknown amounts must be null.
- Do not claim bookings.
- Do not claim availability.
- Use only supplied research.
- Return ONLY valid JSON.

Output:

{{
    "destination": "",
    "costs": [
        {{
            "category": "",
            "amount": null,
            "description": ""
        }}
    ],
    "total_estimated_cost": 0,
    "unknown_costs": [],
    "within_budget": true,
    "notes": []
}}
"""

        response = self.client.interactions.create(
            model=self.model,
            input=prompt
        )

        content = getattr(
            response,
            "output_text",
            None
        )

        if not content:

            raise ValueError(
                "Gemini returned an empty selected-trip response."
            )

        result = self._parse_json_object(
            content,
            "selected trip"
        )

        costs = result.get(
            "costs",
            []
        )

        if not isinstance(
            costs,
            list
        ):

            costs = []

        cleaned_costs = []

        for cost in costs:

            if not isinstance(
                cost,
                dict
            ):

                continue

            amount = cost.get(
                "amount"
            )

            if amount is not None:

                try:

                    amount = round(
                        float(amount),
                        2
                    )

                except (
                    TypeError,
                    ValueError
                ):

                    amount = None

            cleaned_costs.append({
                "category":
                    str(
                        cost.get(
                            "category",
                            "other"
                        )
                    ).strip(),

                "amount":
                    amount,

                "description":
                    str(
                        cost.get(
                            "description",
                            ""
                        )
                    ).strip()
            })

        total = round(
            sum(
                cost["amount"]
                for cost in cleaned_costs
                if cost["amount"] is not None
            ),
            2
        )

        return {
            "destination":
                str(
                    result.get(
                        "destination",
                        selected_destination
                    )
                ).strip(),

            "costs":
                cleaned_costs,

            "total_estimated_cost":
                total,

            "unknown_costs":
                result.get(
                    "unknown_costs",
                    []
                ),

            "within_budget":
                result.get(
                    "within_budget",
                    True
                ),

            "notes":
                result.get(
                    "notes",
                    []
                )
        }

    # ==========================================================
    # SCORING HELPERS
    # ==========================================================

    @staticmethod
    def _fit_score(
        fit_data,
        default=50
    ):

        if not isinstance(
            fit_data,
            dict
        ):

            return default

        matches = fit_data.get(
            "matches",
            []
        )

        partial = fit_data.get(
            "partial_matches",
            []
        )

        conflicts = fit_data.get(
            "conflicts",
            []
        )

        if not isinstance(
            matches,
            list
        ):

            matches = []

        if not isinstance(
            partial,
            list
        ):

            partial = []

        if not isinstance(
            conflicts,
            list
        ):

            conflicts = []

        score = (
            50
            + min(len(matches), 8) * 7
            + min(len(partial), 5) * 2
            - min(len(conflicts), 8) * 10
        )

        return max(
            0,
            min(
                100,
                score
            )
        )

    @staticmethod
    def _budget_score(
        research
    ):

        if not isinstance(
            research,
            dict
        ):

            return 50

        compatibility = research.get(
            "budget_compatibility",
            {}
        )

        score = TravelAgent._fit_score(
            compatibility
        )

        affordability = research.get(
            "affordability",
            {}
        )

        if isinstance(
            affordability,
            dict
        ):

            level = str(
                affordability.get(
                    "overall_level",
                    ""
                )
            ).lower()

            if level in (
                "very inexpensive",
                "inexpensive"
            ):

                score += 10

            elif level == "moderate":

                score += 3

            elif level in (
                "expensive",
                "very expensive"
            ):

                score -= 10

        return max(
            0,
            min(
                100,
                score
            )
        )

    @staticmethod
    def _practicality_score(
        research
    ):

        if not isinstance(
            research,
            dict
        ):

            return 50

        data = research.get(
            "transportation_practicality",
            {}
        )

        if not isinstance(
            data,
            dict
        ):

            return 50

        score = 50

        text = " ".join([
            str(
                data.get(
                    "convenience",
                    ""
                )
            ),
            str(
                data.get(
                    "accessibility",
                    ""
                )
            ),
            str(
                data.get(
                    "complexity",
                    ""
                )
            )
        ]).lower()

        if any(
            word in text
            for word in (
                "easy",
                "excellent",
                "convenient",
                "good"
            )
        ):

            score += 15

        if any(
            word in text
            for word in (
                "difficult",
                "poor",
                "limited",
                "complex"
            )
        ):

            score -= 15

        local_transport = research.get(
            "local_transportation",
            {}
        )

        if isinstance(
            local_transport,
            dict
        ):

            if local_transport.get(
                "car_required"
            ) is False:

                score += 5

            elif local_transport.get(
                "car_required"
            ) is True:

                score -= 10

        return max(
            0,
            min(
                100,
                score
            )
        )

    @staticmethod
    def _travel_effort_score(
        research
    ):

        if not isinstance(
            research,
            dict
        ):

            return 50

        departure = research.get(
            "departure_analysis",
            {}
        )

        if not isinstance(
            departure,
            dict
        ):

            return 50

        score = 60

        complexity = str(
            departure.get(
                "connection_complexity",
                ""
            )
        ).lower()

        if any(
            word in complexity
            for word in (
                "easy",
                "simple",
                "low"
            )
        ):

            score += 20

        if any(
            word in complexity
            for word in (
                "complex",
                "difficult",
                "high",
                "multiple"
            )
        ):

            score -= 20

        if departure.get(
            "direct_travel_possible"
        ) is True:

            score += 10

        return max(
            0,
            min(
                100,
                score
            )
        )

    @staticmethod
    def _evidence_score(
        *research_objects
    ):

        total = 0
        quality = 0

        for research in research_objects:

            if not isinstance(
                research,
                dict
            ):

                continue

            evidence = research.get(
                "evidence",
                []
            )

            if not isinstance(
                evidence,
                list
            ):

                continue

            total += len(
                evidence
            )

            for item in evidence:

                if not isinstance(
                    item,
                    dict
                ):

                    continue

                if str(
                    item.get(
                        "source",
                        ""
                    )
                ).strip():

                    quality += 1

        if total == 0:

            return 20

        return max(
            0,
            min(
                100,
                20 + quality * 8
            )
        )

    # ==========================================================
    # JSON PARSER
    # ==========================================================

    @staticmethod
    def _parse_json_object(
        content,
        description="response"
    ):

        if not isinstance(
            content,
            str
        ):

            raise ValueError(
                f"Invalid Gemini {description}."
            )

        content = content.strip()

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

        start = content.find(
            "{"
        )

        end = content.rfind(
            "}"
        )

        if (
            start == -1
            or end == -1
            or end <= start
        ):

            raise ValueError(
                "Gemini did not return a JSON object "
                f"for {description}."
            )

        try:

            result = json.loads(
                content[
                    start:end + 1
                ]
            )

        except json.JSONDecodeError as error:

            raise ValueError(
                f"Invalid JSON for {description}: {error}"
            ) from error

        if not isinstance(
            result,
            dict
        ):

            raise ValueError(
                f"Gemini {description} must be a JSON object."
            )

        return result