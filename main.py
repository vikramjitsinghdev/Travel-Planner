import json
import os
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed

import database

from ai.mood_agent import MoodAgent
from ai.travel_agent import TravelAgent
from ai.research_agent import ResearchAgent

from travel.budget import Budget
from location.map import MapService

from random_destination import (
    get_random_destinations
)

from search_destination import (
    build_search_request,
    search_destinations
)

import pexels_service


# ==============================================================
# ACTIVE TRAVEL PLANNING SESSIONS
# ==============================================================

TRIPS = {}


# ==============================================================
# AI / SERVICES
# ==============================================================

mood_agent = None
travel_agent = None
research_agent = None
map_service = None


# ==============================================================
# CONFIGURATION
# ==============================================================

def _get_int_env(
    name,
    default
):

    try:
        return max(
            1,
            int(
                os.getenv(
                    name,
                    str(default)
                )
            )
        )

    except (
        TypeError,
        ValueError
    ):

        return default


# ==============================================================
# INITIALIZE SYSTEMS
# ==============================================================

def initialize_systems():

    global mood_agent
    global travel_agent
    global research_agent
    global map_service

    database.initialize_database()

    # ----------------------------------------------------------
    # MoodAgent
    # ----------------------------------------------------------

    if mood_agent is None:

        mood_agent = MoodAgent()

    # ----------------------------------------------------------
    # Main Gemini
    # ----------------------------------------------------------

    if travel_agent is None:

        travel_agent = TravelAgent()

    # ----------------------------------------------------------
    # Ollama Research System
    # ----------------------------------------------------------

    if research_agent is None:

        research_agent = ResearchAgent()

    # ----------------------------------------------------------
    # Map Service
    # ----------------------------------------------------------

    if map_service is None:

        map_service = MapService()


# ==============================================================
# JSON SAFETY
# ==============================================================

def make_json_safe(data):

    try:

        return json.loads(
            json.dumps(
                data,
                default=str
            )
        )

    except (
        TypeError,
        ValueError
    ):

        return str(data)


# ==============================================================
# NORMALIZE DATABASE TRIP
# ==============================================================

def normalize_trip_information(
    saved_trip
):

    if not isinstance(
        saved_trip,
        dict
    ):

        raise TypeError(
            "database.get_trip() must return a dictionary."
        )

    basic_information = saved_trip.get(
        "basic_information"
    )

    if isinstance(
        basic_information,
        dict
    ):

        normalized = dict(
            basic_information
        )

        for key, value in saved_trip.items():

            if key != "basic_information":

                normalized.setdefault(
                    key,
                    value
                )

        return normalized

    return dict(
        saved_trip
    )


# ==============================================================
# GET SAVED TRIP
# ==============================================================

def get_saved_trip(
    trip_id
):

    try:

        trip_id = int(
            trip_id
        )

    except (
        TypeError,
        ValueError
    ):

        raise ValueError(
            "trip_id must be a valid integer."
        )

    database.initialize_database()

    saved_trip = database.get_trip(
        trip_id
    )

    if saved_trip is None:

        raise ValueError(
            f"Trip {trip_id} was not found in the database."
        )

    return normalize_trip_information(
        saved_trip
    )


# ==============================================================
# HOME DESTINATIONS
# ==============================================================

def get_home_destinations(
    limit=5
):

    try:

        limit = int(
            limit
        )

    except (
        TypeError,
        ValueError
    ):

        limit = 5

    limit = max(
        1,
        min(
            limit,
            20
        )
    )

    database.initialize_database()

    destinations = database.get_home_destinations(
        limit
    )

    return make_json_safe(
        destinations
    )


# ==============================================================
# CREATE TRIP
# ==============================================================

def create_trip(
    basic_information
):

    if not isinstance(
        basic_information,
        dict
    ):

        raise TypeError(
            "basic_information must be a dictionary."
        )

    database.initialize_database()

    trip_id = database.create_trip(
        basic_information
    )

    if trip_id is None:

        raise RuntimeError(
            "Database did not return a trip ID."
        )

    return make_json_safe({

        "trip_id":
            trip_id,

        "basic_information":
            basic_information
    })


# ==============================================================
# GET TRIP
# ==============================================================

def get_trip(
    trip_id
):

    try:

        trip_id = int(
            trip_id
        )

    except (
        TypeError,
        ValueError
    ):

        raise ValueError(
            "trip_id must be a valid integer."
        )

    database.initialize_database()

    saved_trip = database.get_trip(
        trip_id
    )

    if saved_trip is None:

        return None

    return make_json_safe(
        normalize_trip_information(
            saved_trip
        )
    )


# ==============================================================
# ACTIVE SESSION
# ==============================================================

