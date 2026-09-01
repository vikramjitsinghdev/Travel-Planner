import json
import uuid
from concurrent.futures import ThreadPoolExecutor
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
# AI / MAP SYSTEMS
# ==============================================================

mood_agent = None
travel_agent = None
research_agent = None
map_service = None


# ==============================================================
# INITIALIZE SYSTEMS
# ==============================================================

def initialize_systems():
    """
    Initialize the Wanderlust backend.

    main.py is responsible for initializing the database
    and backend services.

    app.py does not communicate directly with database.py.
    """

    global mood_agent
    global travel_agent
    global research_agent
    global map_service

    # ----------------------------------------------------------
    # DATABASE
    # ----------------------------------------------------------

    database.initialize_database()

    # ----------------------------------------------------------
    # AI / MAP SERVICES
    # ----------------------------------------------------------

    if mood_agent is None:
        mood_agent = MoodAgent()

    if travel_agent is None:
        travel_agent = TravelAgent()

    if research_agent is None:
        research_agent = ResearchAgent()

    if map_service is None:
        map_service = MapService()

# ==============================================================
# JSON SAFETY
# ==============================================================

def make_json_safe(data):
    """
    Convert backend data into JSON-safe data.
    """

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

def normalize_trip_information(saved_trip):
    """
    Normalize the structure returned by database.py.
    """

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
# GET SQLITE TRIP
# ==============================================================

def get_saved_trip(trip_id):
    """
    Retrieve a trip from SQLite and normalize it.
    """

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
    """
    Retrieve preloaded destinations for the homepage.

    main.py controls the database interaction.
    """

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

    destinations = (
        database.get_home_destinations(
            limit
        )
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
    """
    Create a new trip in SQLite.

    Architecture:

        app.py
            ↓
        main.py
            ↓
        database.py
            ↓
        SQLite
    """

    if not isinstance(
        basic_information,
        dict
    ):

        raise TypeError(
            "basic_information must be a dictionary."
        )

    # Make sure the database exists.
    database.initialize_database()

    # Save the trip.
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
    """
    Retrieve basic trip information from SQLite.
    """

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
# FIND ACTIVE SESSION
# ==============================================================

def get_active_trip(trip_id):
    """
    Retrieve the temporary AI session associated
    with a SQLite trip ID.
    """

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

def validate_start_request(trip_data):
    """
    Validate the request coming from the Plan Trip screen.

    Plan Trip only needs:

        trip_id
        user_input
    """

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

    return (
        int(trip_id),
        user_input
    )


# ==============================================================
# EXTRACT CANDIDATES
# ==============================================================

def extract_candidates(candidate_result):
    """
    Extract destination candidates from TravelAgent while
    preserving useful destination information.
    """

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
                    str(name).strip(),

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
                        None
                })

    return candidates


# ==============================================================
# DESTINATION DISPLAY NAMES
# ==============================================================

def destination_names(destination_results):
    """
    Convert structured destination results into the names
    required by MapService and ResearchAgent.
    """

    names = []

    if not isinstance(
        destination_results,
        list
    ):

        return names

    for destination in destination_results:

        if not isinstance(
            destination,
            dict
        ):

            continue

        name = destination.get(
            "name"
        )

        country = destination.get(
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
# VALIDATE MAP RESULTS
# ==============================================================

def validate_map_results(map_results):
    """
    Keep only valid geographic MapTiler results.
    """

    if not isinstance(
        map_results,
        list
    ):

        return []

    valid_results = []

    for location in map_results:

        if not isinstance(
            location,
            dict
        ):

            continue

        if not location.get(
            "found",
            False
        ):

            continue

        coordinates = location.get(
            "coordinates"
        )

        if not isinstance(
            coordinates,
            dict
        ):

            continue

        latitude = coordinates.get(
            "latitude"
        )

        longitude = coordinates.get(
            "longitude"
        )

        if latitude is None:
            continue

        if longitude is None:
            continue

        valid_results.append(
            location
        )

    return valid_results


# ==============================================================
# CREATE TRIP STATE
# ==============================================================

def create_trip_state(
    trip_id,
    session_id,
    trip_information,
    budget
):
    """
    Create the temporary AI planning state.
    """

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

        "preferences":
            {},

        "candidate_result":
            {},

        "candidates":
            [],

        "destination_results":
            [],

        "map_data":
            [],

        "research":
            {},

        "travel_options":
            None,

        "selected_destination":
            None,

        "selected_trip":
            None,

        "budget":
            budget
    }


