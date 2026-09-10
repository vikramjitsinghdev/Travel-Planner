import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Dict, List, Optional


# ==============================================================
# AI AGENTS
# ==============================================================

from ai.mood_agent import MoodAgent
from ai.research_agent import ResearchAgent
from ai.travel_agent import TravelAgent
from ai.recheck_agent import RecheckAgent

from workers.worker_agent1 import Worker1
from workers.worker_agent2 import Worker2
from workers.worker_agent3 import Worker3

from structure import StructureAgent


# ==============================================================
# MAIN ORCHESTRATOR
# ==============================================================

class TravelPlanner:
    """
    Main orchestration layer for the AI travel planner.

    main.py is responsible ONLY for communication between
    the individual components.

    Architecture:

        User Input
            |
            v
        MoodAgent
            |
            | TripRequirements
            v
        ResearchAgent
            |
            | exactly 3 destinations
            |
            +-------------------+-------------------+
            |                   |                   |
            v                   v                   v
         Worker 1            Worker 2            Worker 3
            |                   |                   |
            v                   v                   v
         Recheck             Recheck             Recheck
            |                   |                   |
            +-------------------+-------------------+
                                |
                                v
                         Verified Research
                                |
                                +------------------+
                                |                  |
                                v                  v
                          TravelAgent        StructureAgent
                                |                  |
                                +--------+---------+
                                         |
                                         v
                              Final Structured Backend
                                         |
                                         v
                                      Frontend

    IMPORTANT:

    - Agents do not communicate directly with each other.
    - main.py controls all data flow.
    - ResearchAgent chooses exactly 3 destinations.
    - Each worker researches exactly one destination.
    - Each worker has its own RecheckAgent.
    - A recheck starts immediately after its worker finishes.
    - Failed rechecks cause the SAME worker to retry.
    - Worker pipelines run concurrently.
    - TravelAgent handles destination information, images,
      and map coordinates.
    - StructureAgent creates the final backend structure.
    """

    # ----------------------------------------------------------
    # CONFIGURATION
    # ----------------------------------------------------------

    MAX_WORKER_RETRIES = 3

    # ----------------------------------------------------------
    # INITIALIZATION
    # ----------------------------------------------------------

    def __init__(self):
        """
        Initialize all components.

        No API keys are handled here.
        Each individual class is responsible for its own
        configuration and environment variables.
        """

        self.mood_agent = MoodAgent()
        self.research_agent = ResearchAgent()

        self.worker1 = Worker1()
        self.worker2 = Worker2()
        self.worker3 = Worker3()

        self.recheck_agent = RecheckAgent()
        self.travel_agent = TravelAgent()

        self.structure_agent = StructureAgent()

    # ==========================================================
    # VALIDATION
    # ==========================================================

    @staticmethod
    def _validate_user_input(
        user_input: str
    ) -> None:

        if not isinstance(
            user_input,
            str
        ):
            raise TypeError(
                "user_input must be a string."
            )

        if not user_input.strip():
            raise ValueError(
                "user_input cannot be empty."
            )

    # ----------------------------------------------------------

    @staticmethod
    def _validate_trip_requirements(
        requirements: Any
    ) -> Dict[str, Any]:

        if not isinstance(
            requirements,
            dict
        ):
            raise TypeError(
                "MoodAgent must return a dictionary."
            )

        return requirements

    # ----------------------------------------------------------

    @staticmethod
    def _validate_research_result(
        research_result: Any
    ) -> Dict[str, Any]:

        if not isinstance(
            research_result,
            dict
        ):
            raise TypeError(
                "ResearchAgent must return a dictionary."
            )

        destinations = research_result.get(
            "destinations"
        )

        if not isinstance(
            destinations,
            list
        ):
            raise ValueError(
                "ResearchAgent result must contain "
                "'destinations' as a list."
            )

        if len(destinations) != 3:
            raise ValueError(
                "ResearchAgent must return exactly 3 destinations."
            )

        return research_result

    # ==========================================================
    # DESTINATION NORMALIZATION
    # ==========================================================

    @staticmethod
    def _normalize_destination(
        destination: Any
    ) -> Dict[str, str]:

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
            name = str(
                destination.get(
                    "destination",
                    destination.get(
                        "name",
                        ""
                    )
                )
            ).strip()

            country = str(
                destination.get(
                    "country",
                    ""
                )
            ).strip()

        else:
            raise TypeError(
                "Each destination must be a string "
                "or dictionary."
            )

        if not name:
            raise ValueError(
                "ResearchAgent returned an empty destination."
            )

        return {
            "destination": name,
            "country": country
        }

    # ==========================================================
    # WORKER → RECHECK PIPELINE
    # ==========================================================

    def _run_worker_pipeline(
        self,
        worker,
        destination: str,
        country: str,
        trip_days: int,
        starting_location: Optional[str]
    ) -> Dict[str, Any]:
        """
        Run one complete:

            Worker
              |
              v
            Recheck
              |
          PASS | FAIL
              |
              v
        verified result

        The recheck happens immediately after the worker
        finishes.

        If recheck fails, the SAME worker researches the
        SAME destination again.
        """

        last_error = None

        for attempt in range(
            1,
            self.MAX_WORKER_RETRIES + 1
        ):

            try:

                # --------------------------------------------------
                # WORKER
                # --------------------------------------------------

                worker_result = worker.research(
                    destination=destination,
                    country=country,
                    trip_days=trip_days,
                    starting_location=starting_location
                )

                if not isinstance(
                    worker_result,
                    dict
                ):
                    raise TypeError(
                        "Worker returned an invalid result."
                    )

                # --------------------------------------------------
                # RECHECK
                # --------------------------------------------------

                check_result = (
                    self.recheck_agent.recheck(
                        worker_result
                    )
                )

                if not isinstance(
                    check_result,
                    dict
                ):
                    raise TypeError(
                        "RecheckAgent returned an invalid result."
                    )

                status = str(
                    check_result.get(
                        "status",
                        ""
                    )
                ).upper()

                # --------------------------------------------------
                # PASS
                # --------------------------------------------------

                if status == "PASS":

                    verified_result = (
                        check_result.get(
                            "result"
                        )
                    )

                    if not isinstance(
                        verified_result,
                        dict
                    ):
                        raise ValueError(
                            "RecheckAgent returned PASS "
                            "without a valid result."
                        )

                    # Keep destination identity controlled
                    # by main.py.
                    verified_result[
                        "destination"
                    ] = destination

                    verified_result[
                        "country"
                    ] = country

                    return verified_result

                # --------------------------------------------------
                # FAIL
                # --------------------------------------------------

                issues = check_result.get(
                    "issues",
                    []
                )

                last_error = RuntimeError(
                    "Recheck failed for "
                    f"{destination}. "
                    f"Issues: {issues}"
                )

            except Exception as exc:

                last_error = exc

        # ----------------------------------------------------------
        # ALL RETRIES FAILED
        # ----------------------------------------------------------

        raise RuntimeError(
            f"Worker pipeline failed for "
            f"{destination} after "
            f"{self.MAX_WORKER_RETRIES} attempts."
        ) from last_error

    # ==========================================================
    # RUN ALL THREE WORKER PIPELINES
    # ==========================================================

    def _run_verified_research(
        self,
        research_result: Dict[str, Any],
        trip_requirements: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Run the three Worker → Recheck chains concurrently.

        Important behavior:

            Worker 1 → Recheck 1
            Worker 2 → Recheck 2
            Worker 3 → Recheck 3

        These are independent pipelines.

        Therefore:

            Worker 1 finishing does NOT wait for
            Worker 2 or Worker 3 before Recheck 1 begins.
        """

        destinations = (
            research_result[
                "destinations"
            ]
        )

        normalized_destinations = [
            self._normalize_destination(
                destination
            )
            for destination in destinations
        ]

        # ----------------------------------------------------------
        # Trip information
        # ----------------------------------------------------------

        constraints = trip_requirements.get(
            "constraints",
            {}
        )

        if not isinstance(
            constraints,
            dict
        ):
            constraints = {}

        trip_days = constraints.get(
            "duration_days",
            7
        )

        try:
            trip_days = int(
                trip_days
            )
        except (
            TypeError,
            ValueError
        ):
            trip_days = 7

        starting_location = (
            constraints.get(
                "departure_location"
            )
        )

        # ----------------------------------------------------------
        # Assign exactly one worker to each destination.
        # ----------------------------------------------------------

        worker_assignments = [
            (
                self.worker1,
                normalized_destinations[0]
            ),
            (
                self.worker2,
                normalized_destinations[1]
            ),
            (
                self.worker3,
                normalized_destinations[2]
            )
        ]

        results = [None, None, None]

        # ----------------------------------------------------------
        # Run concurrently.
        # ----------------------------------------------------------

        with ThreadPoolExecutor(
            max_workers=3
        ) as executor:

            future_to_index = {}

            for index, (
                worker,
                destination_data
            ) in enumerate(
                worker_assignments
            ):

                future = executor.submit(
                    self._run_worker_pipeline,
                    worker,
                    destination_data[
                        "destination"
                    ],
                    destination_data[
                        "country"
                    ],
                    trip_days,
                    starting_location
                )

                future_to_index[
                    future
                ] = index

            # ------------------------------------------------------
            # Collect results as each pipeline finishes.
            # ------------------------------------------------------

            for future in as_completed(
                future_to_index
            ):

                index = future_to_index[
                    future
                ]

                results[index] = (
                    future.result()
                )

        # ----------------------------------------------------------
        # Safety validation.
        # ----------------------------------------------------------

        for index, result in enumerate(
            results
        ):

            if not isinstance(
                result,
                dict
            ):
                raise RuntimeError(
                    f"Worker pipeline {index + 1} "
                    "did not produce a valid result."
                )

        return results

    # ==========================================================
    # MAIN WORKFLOW
    # ==========================================================

    def run(
        self,
        user_input: str
    ) -> Dict[str, Any]:
        """
        Execute the complete backend workflow.

        Returns the final output generated by StructureAgent.
        """

        # ======================================================
        # 1. VALIDATE USER INPUT
        # ======================================================

        self._validate_user_input(
            user_input
        )

        # ======================================================
        # 2. MOOD AGENT
        # ======================================================

        trip_requirements = (
            self.mood_agent.interpret(
                user_input
            )
        )

        trip_requirements = (
            self._validate_trip_requirements(
                trip_requirements
            )
        )

        # ======================================================
        # 3. RESEARCH AGENT
        # ======================================================

        research_result = (
            self.research_agent.research(
                trip_requirements
            )
        )

        research_result = (
            self._validate_research_result(
                research_result
            )
        )

        # ======================================================
        # 4. VERIFIED WORKER RESEARCH
        # ======================================================

        verified_worker_results = (
            self._run_verified_research(
                research_result,
                trip_requirements
            )
        )

        # ======================================================
        # 5. TRAVEL AGENT
        # ======================================================

        # TravelAgent receives ONLY the destinations selected
        # by ResearchAgent.

        travel_result = (
            self.travel_agent.process(
                research_result
            )
        )

        if not isinstance(
            travel_result,
            dict
        ):
            raise TypeError(
                "TravelAgent must return a dictionary."
            )

        # ======================================================
        # 6. STRUCTURE AGENT
        # ======================================================

        # StructureAgent receives all information required
        # to construct the final backend structure.
        #
        # It does NOT need to communicate with the other
        # agents directly.

        structure_input = {
            "user_input": user_input,

            "trip_requirements": (
                trip_requirements
            ),

            "research_result": (
                research_result
            ),

            "verified_worker_results": (
                verified_worker_results
            ),

            "travel_result": (
                travel_result
            )
        }

        final_result = (
            self.structure_agent.process(
                structure_input
            )
        )

        if not isinstance(
            final_result,
            dict
        ):
            raise TypeError(
                "StructureAgent must return a dictionary."
            )

        # ======================================================
        # 7. RETURN FINAL BACKEND
        # ======================================================

        return final_result


# ==============================================================
# SIMPLE PUBLIC FUNCTION
# ==============================================================

_planner = None


def run_travel_planner(
    user_input: str
) -> Dict[str, Any]:
    """
    Public entry point for app.py / Flask / frontend.

    Example:

        result = run_travel_planner(
            "I want a peaceful mountain vacation..."
        )
    """

    global _planner

    if _planner is None:
        _planner = TravelPlanner()

    return _planner.run(
        user_input
    )


# ==============================================================
# COMMAND LINE TEST
# ==============================================================

if __name__ == "__main__":

    print("=" * 70)
    print("WANDERLUST AI TRAVEL PLANNER")
    print("=" * 70)

    user_input = input(
        "\nDescribe the trip you want:\n> "
    ).strip()

    try:

        result = run_travel_planner(
            user_input
        )

        print(
            "\n" + "=" * 70
        )

        print(
            "FINAL STRUCTURED BACKEND"
        )

        print(
            "=" * 70
        )

        print(
            json.dumps(
                result,
                indent=4,
                ensure_ascii=False
            )
        )

    except Exception as exc:

        print(
            "\nERROR:"
        )

        print(
            str(exc)
        )