def get_active_trip(
    trip_id
):

    try:

        trip_id = int(
            trip_id
        )

    except (
        TypeError,
        ValueError
    ):

        raise ValueError(
            "trip_id must be a valid integer."
        )

    trip = TRIPS.get(
        trip_id
    )

    if trip is None:

        raise ValueError(
            "The AI planning session was not found. "
            "Please start the trip again."
        )

    return trip


# ==============================================================
# VALIDATE START REQUEST
# ==============================================================

def validate_start_request(
    trip_data
):

    if not isinstance(
        trip_data,
        dict
    ):

        raise TypeError(
            "trip_data must be a dictionary."
        )

    trip_id = trip_data.get(
        "trip_id"
    )

    if trip_id is None:

        raise ValueError(
            "Missing required field: trip_id"
        )

    user_input = trip_data.get(
        "user_input"
    )

    if not isinstance(
        user_input,
        str
    ):

        raise ValueError(
            "user_input must be a string."
        )

    user_input = user_input.strip()

    if not user_input:

        raise ValueError(
            "Please describe what you want from your trip."
        )

    try:

        trip_id = int(
            trip_id
        )

    except (
        TypeError,
        ValueError
    ):

        raise ValueError(
            "trip_id must be a valid integer."
        )

    return (
        trip_id,
        user_input
    )


# ==============================================================
# EXTRACT CANDIDATES
# ==============================================================

def extract_candidates(
    candidate_result
):

    candidates = []

    if not isinstance(
        candidate_result,
        dict
    ):

        return candidates

    raw_candidates = candidate_result.get(
        "candidates",
        []
    )

    if not isinstance(
        raw_candidates,
        list
    ):

        return candidates

    for candidate in raw_candidates:

        if isinstance(
            candidate,
            dict
        ):

            name = candidate.get(
                "name"
            )

            if not name:

                continue

            candidates.append({

                "name":
                    str(
                        name
                    ).strip(),

                "country":
                    (
                        str(
                            candidate.get(
                                "country"
                            )
                        ).strip()
                        if candidate.get(
                            "country"
                        )
                        else None
                    ),

                "description":
                    candidate.get(
                        "description"
                    ),

                "reason":
                    candidate.get(
                        "reason"
                    ),

                "research_priority":
                    candidate.get(
                        "research_priority"
                    )
            })

        elif isinstance(
            candidate,
            str
        ):

            candidate = candidate.strip()

            if candidate:

                candidates.append({

                    "name":
                        candidate,

                    "country":
                        None,

                    "description":
                        None,

                    "reason":
                        None,

                    "research_priority":
                        None
                })

    return candidates


# ==============================================================
# CREATE TRIP STATE
# ==============================================================

def create_trip_state(
    trip_id,
    session_id,
    trip_information,
    budget
):

    return {

        "trip_id":
            trip_id,

        "session_id":
            session_id,

        "status":
            "planning",

        "original_user_input":
            "",

        "trip_information":
            trip_information,

        # ------------------------------------------------------
        # MOOD AGENT
        # ------------------------------------------------------

        "trip_requirements":
            {},

        "preferences":
            {},

        # ------------------------------------------------------
        # MAIN GEMINI
        # ------------------------------------------------------

        "candidate_result":
            {},

        "candidates":
            [],

        "candidate_names":
            [],

        "research_plan":
            {},

        # ------------------------------------------------------
        # OLLAMA RESEARCH
        # ------------------------------------------------------

        "research":
            {},

        # ------------------------------------------------------
        # EVALUATOR
        # ------------------------------------------------------

        "evaluation":
            {},

        "ranked_candidates":
            [],

        # ------------------------------------------------------
        # FINAL GEMINI
        # ------------------------------------------------------

        "travel_options":
            [],

        # ------------------------------------------------------
        # USER SELECTION
        # ------------------------------------------------------

        "selected_destination":
            None,

        "selected_trip":
            None,

        # ------------------------------------------------------
        # MAP
        # ------------------------------------------------------

        "map_data":
            [],

        # ------------------------------------------------------
        # BUDGET
        # ------------------------------------------------------

        "budget":
            budget
    }


# ==============================================================
# STEP 2
# MOOD AGENT
# ==============================================================

def extract_trip_requirements(
    user_input,
    trip_information
):

    initialize_systems()

    trip_requirements = mood_agent.interpret(

        user_input=
            user_input,

        trip_information=
            trip_information
    )

    if not isinstance(
        trip_requirements,
        dict
    ):

        raise ValueError(
            "MoodAgent returned an invalid "
            "TripRequirements object."
        )

    return trip_requirements


# ==============================================================
# STEP 3
# MAIN GEMINI — CANDIDATES
# ==============================================================