# ==============================================================
# BUILD DESTINATION SEARCH INPUT
# ==============================================================

def build_destination_search_input(
    trip_information,
    mood_preferences,
    budget_value,
    candidates=None
):
    """
    Build the standardized input expected by
    search_destination.py.
    """

    return {

        "departure_location":
            trip_information.get(
                "departure_location"
            ),

        "trip_scope":
            trip_information.get(
                "trip_scope",
                trip_information.get(
                    "scope",
                    ""
                )
            ),

        "travelers":
            trip_information.get(
                "travelers"
            ),

        "duration_days":
            trip_information.get(
                "duration_days"
            ),

        "travel_dates":
            trip_information.get(
                "travel_dates"
            ),

        "budget":
            budget_value,

        "user_preferences":
            mood_preferences,

        "candidates":
            candidates or []
    }


# ==============================================================
# START TRIP
# ==============================================================

def start_trip(trip_data):
    """
    Start the complete AI travel-planning workflow.

    Workflow:

        SQLite
           ↓
        MoodAgent
           ↓
        TravelAgent
           ↓
        TravelAgent
           ↓
        ┌───────────────┐
        │               │
        MapService   ResearchAgent
        │               │
        └───────┬───────┘
                ↓
        TravelAgent / Gemini
                ↓
             Results
    """

    initialize_systems()

    trip_id, user_input = (
        validate_start_request(
            trip_data
        )
    )

    # ==========================================================
    # GET BASIC INFORMATION FROM SQLITE
    # ==========================================================

    trip_information = get_saved_trip(
        trip_id
    )

    # ==========================================================
    # GET BUDGET
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

    budget = Budget(
        total_budget=float(
            budget_value
        ),
        currency=currency
    )

    # ==========================================================
    # CREATE UNIQUE AI SESSION
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
    # MOOD ANALYSIS
    # ==========================================================

    mood_preferences = (
        mood_agent.interpret(
            user_input
        )
    )

    trip[
        "preferences"
    ] = mood_preferences

    # ==========================================================
    # GEMINI CANDIDATE GENERATION
    # ==========================================================

    budget_state = (
        budget.get_status()
    )

    candidate_result = (
        travel_agent.find_candidates(

            user_input=
                user_input,

            preferences=
                mood_preferences,

            budget=
                budget_state,

            trip_information=
                trip_information
        )
    )

    candidate_objects = extract_candidates(
        candidate_result
    )

    if not candidate_objects:

        del TRIPS[
            trip_id
        ]

        raise ValueError(
            "TravelAgent did not return any candidate destinations."
        )

    # ==========================================================
    # DESTINATION SEARCH / RANKING
    # ==========================================================

    destination_results = []

    for candidate in candidate_objects:

        if not isinstance(
            candidate,
            dict
        ):

            continue

        name = candidate.get(
            "name"
        )

        if not name:

            continue

        destination_results.append({

            "name":
                name,

            "country":
                candidate.get(
                    "country"
                ),

            "description":
                candidate.get(
                    "description"
                ),

            "reason":
                candidate.get(
                    "reason"
                ),

            "source":
                "travel_agent"
        })

    candidates = destination_names(
        destination_results
    )

    if not candidates:

        del TRIPS[
            trip_id
        ]

        raise ValueError(
            "No usable destination candidates were found."
        )

    trip[
        "candidate_result"
    ] = candidate_result

    trip[
        "candidates"
    ] = candidates

    trip[
        "destination_results"
    ] = destination_results

    # ==========================================================
    # MAPTILER + RESEARCH
    # ==========================================================
    #
    # These operations are independent after TravelAgent has
    # selected the candidates, so main.py runs them concurrently.
    #
    # main.py remains the only orchestrator. The agents/services
    # do not communicate directly with one another.
    # ==========================================================

    def get_map_results():

        try:

            return (
                map_service.get_locations(
                    candidates
                )
            )

        except Exception as error:

            return {
                "__error__":
                    str(error)
            }

    def get_research_results():

        try:

            # ResearchAgent is an information-gathering layer.
            # Only the useful preference fields are passed to it.
            research_preferences = {

                "wanted":
                    mood_preferences.get(
                        "wanted",
                        []
                    ),

                "avoid":
                    mood_preferences.get(
                        "avoid",
                        []
                    )
            }

            return (
                research_agent.research(

                    destinations=
                        candidates,

                    preferences=
                        research_preferences,

                    budget=
                        budget_state
                )
            )

        except Exception as error:

            return {

                "destinations":
                    [],

                "error":
                    str(error)
            }

    with ThreadPoolExecutor(
        max_workers=2
    ) as executor:

        map_future = executor.submit(
            get_map_results
        )

        research_future = executor.submit(
            get_research_results
        )

        map_results = map_future.result()

        research_result = (
            research_future.result()
        )

    # ----------------------------------------------------------
    # MAP RESULTS
    # ----------------------------------------------------------

    if isinstance(
        map_results,
        dict
    ) and "__error__" in map_results:

        trip[
            "map_error"
        ] = map_results[
            "__error__"
        ]

        map_results = []

    valid_map_results = (
        validate_map_results(
            map_results
        )
    )

    trip[
        "map_data"
    ] = valid_map_results

    # ----------------------------------------------------------
    # RESEARCH RESULTS
    # ----------------------------------------------------------

    trip[
        "research"
    ] = research_result

    # ==========================================================
    # FINAL GEMINI PASS
    # ==========================================================

    final_response = (
        travel_agent.ask(

            user_input=
                user_input,

            preferences=
                mood_preferences,

            budget=
                budget_state,

            research=
                research_result,

            map_data=
                valid_map_results,

            trip_information=
                trip_information
        )
    )

    trip[
        "travel_options"
    ] = final_response

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

