import json
import os

from dotenv import load_dotenv
from google import genai


class TravelAgent:
    """
    MAIN GEMINI TRAVEL REASONING AGENT

    This class is responsible ONLY for the Main Gemini stages.

    Architecture:

        User
          |
          v
        MoodAgent
          |
          v
        TripRequirements
          |
          v
        TravelAgent
          |
          +---- Generate 5 candidates
          |
          +---- Create research plan
          |
          v
        main.py
          |
          v
        ResearchAgent
          |
          +---- Ollama Worker 1
          |       Destination / Experience
          |
          +---- Ollama Worker 2
          |       Transportation / Logistics / Weather
          |
          +---- Ollama Worker 3
                  Costs / Budget
          |
          v
        Research Results
          |
          v
        TravelAgent
          |
          +---- Evaluate candidates
          |
          +---- Select best 3
          |
          v
        Frontend

    IMPORTANT:

    TravelAgent does NOT:
        - perform web research
        - call Ollama
        - call WorkerAgent1
        - call WorkerAgent2
        - call WorkerAgent3
        - perform parallel research

    main.py is responsible for connecting TravelAgent
    with ResearchAgent.
    """

    # ==========================================================
    # INITIALIZATION
    # ==========================================================

    def __init__(self):

        load_dotenv()

        api_key = os.getenv("GEMINI_API_KEY")

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
        """
        Ask Main Gemini to generate exactly five candidate
        destinations.

        No research is performed here.
        """

        if not isinstance(user_input, str) or not user_input.strip():
            raise ValueError(
                "user_input must be a non-empty string."
            )

        if not isinstance(preferences, dict):
            raise TypeError(
                "preferences must be a dictionary."
            )

        if not isinstance(budget, dict):
            raise TypeError(
                "budget must be a dictionary."
            )

        if trip_information is None:
            trip_information = {}

        if not isinstance(trip_information, dict):
            raise TypeError(
                "trip_information must be a dictionary."
            )

        prompt = f"""
You are the MAIN AI ORCHESTRATOR of a travel planning
system.

Your current task is to select EXACTLY FIVE destinations
that deserve further research.

You are NOT the research layer.

DO NOT browse the internet.
DO NOT claim live prices.
DO NOT claim live availability.
DO NOT search for flights.
DO NOT search for hotels.
DO NOT create an itinerary.

Use the user's requirements to create five strong
research candidates.

============================================================
USER REQUEST
============================================================

{user_input}

============================================================
TRIP REQUIREMENTS
============================================================

{json.dumps(
    preferences,
    indent=2,
    default=str
)}

============================================================
TRIP INFORMATION
============================================================

{json.dumps(
    trip_information,
    indent=2,
    default=str
)}

============================================================
BUDGET
============================================================

{json.dumps(
    budget,
    indent=2,
    default=str
)}

============================================================
RULES
============================================================

1. Respect all hard constraints.

2. Pay attention to:
   - country
   - region
   - trip scope
   - number of travelers
   - duration
   - departure location
   - travel dates
   - budget
   - transportation preferences
   - accommodation preferences
   - safety requirements

3. Maximize compatibility with the user's preferences.

4. Make the five candidates meaningfully different.

5. Do not select destinations simply because they are famous.

6. Each destination must have a clear research reason.

7. Do not invent live information.

8. Do not provide exact current prices.

9. Do not create an itinerary.

============================================================
OUTPUT
============================================================

Return ONLY valid JSON.

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

Exactly five unique candidates are required.
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

        raw_candidates = result.get("candidates")

        if not isinstance(raw_candidates, list):
            raise ValueError(
                "Gemini candidate response does not contain "
                "a candidates list."
            )

        cleaned = []
        seen = set()

        for candidate in raw_candidates:

            if not isinstance(candidate, dict):
                continue

            name = candidate.get("name")
            country = candidate.get("country")

            if not isinstance(name, str):
                continue

            if not isinstance(country, str):
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

            seen.add(key)

            try:
                priority = int(
                    candidate.get(
                        "research_priority",
                        len(cleaned) + 1
                    )
                )
            except (TypeError, ValueError):
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
        """
        Main Gemini determines what the research workers
        should investigate.

        It does NOT perform the research.
        """

        if not isinstance(trip_requirements, dict):
            raise TypeError(
                "trip_requirements must be a dictionary."
            )

        if not isinstance(candidates, list):
            raise TypeError(
                "candidates must be a list."
            )

        if len(candidates) != 5:
            raise ValueError(
                "Exactly five candidates are required."
            )

        if trip_information is None:
            trip_information = {}

        if not isinstance(trip_information, dict):
            raise TypeError(
                "trip_information must be a dictionary."
            )

        prompt = f"""