def generate_candidates(
    user_input,
    trip_requirements,
    trip_information,
    budget
):

    initialize_systems()

    budget_state = budget.get_status()

    candidate_result = travel_agent.find_candidates(

        user_input=
            user_input,

        preferences=
            trip_requirements,

        budget=
            budget_state,

        trip_information=
            trip_information
    )

    candidates = extract_candidates(
        candidate_result
    )

    if len(candidates) != 5:

        raise ValueError(
            "TravelAgent must return exactly five candidates."
        )

    return (
        candidate_result,
        candidates
    )


# ==============================================================
# DESTINATION DISPLAY NAMES
# ==============================================================

def destination_names(
    candidates
):

    names = []

    if not isinstance(
        candidates,
        list
    ):

        return names

    for candidate in candidates:

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

        if not name:

            continue

        if country:

            names.append(
                f"{name}, {country}"
            )

        else:

            names.append(
                str(name)
            )

    return names


# ==============================================================
# BUILD RESEARCH RESULT CONTAINER
# ==============================================================

def create_research_result_container():

    return {

        "worker_1":
            {},

        "worker_2":
            {},

        "worker_3":
            {},

        "errors":
            []
    }


# ==============================================================
# GET RESEARCH QUESTIONS
# ==============================================================

def get_research_questions(
    research_plan,
    worker_name,
    destination
):

    if not isinstance(
        research_plan,
        dict
    ):

        return []

    questions_map = research_plan.get(
        f"{worker_name}_questions",
        {}
    )

    if not isinstance(
        questions_map,
        dict
    ):

        return []

    questions = questions_map.get(
        destination,
        []
    )

    if not isinstance(
        questions,
        list
    ):

        return []

    return questions


# ==============================================================
# STEP 4
# OLLAMA RESEARCH — ONE DESTINATION
# ==============================================================

def research_one_destination(
    candidate,
    trip_requirements,
    research_plan
):

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

        raise ValueError(
            "Candidate has no destination name."
        )

    # ----------------------------------------------------------
    # Get the questions generated by Main Gemini.
    # ----------------------------------------------------------

    worker1_questions = get_research_questions(
        research_plan,
        "worker_1",
        destination
    )

    worker2_questions = get_research_questions(
        research_plan,
        "worker_2",
        destination
    )

    worker3_questions = get_research_questions(
        research_plan,
        "worker_3",
        destination
    )

    # ----------------------------------------------------------
    # ResearchAgent runs its three Ollama workers in parallel.
    # ----------------------------------------------------------

    result = research_agent.research_all_workers(

        destination=
            destination,

        country=
            country,

        trip_requirements=
            trip_requirements,

        research_plan={
            "worker_1_questions": {
                destination:
                    worker1_questions
            },

            "worker_2_questions": {
                destination:
                    worker2_questions
            },

            "worker_3_questions": {
                destination:
                    worker3_questions
            }
        }
    )

    if not isinstance(
        result,
        dict
    ):

        raise ValueError(
            f"ResearchAgent returned invalid data "
            f"for {destination}."
        )

    return (
        destination,
        result
    )


# ==============================================================
# STEP 4
# OLLAMA RESEARCH — ALL FIVE DESTINATIONS
# ==============================================================