def get_trip_status(trip_data):
    """
    Return the current planning state.
    """

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

        "preferences":
            trip["preferences"],

        "candidate_result":
            trip["candidate_result"],

        "candidates":
            trip["candidates"],

        "destination_results":
            trip["destination_results"],

        "map_data":
            trip["map_data"],

        "research":
            trip["research"],

        "travel_options":
            trip["travel_options"],

        "selected_destination":
            trip["selected_destination"],

        "selected_trip":
            trip["selected_trip"],

        "budget":
            budget.get_status()
    }

    return make_json_safe(
        result
    )


# ==============================================================
# UPDATE TRIP
# ==============================================================

def update_trip(trip_data):
    """
    Re-run the planning pipeline after the user requests
    a change.
    """

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

    old_budget = trip[
        "budget"
    ]

    new_budget = Budget(
        total_budget=
            old_budget.get_total(),

        currency=
            old_budget.currency
    )

    # ==========================================================
    # MOOD
    # ==========================================================

    mood_preferences = (
        mood_agent.interpret(
            updated_request
        )
    )

    # ==========================================================
    # CANDIDATES
    # ==========================================================

    candidate_result = (
        travel_agent.find_candidates(

            user_input=
                updated_request,

            preferences=
                mood_preferences,

            budget=
                new_budget.get_status(),

            trip_information=
                trip_information
        )
    )

    candidate_objects = extract_candidates(
        candidate_result
    )

    if not candidate_objects:

        raise ValueError(
            "TravelAgent did not return any destinations."
        )

    # ==========================================================
    # DESTINATION SEARCH / RANKING
    # ==========================================================

    budget_value = trip_information.get(
        "budget"
    )

    if budget_value is None:

        budget_value = trip_information.get(
            "total_budget"
        )

    destination_results = []

    for candidate in candidate_objects:

        if not isinstance(
            candidate,
            dict
        ):

            continue

        name = candidate.get(
            "name"
        )

        if not name:

            continue

        destination_results.append({

            "name":
                name,

            "country":
                candidate.get(
                    "country"
                ),

            "description":
                candidate.get(
                    "description"
                ),

            "reason":
                candidate.get(
                    "reason"
                ),

            "source":
                "travel_agent"
        })

    candidates = destination_names(
        destination_results
    )

    # ==========================================================
    # MAP + RESEARCH
    # ==========================================================
    #
    # Both operations are independent after candidate selection.
    # Run them concurrently while keeping main.py as the
    # communication/orchestration layer.
    # ==========================================================

    def get_map_results():

        try:

            return (
                map_service.get_locations(
                    candidates
                )
            )

        except Exception:

            return []

    def get_research_results():

        research_preferences = {

            "wanted":
                mood_preferences.get(
                    "wanted",
                    []
                ),

            "avoid":
                mood_preferences.get(
                    "avoid",
                    []
                )
        }

        return (
            research_agent.research(

                destinations=
                    candidates,

                preferences=
                    research_preferences,

                budget=
                    new_budget.get_status()
            )
        )

    with ThreadPoolExecutor(
        max_workers=2
    ) as executor:

        map_future = executor.submit(
            get_map_results
        )

        research_future = executor.submit(
            get_research_results
        )

        map_results = map_future.result()

        research_result = (
            research_future.result()
        )

    valid_map_results = (
        validate_map_results(
            map_results
        )
    )

    # ==========================================================
    # FINAL RESPONSE
    # ==========================================================

    final_response = (
        travel_agent.ask(

            user_input=
                updated_request,

            preferences=
                mood_preferences,

            budget=
                new_budget.get_status(),

            research=
                research_result,

            map_data=
                valid_map_results,

            trip_information=
                trip_information
        )
    )

    # ==========================================================
    # UPDATE SESSION
    # ==========================================================

    trip[
        "status"
    ] = "awaiting_selection"

    trip[
        "original_user_input"
    ] = updated_request

    trip[
        "preferences"
    ] = mood_preferences

    trip[
        "budget"
    ] = new_budget

    trip[
        "candidate_result"
    ] = candidate_result

    trip[
        "candidates"
    ] = candidates

    trip[
        "destination_results"
    ] = destination_results

    trip[
        "map_data"
    ] = valid_map_results

    trip[
        "research"
    ] = research_result

    trip[
        "travel_options"
    ] = final_response

    trip[
        "selected_destination"
    ] = None

    trip[
        "selected_trip"
    ] = None

    return get_trip_status({

        "trip_id":
            trip_id
    })