You are the research-planning component of a travel
planning AI.

Create a research plan for THREE specialized research
workers.

DO NOT perform the research yourself.

============================================================
USER REQUEST
============================================================

{user_input}

============================================================
TRIP REQUIREMENTS
============================================================

{json.dumps(
    trip_requirements,
    indent=2,
    default=str
)}

============================================================
TRIP INFORMATION
============================================================

{json.dumps(
    trip_information,
    indent=2,
    default=str
)}

============================================================
CANDIDATES
============================================================

{json.dumps(
    candidates,
    indent=2,
    default=str
)}

============================================================
WORKER 1
============================================================

Focus on:

- destination suitability
- attractions
- activities
- nature
- culture
- experiences
- things to do
- suitability for the user's preferences

============================================================
WORKER 2
============================================================

Focus on:

- transportation
- travel time
- departure logistics
- airport/train access
- local transportation
- weather
- seasonal considerations
- practical travel difficulties

============================================================
WORKER 3
============================================================

Focus on:

- affordability
- accommodation
- food
- activities
- transportation costs
- major trip expenses
- budget compatibility

============================================================
IMPORTANT
============================================================

Every candidate MUST appear in all three worker
question dictionaries.

Questions should be specific enough that the research
workers know exactly what information they need.

Do not answer the questions.

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
            result.get("required_evidence"),
            list
        ):
            result["required_evidence"] = []

        return result

    # ==========================================================
    # STEP 3
    # EVALUATE RESEARCH
    # ==========================================================

    def evaluate_candidates(
        self,
        candidates,
        trip_requirements,
        research_results
    ):
        """
        Deterministic evaluator.

        This stage does NOT ask Gemini to decide the scores.

        It uses the structured outputs from the three Ollama
        research workers.

        Scores:

            Budget             25%
            Preference fit     25%
            Practicality       20%
            Weather            15%
            Travel effort      10%
            Evidence quality    5%
        """

        if not isinstance(candidates, list):
            raise TypeError(
                "candidates must be a list."
            )

        if not isinstance(trip_requirements, dict):
            raise TypeError(
                "trip_requirements must be a dictionary."
            )

        if not isinstance(research_results, dict):
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

        if not isinstance(worker1, dict):
            worker1 = {}

        if not isinstance(worker2, dict):
            worker2 = {}

        if not isinstance(worker3, dict):
            worker3 = {}

        evaluations = []

        for candidate in candidates:

            if not isinstance(candidate, dict):
                continue

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

            if not isinstance(r1, dict):
                r1 = {}

            if not isinstance(r2, dict):
                r2 = {}

            if not isinstance(r3, dict):
                r3 = {}

            # --------------------------------------------------
            # Individual scores
            # --------------------------------------------------

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

            # --------------------------------------------------
            # Weighted overall score
            # --------------------------------------------------

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
                "destination": destination,
                "country": country,

                "scores": {
                    "budget": budget,
                    "preference": preference,
                    "practicality": practicality,
                    "weather": weather,
                    "travel_effort": travel_effort,
                    "evidence_quality": evidence,
                    "overall": overall
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

            "candidates": evaluations
        }

    # ==========================================================
    # STEP 4
    # FINAL GEMINI SELECTION
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
        """
        Main Gemini makes the final decision.

        It receives:

            - user requirements
            - research evidence
            - deterministic evaluator scores

        and selects exactly three destinations.
        """

        if not isinstance(trip_requirements, dict):
            raise TypeError(
                "trip_requirements must be a dictionary."
            )

        if not isinstance(research_results, dict):
            raise TypeError(
                "research_results must be a dictionary."
            )

        if not isinstance(evaluation_results, dict):
            raise TypeError(
                "evaluation_results must be a dictionary."
            )

        if trip_information is None:
            trip_information = {}

        if budget is None:
            budget = {}

        prompt = f"""
You are the FINAL DECISION-MAKER of a travel planning AI.

Five destinations were researched by three specialized
research workers.

A deterministic evaluator independently scored them.

Your task is to select EXACTLY THREE final travel options.

============================================================
USER REQUEST
============================================================

{user_input}

============================================================
TRIP REQUIREMENTS
============================================================

{json.dumps(
    trip_requirements,
    indent=2,
    default=str
)}

============================================================
TRIP INFORMATION
============================================================

{json.dumps(
    trip_information,
    indent=2,
    default=str
)}

============================================================
BUDGET
============================================================

{json.dumps(
    budget,
    indent=2,
    default=str
)}

============================================================
RESEARCH RESULTS
============================================================

{json.dumps(
    research_results,
    indent=2,
    default=str
)}

============================================================
EVALUATION RESULTS
============================================================

{json.dumps(
    evaluation_results,
    indent=2,
    default=str
)}

============================================================
DECISION RULES
============================================================

1. Respect every hard constraint.

2. Use the evaluator scores as an important signal.

3. Use the research evidence to understand WHY a
   destination received its score.

4. Do not blindly select the three highest scores if
   research evidence clearly shows a hard constraint
   violation.

5. Never invent facts.

6. Never invent prices.

7. Never claim live availability.

8. Never claim that something is booked.

9. Do not browse.

10. Do not create a detailed itinerary.

11. Explain why each selected destination fits.

12. Mention meaningful limitations.

13. Prefer evidence-backed conclusions.

14. Return exactly three options.

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

Exactly three options are required.
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

        if not isinstance(selected, list):
            raise ValueError(
                "Final Gemini response is missing "
                "selected_trips."
            )

        if len(selected) != 3:
            raise ValueError(
                "Final Gemini must return exactly "
                f"3 trips. Got {len(selected)}."
            )

        cleaned = []

        for index, trip in enumerate(
            selected,
            start=1
        ):

            if not isinstance(trip, dict):
                continue

            destination = str(
                trip.get(
                    "destination",
                    ""
                )
            ).strip()

            country = str(
                trip.get(
                    "country",
                    ""
                )
            ).strip()

            if not destination:
                continue

            highlights = trip.get(
                "highlights",
                []
            )

            limitations = trip.get(
                "limitations",
                []
            )

            if not isinstance(
                highlights,
                list
            ):
                highlights = []

            if not isinstance(
                limitations,
                list
            ):
                limitations = []

            cleaned.append({
                "rank": index,
                "destination": destination,
                "country": country,

                "why_it_fits": str(
                    trip.get(
                        "why_it_fits",
                        ""
                    )
                ).strip(),

                "highlights": [
                    str(item).strip()
                    for item in highlights
                    if str(item).strip()
                ],

                "limitations": [
                    str(item).strip()
                    for item in limitations
                    if str(item).strip()
                ],

                "budget_summary": str(
                    trip.get(
                        "budget_summary",
                        ""
                    )
                ).strip(),

                "practicality_summary": str(
                    trip.get(
                        "practicality_summary",
                        ""
                    )
                ).strip(),

                "weather_summary": str(
                    trip.get(
                        "weather_summary",
                        ""
                    )
                ).strip(),

                "confidence": str(
                    trip.get(
                        "confidence",
                        ""
                    )
                ).strip()
            })

        if len(cleaned) != 3:
            raise ValueError(
                "Final Gemini did not return three valid "
                "trip options."
            )

        return {
            "selected_trips": cleaned
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
        """
        Build a detailed cost summary after the user has
        selected one of the recommended destinations.

        This is NOT part of the candidate research stage.
        """

        if research is None:
            research = {}

        if map_data is None:
            map_data = []

        if trip_information is None:
            trip_information = {}

        prompt = f"""