def run_research_pipeline(
    candidates,
    trip_requirements,
    research_plan
):

    initialize_systems()

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

    results = create_research_result_container()

    # ----------------------------------------------------------
    # Five destination jobs run concurrently.
    #
    # Each ResearchAgent job then launches:
    #
    # Worker 1
    # Worker 2
    # Worker 3
    #
    # concurrently.
    #
    # Therefore the intended structure is:
    #
    #       5 destinations
    #             |
    #       +-----+-----+
    #       |     |     |
    #      W1    W2    W3
    #
    # up to 15 Ollama calls.
    # ----------------------------------------------------------

    max_destination_jobs = _get_int_env(
        "OLLAMA_DESTINATION_CONCURRENCY",
        5
    )

    max_destination_jobs = min(
        max_destination_jobs,
        len(candidates)
    )

    with ThreadPoolExecutor(
        max_workers=max_destination_jobs
    ) as executor:

        future_map = {

            executor.submit(
                research_one_destination,
                candidate,
                trip_requirements,
                research_plan
            ):
                candidate

            for candidate in candidates
        }

        for future in as_completed(
            future_map
        ):

            candidate = future_map[
                future
            ]

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

            try:

                (
                    destination,
                    destination_result
                ) = future.result()

                # --------------------------------------------------
                # ResearchAgent returns:
                #
                # {
                #   "worker_1": {...},
                #   "worker_2": {...},
                #   "worker_3": {...}
                # }
                #
                # Convert it into the structure expected by
                # TravelAgent's evaluator.
                # --------------------------------------------------

                for worker_name in (
                    "worker_1",
                    "worker_2",
                    "worker_3"
                ):

                    worker_result = (
                        destination_result.get(
                            worker_name
                        )
                    )

                    if worker_result is None:

                        results[
                            worker_name
                        ][
                            destination
                        ] = {

                            "destination":
                                destination,

                            "country":
                                country,

                            "success":
                                False,

                            "error":
                                (
                                    "ResearchAgent did not "
                                    f"return {worker_name}."
                                )
                        }

                    else:

                        results[
                            worker_name
                        ][
                            destination
                        ] = worker_result

                        # ------------------------------------------------
                        # Detect worker-level failures.
                        # ------------------------------------------------

                        if (
                            isinstance(
                                worker_result,
                                dict
                            )
                            and
                            worker_result.get(
                                "success"
                            ) is False
                        ):

                            results[
                                "errors"
                            ].append({

                                "worker":
                                    worker_name,

                                "destination":
                                    destination,

                                "error":
                                    worker_result.get(
                                        "error",
                                        "Worker failed."
                                    )
                            })

            except Exception as error:

                error_record = {

                    "destination":
                        destination,

                    "country":
                        country,

                    "error":
                        str(error)
                }

                results[
                    "errors"
                ].append(
                    error_record
                )

                # --------------------------------------------------
                # Preserve a result for every worker so the
                # evaluator can still process the candidate.
                # --------------------------------------------------

                for worker_name in (
                    "worker_1",
                    "worker_2",
                    "worker_3"
                ):

                    results[
                        worker_name
                    ][
                        destination
                    ] = {

                        "destination":
                            destination,

                        "country":
                            country,

                        "success":
                            False,

                        "error":
                            str(error)
                    }

    return results


# ==============================================================
# STEP 5
# EVALUATION
# ==============================================================

def evaluate_research(
    candidates,
    trip_requirements,
    research_results
):

    initialize_systems()

    evaluation = travel_agent.evaluate_candidates(

        candidates=
            candidates,

        trip_requirements=
            trip_requirements,

        research_results=
            research_results
    )

    if not isinstance(
        evaluation,
        dict
    ):

        raise ValueError(
            "TravelAgent evaluator returned invalid data."
        )

    return evaluation


# ==============================================================
# STEP 6
# FINAL GEMINI SELECTION
# ==============================================================

def select_final_trips(
    user_input,
    trip_requirements,
    research_results,
    evaluation_results,
    trip_information,
    budget
):

    initialize_systems()

    final_result = travel_agent.select_best_trips(

        user_input=
            user_input,

        trip_requirements=
            trip_requirements,

        research_results=
            research_results,

        evaluation_results=
            evaluation_results,

        trip_information=
            trip_information,

        budget=
            budget.get_status()
    )

    if not isinstance(
        final_result,
        dict
    ):

        raise ValueError(
            "TravelAgent final selection returned invalid data."
        )

    selected = final_result.get(
        "selected_trips",
        []
    )

    if len(selected) != 3:

        raise ValueError(
            "Main Gemini must return exactly three "
            "final trip options."
        )

    return selected


# ==============================================================
# COMPLETE AI PIPELINE
# ==============================================================

def run_travel_orchestration(
    user_input,
    trip_requirements,
    trip_information,
    budget
):
    """
    COMPLETE NEW ARCHITECTURE.

        USER
          |
          v
      MoodAgent
          |
          v
    TripRequirements
          |
          v
      Main Gemini
          |
          v
      5 candidates
          |
          v
      Main Gemini
          |
          v
      Research Plan
          |
          v
    +---------------------+
    |   Ollama Research   |
    |                     |
    | Worker 1            |
    | Worker 2            |
    | Worker 3            |
    +---------------------+
          |
          v
      Evaluator
          |
          v
      Main Gemini
          |
          v
       Best 3
    """

    initialize_systems()

    # ==========================================================
    # STEP 3 — CANDIDATES
    # ==========================================================

    (
        candidate_result,
        candidates
    ) = generate_candidates(

        user_input=
            user_input,

        trip_requirements=
            trip_requirements,

        trip_information=
            trip_information,

        budget=
            budget
    )

    # ==========================================================
    # STEP 3B — RESEARCH PLAN
    # ==========================================================

    research_plan = (
        travel_agent.create_research_plan(

            user_input=
                user_input,

            trip_requirements=
                trip_requirements,

            candidates=
                candidates,

            trip_information=
                trip_information
        )
    )

    if not isinstance(
        research_plan,
        dict
    ):

        raise ValueError(
            "TravelAgent returned an invalid research plan."
        )

    # ==========================================================
    # STEP 4 — OLLAMA RESEARCH
    # ==========================================================

    research_results = run_research_pipeline(

        candidates=
            candidates,

        trip_requirements=
            trip_requirements,

        research_plan=
            research_plan
    )
    errors = research_results.get(
        "errors",
        []
    )

    successful_workers = 15 - len(errors)

    if successful_workers == 0:

        raise RuntimeError(
            "All research workers failed. "
            "No valid research data is available "
            "for final destination selection."
        )

    # ==========================================================
    # STEP 5 — EVALUATOR
    # ==========================================================

    evaluation_results = evaluate_research(

        candidates=
            candidates,

        trip_requirements=
            trip_requirements,

        research_results=
            research_results
    )

    # ==========================================================
    # STEP 6 — MAIN GEMINI
    # ==========================================================

    travel_options = select_final_trips(

        user_input=
            user_input,

        trip_requirements=
            trip_requirements,

        research_results=
            research_results,

        evaluation_results=
            evaluation_results,

        trip_information=
            trip_information,

        budget=
            budget
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
            travel_options
    }