# ==============================================================
# SELECT TRIP
# ==============================================================

def select_trip(trip_data):
    """
    Select one candidate destination.
    """

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

    selected_destination = (
        trip_data.get(
            "destination"
        )
    )

    trip = get_active_trip(
        trip_id
    )

    candidates = trip[
        "candidates"
    ]

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
                candidates
            )
        ):

            raise ValueError(
                "Selected destination does not exist."
            )

        selected_destination = (
            candidates[
                selected_index
            ]
        )

    # ==========================================================
    # SELECT BY NAME
    # ==========================================================

    if not selected_destination:

        raise ValueError(
            "A destination or selected_index is required."
        )

    if selected_destination not in candidates:

        raise ValueError(
            "Selected destination is not one of the candidates."
        )

    budget = trip[
        "budget"
    ]

    budget.clear_estimates()

    # ==========================================================
    # BUILD SELECTED TRIP
    # ==========================================================

    selected_trip = (
        travel_agent.build_selected_trip(

            selected_destination=
                selected_destination,

            user_input=
                trip[
                    "original_user_input"
                ],

            preferences=
                trip[
                    "preferences"
                ],

            budget=
                budget.get_status(),

            research=
                trip[
                    "research"
                ],

            map_data=
                trip[
                    "map_data"
                ],

            trip_information=
                trip[
                    "trip_information"
                ]
        )
    )

    if not isinstance(
        selected_trip,
        dict
    ):

        raise ValueError(
            "TravelAgent returned an invalid selected-trip result."
        )

    # ==========================================================
    # TEMPORARY COST ESTIMATE
    # ==========================================================

    costs = selected_trip.get(
        "costs",
        []
    )

    if not isinstance(
        costs,
        list
    ):

        costs = []

    known_costs = []

    for cost in costs:

        if not isinstance(
            cost,
            dict
        ):

            continue

        if cost.get(
            "amount"
        ) is None:

            continue

        known_costs.append(
            cost
        )

    budget.set_estimates(
        known_costs
    )

    # ==========================================================
    # SAVE
    # ==========================================================

    trip[
        "selected_destination"
    ] = selected_destination

    trip[
        "selected_trip"
    ] = selected_trip

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

