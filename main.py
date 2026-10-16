"""
Wanderlust's central orchestration layer.

Architecture:
- No research workers.
- No separate RecheckAgent.
- Concurrent deep research for independent destinations.
- Per-destination validation and enrichment.
- Ordered final results.
"""

import time

from concurrent.futures import (
    ThreadPoolExecutor,
    as_completed
)

from ai.mood_agent import MoodAgent
from ai.travel_agent import TravelAgent
from ai.research_agent import ResearchAgent


class TravelPlanner:
    def __init__(self):
        self.mood_agent = MoodAgent()
        self.travel_agent = TravelAgent()
        self.research_agent = ResearchAgent()

        self.max_concurrent_destinations = 3

    # --------------------------------------------------
    # MAIN ENTRY POINT
    # --------------------------------------------------

    def run(
        self,
        user_input,
        trip_information=None
    ):
        total_started = time.perf_counter()

        if (
            not isinstance(user_input, str)
            or not user_input.strip()
        ):
            raise ValueError(
                "Please describe what you want from your trip."
            )

        trip_information = trip_information or {}

        performance = {}

        # ----------------------------------------------
        # 1. UNDERSTAND USER REQUIREMENTS
        # ----------------------------------------------

        stage_started = time.perf_counter()

        requirements = self.mood_agent.interpret(
            user_input,
            trip_information
        )

        performance["requirement_interpretation_seconds"] = (
            round(
                time.perf_counter() - stage_started,
                3
            )
        )

        # ----------------------------------------------
        # 2. SELECT DESTINATIONS
        # ----------------------------------------------

        stage_started = time.perf_counter()

        candidates = self.travel_agent.select_destinations(
            requirements,
            count=3
        )

        performance["destination_selection_seconds"] = (
            round(
                time.perf_counter() - stage_started,
                3
            )
        )

        if not candidates:
            raise ValueError(
                "No destinations were selected."
            )

        # Each destination has its own result slot.
        # This preserves the original selection order,
        # even when tasks complete out of order.
        results = [None] * len(candidates)

        verification = [None] * len(candidates)

        research_errors = {}

        deep_started = time.perf_counter()

        # ----------------------------------------------
        # 3. CONCURRENT DEEP RESEARCH
        # ----------------------------------------------

        worker_count = min(
            self.max_concurrent_destinations,
            len(candidates)
        )

        print(
            f"[TravelPlanner] Starting deep research "
            f"for {len(candidates)} destinations "
            f"with {worker_count} concurrent tasks."
        )

        with ThreadPoolExecutor(
            max_workers=worker_count,
            thread_name_prefix="destination-research"
        ) as executor:

            future_to_index = {
                executor.submit(
                    self.research_agent.research_destination,
                    candidate,
                    requirements,
                    0
                ): index
                for index, candidate in enumerate(candidates)
            }

            # ------------------------------------------
            # 4. PROCESS EACH DESTINATION AS IT FINISHES
            # ------------------------------------------

            for future in as_completed(future_to_index):
                index = future_to_index[future]

                candidate = candidates[index]

                destination_name = candidate["destination"]

                print(
                    f"[TravelPlanner] Deep research completed "
                    f"for {destination_name}."
                )

                try:
                    deep = future.result()

                except Exception as exc:
                    research_errors[index] = str(exc)

                    print(
                        f"[TravelPlanner] Deep research failed "
                        f"for {destination_name}: {exc}"
                    )

                    deep = self._empty_research(
                        candidate,
                        error=str(exc)
                    )

                # Process this destination immediately.
                # Other research futures continue running
                # in the background.
                try:
                    destination_result, check = (
                        self._process_completed_destination(
                            candidate=candidate,
                            requirements=requirements,
                            deep=deep,
                            initial_research_error=(
                                research_errors.get(index)
                            )
                        )
                    )

                except Exception as exc:
                    # A failure in one destination should not
                    # discard the other destinations.
                    print(
                        f"[TravelPlanner] Processing failed "
                        f"for {destination_name}: {exc}"
                    )

                    destination_result = (
                        self._minimal_destination_result(
                            candidate,
                            deep,
                            str(exc)
                        )
                    )

                    check = {
                        "destination": destination_name,
                        "country": candidate["country"],
                        "similar": None,
                        "reason": (
                            "Destination processing failed."
                        ),
                        "contradictions": [],
                        "retried": False,
                        "error": str(exc),
                    }

                results[index] = destination_result

                verification[index] = {
                    "destination": destination_name,
                    "country": candidate["country"],
                    **check,
                }

        performance["deep_research_and_processing_seconds"] = (
            round(
                time.perf_counter() - deep_started,
                3
            )
        )

        # ----------------------------------------------
        # 5. ENSURE ALL RESULT SLOTS ARE POPULATED
        # ----------------------------------------------

        final_destinations = []

        for index, result in enumerate(results):
            if result is None:
                result = self._minimal_destination_result(
                    candidates[index],
                    {},
                    "Destination processing did not produce a result."
                )

            final_destinations.append(result)

        final_verification = [
            item
            for item in verification
            if item is not None
        ]

        performance["total_seconds"] = round(
            time.perf_counter() - total_started,
            3
        )

        print(
            "[TravelPlanner] Trip planning completed "
            f"in {performance['total_seconds']:.2f}s."
        )

        # ----------------------------------------------
        # 6. RETURN FRONTEND-COMPATIBLE RESPONSE
        # ----------------------------------------------

        return {
            "trip_requirements": requirements,
            "destinations": final_destinations,
            "verification": final_verification,
            "performance": performance,
            "architecture": {
                "mood_model": "Groq GPT-OSS 20B",
                "destination_model": self.travel_agent.llm.model,
                "research_model": self.research_agent.llm.model,
                "workers_enabled": False,
                "recheck_agent_enabled": False,
                "concurrent_destination_research": True,
                "max_concurrent_destinations": worker_count,
                "pipeline_processing": True,
            },
        }

    # --------------------------------------------------
    # PROCESS ONE COMPLETED DESTINATION
    # --------------------------------------------------

    def _process_completed_destination(
        self,
        candidate,
        requirements,
        deep,
        initial_research_error=None
    ):
        """
        Finish one destination independently.

        Called as soon as its initial deep-research
        future completes.
        """

        destination = candidate["destination"]

        country = candidate["country"]

        timings = {}

        # ----------------------------------------------
        # A. INDEPENDENT BASIC INFORMATION
        # ----------------------------------------------

        basic_started = time.perf_counter()

        basic_error = None

        try:
            basic = self.travel_agent.get_basic_information(
                destination,
                country
            )

        except Exception as exc:
            basic_error = str(exc)

            print(
                f"[TravelPlanner] Independent basic "
                f"research failed for {destination}: {exc}"
            )

            basic = {
                "basic_info": "",
                "key_facts": [],
                "uncertainties": [
                    "Independent basic research failed."
                ],
                "sources": [],
                "search_query": "",
            }

        timings["basic_information_seconds"] = round(
            time.perf_counter() - basic_started,
            3
        )

        # ----------------------------------------------
        # B. CONSISTENCY CHECK
        # ----------------------------------------------

        comparison = {
            "similar": None,
            "reason": "Comparison was not completed.",
            "contradictions": [],
            "method": "not-run",
            "needs_review": True,
        }

        comparison_started = time.perf_counter()

        comparison_error = None

        if (
            deep.get("basic_info")
            and basic.get("basic_info")
        ):
            comparison = self.travel_agent.compare_information(
                destination,
                country,
                deep,
                basic
            )

        else:
            comparison_error = (
                "Insufficient information for comparison."
            )

        timings["comparison_seconds"] = round(
            time.perf_counter() - comparison_started,
            3
        )

        # ----------------------------------------------
        # C. CONDITIONAL RESEARCH RETRY
        # ----------------------------------------------

        retry_performed = False

        retry_reason = None

        retry_started = time.perf_counter()

        needs_retry = (
            not initial_research_error
            and (
                comparison.get("similar") is False
                or bool(
                    deep.get("research_warnings")
                )
            )
        )

        # If the independent source failed, do not
        # automatically launch a deep-research retry.
        if basic_error:
            needs_retry = False

        if needs_retry:
            retry_reason = (
                "Research evidence was insufficient or "
                "the summaries were inconsistent."
            )

            try:
                retry_result = (
                    self.research_agent.research_destination(
                        candidate,
                        requirements,
                        retry_number=1
                    )
                )

                retry_performed = True

                retry_comparison = {
                    "similar": None,
                    "reason": (
                        "Comparison could not be completed."
                    ),
                    "contradictions": [],
                    "method": "not-run",
                    "needs_review": True,
                }

                if (
                    retry_result.get("basic_info")
                    and basic.get("basic_info")
                ):
                    retry_comparison = (
                        self.travel_agent.compare_information(
                            destination,
                            country,
                            retry_result,
                            basic
                        )
                    )

                # Use the retry when it produced useful
                # evidence, even if comparison remains
                # inconclusive.
                if (
                    retry_result.get("basic_info")
                    or retry_result.get("source_urls")
                ):
                    deep = retry_result

                comparison = {
                    **retry_comparison,
                    "retried": True,
                    "retry_reason": retry_reason,
                    "first_comparison": comparison,
                }

            except Exception as exc:
                print(
                    f"[TravelPlanner] Research retry failed "
                    f"for {destination}: {exc}"
                )

                comparison = {
                    **comparison,
                    "retried": True,
                    "retry_reason": retry_reason,
                    "retry_error": str(exc),
                }

        else:
            comparison["retried"] = False

        timings["retry_seconds"] = round(
            time.perf_counter() - retry_started,
            3
        )

        # ----------------------------------------------
        # D. DESTINATION IMAGES AND MAP
        # ----------------------------------------------

        enrichment_started = time.perf_counter()

        enriched = self.travel_agent.enrich_destination(
            destination,
            country,
            basic
        )

        # ----------------------------------------------
        # E. ATTRACTION IMAGES
        # ----------------------------------------------

        attractions = deep.get(
            "major_attractions",
            []
        )

        if not isinstance(attractions, list):
            attractions = []

        enriched_attractions = (
            self.travel_agent.enrich_attractions(
                attractions,
                destination,
                country
            )
        )

        timings["enrichment_seconds"] = round(
            time.perf_counter() - enrichment_started,
            3
        )

        # ----------------------------------------------
        # F. BUILD FINAL DESTINATION
        # ----------------------------------------------

        destination_result = {
            "destination": destination,
            "name": destination,
            "country": country,
            "reason": candidate.get("reason", ""),

            "basic_info": basic.get(
                "basic_info",
                ""
            ),

            "key_facts": basic.get(
                "key_facts",
                []
            ),

            "images": enriched.get(
                "images",
                []
            ),

            "image_urls": enriched.get(
                "image_urls",
                []
            ),

            "map_coordinates": enriched.get(
                "map_coordinates"
            ),

            "map_url": enriched.get(
                "map_url"
            ),

            "research": deep,
            "research_result": deep,

            "major_attractions": enriched_attractions,

            "cost_estimates": deep.get(
                "cost_estimates",
                {}
            ),

            "best_time_to_visit": deep.get(
                "best_time_to_visit",
                ""
            ),

            "local_transport": deep.get(
                "local_transport",
                ""
            ),

            "practical_tips": deep.get(
                "practical_tips",
                []
            ),

            "safety_and_accessibility_notes": deep.get(
                "safety_and_accessibility_notes",
                []
            ),

            "fit_to_user_preferences": deep.get(
                "fit_to_user_preferences",
                ""
            ),

            "uncertainties": deep.get(
                "uncertainties",
                []
            ),

            "source_urls": deep.get(
                "source_urls",
                []
            ),

            "basic_info_sources": basic.get(
                "sources",
                []
            ),

            "consistency_check": comparison,

            "enrichment_warnings": (
                enriched.get(
                    "enrichment_warnings",
                    []
                )
            ),

            "processing_warnings": [
                warning
                for warning in [
                    initial_research_error,
                    basic_error,
                    comparison_error,
                ]
                if warning
            ],

            "performance": timings,
        }

        verification = {
            **comparison,
            "retried": retry_performed,
        }

        return destination_result, verification

    # --------------------------------------------------
    # FALLBACK RESEARCH DATA
    # --------------------------------------------------

    @staticmethod
    def _empty_research(
        candidate,
        error=None
    ):
        """
        Produce a stable research structure when deep
        research fails.

        This does not fabricate travel information.
        """

        warnings = []

        if error:
            warnings.append(
                f"Deep research failed: {error}"
            )

        return {
            "destination": candidate["destination"],
            "country": candidate["country"],
            "basic_info": "",
            "major_attractions": [],
            "cost_estimates": {},
            "best_time_to_visit": "",
            "local_transport": "",
            "practical_tips": [],
            "safety_and_accessibility_notes": [],
            "fit_to_user_preferences": "",
            "uncertainties": [
                "Deep research could not be completed."
            ],
            "source_urls": [],
            "search_queries": [],
            "research_attempt": 1,
            "research_warnings": warnings,
        }

    # --------------------------------------------------
    # MINIMAL RESULT FALLBACK
    # --------------------------------------------------

    @staticmethod
    def _minimal_destination_result(
        candidate,
        deep,
        error
    ):
        """
        Last-resort fallback so one failed destination
        does not discard the other results.
        """

        return {
            "destination": candidate["destination"],
            "name": candidate["destination"],
            "country": candidate["country"],
            "reason": candidate.get("reason", ""),

            "basic_info": "",
            "key_facts": [],

            "images": [],
            "image_urls": [],

            "map_coordinates": None,
            "map_url": None,

            "research": deep,
            "research_result": deep,

            "major_attractions": [],
            "cost_estimates": {},

            "best_time_to_visit": "",
            "local_transport": "",

            "practical_tips": [],
            "safety_and_accessibility_notes": [],

            "fit_to_user_preferences": "",
            "uncertainties": [
                "Destination processing did not complete."
            ],

            "source_urls": [],
            "basic_info_sources": [],

            "consistency_check": {
                "similar": None,
                "reason": (
                    "Destination processing failed."
                ),
                "contradictions": [],
                "retried": False,
            },

            "enrichment_warnings": [],
            "processing_warnings": [error],
        }

    # --------------------------------------------------
    # PUBLIC WRAPPER
    # --------------------------------------------------


def run_travel_planner(
    user_input,
    trip_information=None
):
    return TravelPlanner().run(
        user_input,
        trip_information
    )