# ==============================================================
# START TRIP
# ==============================================================

def start_trip(
    trip_data
):

    initialize_systems()

    # ==========================================================
    # STEP 1 — USER
    # ==========================================================

    (
        trip_id,
        user_input
    ) = validate_start_request(
        trip_data
    )

    # ==========================================================
    # LOAD SAVED TRIP
    # ==========================================================

    trip_information = get_saved_trip(
        trip_id
    )

    # ==========================================================
    # BUDGET
    # ==========================================================

    budget_value = trip_information.get(
        "budget"
    )

    if budget_value is None:

        budget_value = trip_information.get(
            "total_budget"
        )

    if budget_value is None:

        raise ValueError(
            "The saved trip does not contain a travel budget."
        )

    currency = trip_information.get(
        "currency",
        "CAD"
    )

    try:

        budget_value = float(
            budget_value
        )

    except (
        TypeError,
        ValueError
    ):

        raise ValueError(
            "The travel budget must be a valid number."
        )

    budget = Budget(

        total_budget=
            budget_value,

        currency=
            currency
    )

    # ==========================================================
    # CREATE SESSION
    # ==========================================================

    session_id = str(
        uuid.uuid4()
    )

    trip = create_trip_state(

        trip_id=
            trip_id,

        session_id=
            session_id,

        trip_information=
            trip_information,

        budget=
            budget
    )

    trip[
        "original_user_input"
    ] = user_input

    TRIPS[
        trip_id
    ] = trip

    # ==========================================================
    # STEP 2 — MOOD AGENT
    # ==========================================================

    trip_requirements = (
        extract_trip_requirements(

            user_input=
                user_input,

            trip_information=
                trip_information
        )
    )

    trip[
        "trip_requirements"
    ] = trip_requirements

    # Keep compatibility with existing frontend.
    trip[
        "preferences"
    ] = trip_requirements

    # ==========================================================
    # STEP 3 → STEP 6
    # COMPLETE PIPELINE
    # ==========================================================

    orchestration = run_travel_orchestration(

        user_input=
            user_input,

        trip_requirements=
            trip_requirements,

        trip_information=
            trip_information,

        budget=
            budget
    )

    # ==========================================================
    # SAVE PIPELINE STATE
    # ==========================================================

    trip[
        "candidate_result"
    ] = orchestration.get(
        "candidate_result",
        {}
    )

    trip[
        "candidates"
    ] = orchestration.get(
        "candidates",
        []
    )

    trip[
        "candidate_names"
    ] = destination_names(
        trip["candidates"]
    )

    trip[
        "research_plan"
    ] = orchestration.get(
        "research_plan",
        {}
    )

    trip[
        "research"
    ] = orchestration.get(
        "research",
        {}
    )

    trip[
        "evaluation"
    ] = orchestration.get(
        "evaluation",
        {}
    )

    trip[
        "ranked_candidates"
    ] = orchestration.get(
        "ranked_candidates",
        []
    )

    trip[
        "travel_options"
    ] = orchestration.get(
        "travel_options",
        []
    )

    trip[
        "status"
    ] = "awaiting_selection"

    return get_trip_status({

        "trip_id":
            trip_id
    })


# ==============================================================
# TRIP STATUS
# ==============================================================