Create a detailed trip cost summary for the destination
selected by the user.

============================================================
SELECTED DESTINATION
============================================================

{selected_destination}

============================================================
USER REQUEST
============================================================

{user_input}

============================================================
TRIP REQUIREMENTS
============================================================

{json.dumps(
    preferences,
    indent=2,
    default=str
)}

============================================================
BUDGET
============================================================

{json.dumps(
    budget,
    indent=2,
    default=str
)}

============================================================
RESEARCH
============================================================

{json.dumps(
    research,
    indent=2,
    default=str
)}

============================================================
MAP DATA
============================================================

{json.dumps(
    map_data,
    indent=2,
    default=str
)}

============================================================
TRIP INFORMATION
============================================================

{json.dumps(
    trip_information,
    indent=2,
    default=str
)}

============================================================
RULES
============================================================

1. Use only supplied research.

2. Do not invent prices.

3. If a price is unknown, use null.

4. Do not claim bookings.

5. Do not claim availability.

6. Do not invent transportation schedules.

7. Do not invent hotel availability.

8. Do not browse.

9. Calculate the total only from known numeric
   cost values.

10. Clearly identify unknown costs.

============================================================
OUTPUT
============================================================

Return ONLY valid JSON:

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

        if not isinstance(costs, list):
            costs = []

        cleaned_costs = []

        for cost in costs:

            if not isinstance(cost, dict):
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
                "category": str(
                    cost.get(
                        "category",
                        "other"
                    )
                ).strip(),

                "amount": amount,

                "description": str(
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

        unknown_costs = result.get(
            "unknown_costs",
            []
        )

        if not isinstance(
            unknown_costs,
            list
        ):
            unknown_costs = []

        notes = result.get(
            "notes",
            []
        )

        if not isinstance(
            notes,
            list
        ):
            notes = []

        return {
            "destination": str(
                result.get(
                    "destination",
                    selected_destination
                )
            ).strip(),

            "costs": cleaned_costs,

            "total_estimated_cost": total,

            "unknown_costs": unknown_costs,

            "within_budget": result.get(
                "within_budget",
                True
            ),

            "notes": notes
        }

    # ==========================================================
    # SCORING HELPER
    # PREFERENCE / WEATHER FIT
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

    # ==========================================================
    # SCORING HELPER
    # BUDGET
    # ==========================================================

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

    # ==========================================================
    # SCORING HELPER
    # PRACTICALITY
    # ==========================================================

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

    # ==========================================================
    # SCORING HELPER
    # TRAVEL EFFORT
    # ==========================================================

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

    # ==========================================================
    # SCORING HELPER
    # EVIDENCE QUALITY
    # ==========================================================

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
        """
        Safely parse a Gemini response that is expected
        to contain a JSON object.

        Handles normal JSON and JSON wrapped in Markdown
        code fences.
        """

        if not isinstance(
            content,
            str
        ):
            raise ValueError(
                f"Invalid Gemini {description}."
            )

        content = content.strip()

        # ------------------------------------------------------
        # Remove Markdown JSON fences
        # ------------------------------------------------------

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

        # ------------------------------------------------------
        # Find JSON object
        # ------------------------------------------------------

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

        json_text = content[
            start:end + 1
        ]

        try:

            result = json.loads(
                json_text
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