def confirm_trip(trip_data):
    """
    Permanently commit the selected trip's estimated costs.
    """

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

def cancel_trip(trip_data):
    """
    Cancel the active planning session.
    """

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

def delete_trip(trip_data):
    """
    Delete an active AI planning session.
    """

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

# ==============================================================
# RANDOM DESTINATIONS
# ==============================================================

def get_random_destinations_for_trip(
    trip_data=None
):
    """
    Retrieve random destinations through the central
    main.py orchestration layer.

    Architecture:

        app.py
            ↓
        main.py
            ↓
        database.py
            ↓
        random_destination.py
            ↓
        main.py
            ↓
        app.py
    """

    if trip_data is None:

        trip_data = {}

    if not isinstance(
        trip_data,
        dict
    ):

        raise TypeError(
            "trip_data must be a dictionary."
        )

    # ----------------------------------------------------------
    # DATABASE INITIALIZATION
    # ----------------------------------------------------------

    database.initialize_database()

    # ----------------------------------------------------------
    # REQUEST
    # ----------------------------------------------------------

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

    # ----------------------------------------------------------
    # NORMALIZE COUNT
    # ----------------------------------------------------------

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

    # ----------------------------------------------------------
    # GET DESTINATIONS FROM DATABASE
    # ----------------------------------------------------------

    database_results = (
        database.get_random_destinations(
            limit=count
        )
    )

    # ----------------------------------------------------------
    # PASS DATABASE RESULTS TO random_destination.py
    # ----------------------------------------------------------

    random_result = (
        get_random_destinations(

            count=count,

            scope=scope,

            country=country,

            region=region,

            destinations=
                database_results
        )
    )

    destinations = random_result.get(
        "destinations",
        []
    )

    # ----------------------------------------------------------
    # RETURN
    # ----------------------------------------------------------

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
    """
    Main orchestration layer for independent destination search.

    Flow:

        app.py
           ↓
        main.py
           ↓
        search_destination.py
           ↓
        main.py
           ↓
        database.py
           ↓
        if not found
           ↓
        MapTiler
           ↓
        Pexels
           ↓
        search_destination.py
           ↓
        main.py
           ↓
        app.py
    """

    initialize_systems()

    # ------------------------------------------------------
    # Prepare query through search_destination.py
    # ------------------------------------------------------

    search_request = (
        build_search_request(
            query
        )
    )

    query = search_request[
        "query"
    ]

    # ------------------------------------------------------
    # FIRST: DATABASE
    # ------------------------------------------------------

    database_results = (
        database.search_destinations(
            query
        )
    )

    # ------------------------------------------------------
    # DATABASE FOUND
    # ------------------------------------------------------

    if database_results:

        destination = dict(
            database_results[0]
        )

        # --------------------------------------------------
        # If the database destination does not have an image,
        # main.py asks Pexels.
        # --------------------------------------------------

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

            query=query,

            database_results=
                [destination]
        )

    # ------------------------------------------------------
    # DATABASE DID NOT FIND IT
    #
    # MAIN.PY NOW CALLS MAPTILER.
    # ------------------------------------------------------

    live_result = (
        map_service.get_destination_info(
            query
        )
    )

    # ------------------------------------------------------
    # MAPTILER COULD NOT FIND IT
    # ------------------------------------------------------

    if not live_result.get(
        "found",
        False
    ):

        return search_destinations(

            query=query,

            database_results=[],

            live_result=None
        )

    # ------------------------------------------------------
    # MAPTILER FOUND IT
    #
    # MAIN.PY NOW CALLS PEXELS.
    # ------------------------------------------------------

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

    # ------------------------------------------------------
    # FINAL SEARCH RESULT
    # ------------------------------------------------------

    return search_destinations(

        query=query,

        database_results=[],

        live_result=live_result,

        image=image
    )

# ==============================================================
# CLI TEST MODE
# ==============================================================

def main():
    """
    CLI entry point.
    """

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