def get_trip_status(
    trip_data
):

    if not isinstance(
        trip_data,
        dict
    ):

        raise TypeError(
            "trip_data must be a dictionary."
        )

    trip_id = trip_data.get(
        "trip_id"
    )

    if trip_id is None:

        raise ValueError(
            "trip_id is required."
        )

    trip = get_active_trip(
        trip_id
    )

    budget = trip[
        "budget"
    ]

    result = {

        "trip_id":
            trip["trip_id"],

        "session_id":
            trip["session_id"],

        "status":
            trip["status"],

        "original_user_input":
            trip["original_user_input"],

        "trip_information":
            trip["trip_information"],

        # ------------------------------------------------------
        # STEP 2
        # ------------------------------------------------------

        "trip_requirements":
            trip["trip_requirements"],

        "preferences":
            trip["preferences"],

        # ------------------------------------------------------
        # STEP 3
        # ------------------------------------------------------

        "candidate_result":
            trip["candidate_result"],

        "candidates":
            trip["candidates"],

        "candidate_names":
            trip.get(
                "candidate_names",
                []
            ),

        "research_plan":
            trip.get(
                "research_plan",
                {}
            ),

        # ------------------------------------------------------
        # STEP 4
        # ------------------------------------------------------

        "research":
            trip["research"],

        # ------------------------------------------------------
        # STEP 5
        # ------------------------------------------------------

        "evaluation":
            trip["evaluation"],

        "ranked_candidates":
            trip["ranked_candidates"],

        # ------------------------------------------------------
        # STEP 6
        # ------------------------------------------------------

        "travel_options":
            trip["travel_options"],

        # ------------------------------------------------------
        # SELECTION
        # ------------------------------------------------------

        "selected_destination":
            trip["selected_destination"],

        "selected_trip":
            trip["selected_trip"],

        # ------------------------------------------------------
        # MAP
        # ------------------------------------------------------

        "map_data":
            trip["map_data"],

        # ------------------------------------------------------
        # BUDGET
        # ------------------------------------------------------

        "budget":
            budget.get_status()
    }

    return make_json_safe(
        result
    )


# ==============================================================
# UPDATE TRIP
# ==============================================================

def update_trip(
    trip_data
):

    initialize_systems()

    if not isinstance(
        trip_data,
        dict
    ):

        raise TypeError(
            "trip_data must be a dictionary."
        )

    trip_id = trip_data.get(
        "trip_id"
    )

    change_request = trip_data.get(
        "change_request"
    )

    if trip_id is None:

        raise ValueError(
            "trip_id is required."
        )

    if not isinstance(
        change_request,
        str
    ) or not change_request.strip():

        raise ValueError(
            "change_request is required."
        )

    trip = get_active_trip(
        trip_id
    )

    original_request = trip[
        "original_user_input"
    ]

    updated_request = (
        f"{original_request}\n\n"
        f"USER REQUESTED CHANGE:\n"
        f"{change_request.strip()}"
    )

    trip_information = dict(
        trip[
            "trip_information"
        ]
    )

    budget = trip[
        "budget"
    ]

    # ==========================================================
    # MOOD AGENT
    # ==========================================================

    trip_requirements = (
        extract_trip_requirements(

            user_input=
                updated_request,

            trip_information=
                trip_information
        )
    )

    # ==========================================================
    # COMPLETE RE-RUN
    # ==========================================================

    orchestration = run_travel_orchestration(

        user_input=
            updated_request,

        trip_requirements=
            trip_requirements,

        trip_information=
            trip_information,

        budget=
            budget
    )

    # ==========================================================
    # UPDATE STATE
    # ==========================================================

    trip[
        "original_user_input"
    ] = updated_request

    trip[
        "trip_requirements"
    ] = trip_requirements

    trip[
        "preferences"
    ] = trip_requirements

    trip[
        "candidate_result"
    ] = orchestration.get(
        "candidate_result",
        {}
    )

    trip[
        "candidates"
    ] = orchestration.get(
        "candidates",
        []
    )

    trip[
        "candidate_names"
    ] = destination_names(
        trip["candidates"]
    )

    trip[
        "research_plan"
    ] = orchestration.get(
        "research_plan",
        {}
    )

    trip[
        "research"
    ] = orchestration.get(
        "research",
        {}
    )

    trip[
        "evaluation"
    ] = orchestration.get(
        "evaluation",
        {}
    )

    trip[
        "ranked_candidates"
    ] = orchestration.get(
        "ranked_candidates",
        []
    )

    trip[
        "travel_options"
    ] = orchestration.get(
        "travel_options",
        []
    )

    # Clear previous selection.

    trip[
        "selected_destination"
    ] = None

    trip[
        "selected_trip"
    ] = None

    trip[
        "map_data"
    ] = []

    trip[
        "status"
    ] = "awaiting_selection"

    return get_trip_status({

        "trip_id":
            trip_id
    })


# ==============================================================
# MAP DATA FOR SELECTED DESTINATION
# ==============================================================

def get_selected_destination_map_data(
    destination,
    country=""
):

    initialize_systems()

    if not destination:

        return []

    query = str(
        destination
    ).strip()

    if country:

        query = (
            f"{query}, "
            f"{str(country).strip()}"
        )

    try:

        result = map_service.get_destination_info(
            query
        )

        if isinstance(
            result,
            dict
        ) and result.get(
            "found",
            False
        ):

            return [
                result
            ]

    except Exception as error:

        print(
            "[MapService] Failed to retrieve "
            f"map data: {error}"
        )

    return []


# ==============================================================
# SELECT FINAL TRIP
# ==============================================================

def select_trip(
    trip_data
):

    initialize_systems()

    if not isinstance(
        trip_data,
        dict
    ):

        raise TypeError(
            "trip_data must be a dictionary."
        )

    trip_id = trip_data.get(
        "trip_id"
    )

    selected_index = trip_data.get(
        "selected_index"
    )

    selected_destination = trip_data.get(
        "destination"
    )

    trip = get_active_trip(
        trip_id
    )

    travel_options = trip.get(
        "travel_options",
        []
    )

    if not travel_options:

        raise ValueError(
            "No final trip options are available."
        )

    # ==========================================================
    # SELECT BY INDEX
    # ==========================================================

    if selected_index is not None:

        try:

            selected_index = int(
                selected_index
            )

        except (
            TypeError,
            ValueError
        ):

            raise ValueError(
                "selected_index must be a number."
            )

        if (
            selected_index < 0
            or
            selected_index >= len(
                travel_options
            )
        ):

            raise ValueError(
                "Selected trip does not exist."
            )

        selected_option = travel_options[
            selected_index
        ]

        selected_destination = (
            selected_option.get(
                "destination"
            )
        )

    # ==========================================================
    # SELECT BY DESTINATION
    # ==========================================================

    else:

        selected_option = None

        for option in travel_options:

            if not isinstance(
                option,
                dict
            ):

                continue

            option_destination = str(
                option.get(
                    "destination",
                    ""
                )
            ).strip().lower()

            requested_destination = str(
                selected_destination or ""
            ).strip().lower()

            if (
                option_destination
                ==
                requested_destination
            ):

                selected_option = option

                break

        if selected_option is None:

            raise ValueError(
                "Selected destination is not one of the "
                "final trip options."
            )

    if not selected_destination:

        raise ValueError(
            "A destination or selected_index is required."
        )

    # ==========================================================
    # FIND COUNTRY
    # ==========================================================

    selected_country = ""

    for option in travel_options:

        if not isinstance(
            option,
            dict
        ):

            continue

        if str(
            option.get(
                "destination",
                ""
            )
        ).strip().lower() == str(
            selected_destination
        ).strip().lower():

            selected_country = str(
                option.get(
                    "country",
                    ""
                )
            ).strip()

            break

    # ==========================================================
    # MAP SERVICE
    # ==========================================================

    map_data = get_selected_destination_map_data(

        destination=
            selected_destination,

        country=
            selected_country
    )

    trip[
        "map_data"
    ] = map_data

    # ==========================================================
    # BUILD DETAILED TRIP
    # ==========================================================

    detailed_trip = travel_agent.build_selected_trip(

        selected_destination=
            selected_destination,

        user_input=
            trip[
                "original_user_input"
            ],

        preferences=
            trip[
                "trip_requirements"
            ],

        budget=
            trip[
                "budget"
            ].get_status(),

        research=
            trip[
                "research"
            ],

        map_data=
            map_data,

        trip_information=
            trip[
                "trip_information"
            ]
    )

    if not isinstance(
        detailed_trip,
        dict
    ):

        raise ValueError(
            "TravelAgent returned invalid selected-trip data."
        )

    # ==========================================================
    # SAVE
    # ==========================================================

    trip[
        "selected_destination"
    ] = selected_destination

    trip[
        "selected_trip"
    ] = detailed_trip

    trip[
        "status"
    ] = "awaiting_confirmation"

    return get_trip_status({

        "trip_id":
            trip_id
    })


# ==============================================================
# CONFIRM TRIP
# ==============================================================

def confirm_trip(
    trip_data
):

    if not isinstance(
        trip_data,
        dict
    ):

        raise TypeError(
            "trip_data must be a dictionary."
        )

    trip_id = trip_data.get(
        "trip_id"
    )

    trip = get_active_trip(
        trip_id
    )

    if trip.get(
        "selected_trip"
    ) is None:

        raise ValueError(
            "No trip has been selected."
        )

    budget = trip[
        "budget"
    ]

    budget.confirm_estimates()

    trip[
        "status"
    ] = "confirmed"

    return get_trip_status({

        "trip_id":
            trip_id
    })


# ==============================================================
# CANCEL TRIP
# ==============================================================

def cancel_trip(
    trip_data
):

    if not isinstance(
        trip_data,
        dict
    ):

        raise TypeError(
            "trip_data must be a dictionary."
        )

    trip_id = trip_data.get(
        "trip_id"
    )

    trip = get_active_trip(
        trip_id
    )

    trip[
        "budget"
    ].clear_estimates()

    trip[
        "status"
    ] = "cancelled"

    return get_trip_status({

        "trip_id":
            trip_id
    })


# ==============================================================
# DELETE TRIP
# ==============================================================

def delete_trip(
    trip_data
):

    if not isinstance(
        trip_data,
        dict
    ):

        raise TypeError(
            "trip_data must be a dictionary."
        )

    trip_id = trip_data.get(
        "trip_id"
    )

    if trip_id is None:

        raise ValueError(
            "trip_id is required."
        )

    try:

        trip_id = int(
            trip_id
        )

    except (
        TypeError,
        ValueError
    ):

        raise ValueError(
            "trip_id must be a valid integer."
        )

    if trip_id not in TRIPS:

        raise ValueError(
            "Trip was not found."
        )

    del TRIPS[
        trip_id
    ]

    return {

        "trip_id":
            trip_id,

        "status":
            "deleted"
    }


# ==============================================================
# RANDOM DESTINATIONS
# ==============================================================

def get_random_destinations_for_trip(
    trip_data=None
):

    if trip_data is None:

        trip_data = {}

    if not isinstance(
        trip_data,
        dict
    ):

        raise TypeError(
            "trip_data must be a dictionary."
        )

    database.initialize_database()

    count = trip_data.get(
        "count",
        6
    )

    scope = trip_data.get(
        "scope"
    )

    country = trip_data.get(
        "country"
    )

    region = trip_data.get(
        "region"
    )

    try:

        count = int(
            count
        )

    except (
        TypeError,
        ValueError
    ):

        count = 6

    count = max(
        1,
        min(
            count,
            20
        )
    )

    database_results = (
        database.get_random_destinations(
            limit=count
        )
    )

    random_result = (
        get_random_destinations(

            count=
                count,

            scope=
                scope,

            country=
                country,

            region=
                region,

            destinations=
                database_results
        )
    )

    destinations = random_result.get(
        "destinations",
        []
    )

    return make_json_safe({

        "request":
            random_result.get(
                "request"
            ),

        "destinations":
            destinations
    })


# ==============================================================
# LIVE DESTINATION SEARCH
# ==============================================================

def search_destination(
    query
):

    initialize_systems()

    search_request = build_search_request(
        query
    )

    query = search_request[
        "query"
    ]

    database_results = (
        database.search_destinations(
            query
        )
    )

    # ----------------------------------------------------------
    # DATABASE RESULT
    # ----------------------------------------------------------

    if database_results:

        destination = dict(
            database_results[0]
        )

        if not destination.get(
            "image_url"
        ):

            image = (
                pexels_service.get_destination_image(

                    destination.get(
                        "name"
                    ),

                    destination.get(
                        "country"
                    )
                )
            )

            destination[
                "image_url"
            ] = image.get(
                "image_url"
            )

            destination[
                "pexels_url"
            ] = image.get(
                "pexels_url"
            )

            destination[
                "photo_credit"
            ] = image.get(
                "photographer"
            )

        return search_destinations(

            query=
                query,

            database_results=
                [destination]
        )

    # ----------------------------------------------------------
    # MAPTILER FALLBACK
    # ----------------------------------------------------------

    live_result = (
        map_service.get_destination_info(
            query
        )
    )

    if not live_result.get(
        "found",
        False
    ):

        return search_destinations(

            query=
                query,

            database_results=
                [],

            live_result=
                None
        )

    # ----------------------------------------------------------
    # PEXELS
    # ----------------------------------------------------------

    image = (
        pexels_service.get_destination_image(

            live_result.get(
                "name"
            ),

            live_result.get(
                "country"
            )
        )
    )

    # ----------------------------------------------------------
    # FINAL SEARCH RESULT
    # ----------------------------------------------------------

    return search_destinations(

        query=
            query,

        database_results=
            [],

        live_result=
            live_result,

        image=
            image
    )


# ==============================================================
# CLI
# ==============================================================

def main():

    print("=" * 60)
    print("AI TRAVEL PLANNER BACKEND")
    print("=" * 60)

    print(
        "\nStart the web application with:"
    )

    print(
        "\n    python app.py"
    )


if __name__ == "__main__":

    main()