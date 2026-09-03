import json
import uuid

import database

from ai.mood_agent import MoodAgent
from ai.travel_agent import TravelAgent

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
map_service = None


# ==============================================================
# INITIALIZE SYSTEMS
# ==============================================================

def initialize_systems():

    global mood_agent
    global travel_agent
    global map_service

    database.initialize_database()

    # ----------------------------------------------------------
    # MoodAgent
    # ----------------------------------------------------------

    if mood_agent is None:

        mood_agent = MoodAgent()

    # ----------------------------------------------------------
    # TravelAgent
    #
    # IMPORTANT:
    #
    # TravelAgent now internally owns:
    #
    # Gemini
    # ResearchAgent
    # Pexels
    #
    # main.py does NOT instantiate ResearchAgent separately.
    # ----------------------------------------------------------

    if travel_agent is None:

        travel_agent = TravelAgent()

    # ----------------------------------------------------------
    # MapService
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
                ensure_ascii=False,
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
        # NEW TRAVEL AGENT PIPELINE
        # ------------------------------------------------------

        "candidate_result":
            {},

        "candidates":
            [],

        "candidate_names":
            [],

        # Research is now already enriched by TravelAgent.
        "research":
            {},

        # Direct frontend-ready options.
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
# MOOD AGENT
# ==============================================================

def extract_trip_requirements(
    user_input,
    trip_information
):

    initialize_systems()

    result = mood_agent.interpret(

        user_input=
            user_input,

        trip_information=
            trip_information
    )

    if not isinstance(
        result,
        dict
    ):

        raise ValueError(
            "MoodAgent returned invalid trip requirements."
        )

    return result


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

        name = str(
            name
        ).strip()

        country = str(
            country or ""
        ).strip()

        if country:

            names.append(
                f"{name}, {country}"
            )

        else:

            names.append(
                name
            )

    return names


# ==============================================================
# EXTRACT CANDIDATES FROM TRAVEL AGENT
# ==============================================================

def extract_candidates(
    result
):

    if not isinstance(
        result,
        dict
    ):

        return []

    destinations = result.get(
        "destinations",
        []
    )

    if not isinstance(
        destinations,
        list
    ):

        return []

    candidates = []

    for index, destination in enumerate(
        destinations,
        start=1
    ):

        if not isinstance(
            destination,
            dict
        ):

            continue

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

        if not name:

            continue

        candidates.append({

            "name":
                name,

            "country":
                country,

            "description":
                str(
                    destination.get(
                        "description",
                        ""
                    )
                ).strip(),

            "reason":
                str(
                    destination.get(
                        "reason",
                        ""
                    )
                ).strip(),

            "research_priority":
                destination.get(
                    "research_priority",
                    index
                ),

            "image":
                destination.get(
                    "image",
                    {}
                ),

            "research":
                destination.get(
                    "research",
                    {}
                ),

            "rank":
                destination.get(
                    "rank",
                    index
                )
        })

    if len(candidates) != 3:

        raise ValueError(
            "TravelAgent must return exactly three "
            f"destinations. Got {len(candidates)}."
        )

    return candidates


# ==============================================================
# COMPLETE TRAVEL ORCHESTRATION
# ==============================================================

def run_travel_orchestration(
    user_input,
    trip_requirements,
    trip_information,
    budget
):
    """
    NEW ARCHITECTURE.

        User
          ↓
        MoodAgent
          ↓
        TripRequirements
          ↓
        TravelAgent
          ↓
        Gemini selects EXACTLY 3
          ↓
        ResearchAgent
          ├── Worker 1 → Destination 1
          ├── Worker 2 → Destination 2
          └── Worker 3 → Destination 3
          ↓
        Gemma verification
          ↓
        Pexels images
          ↓
        TravelAgent combines everything
          ↓
        main.py stores the result

    IMPORTANT:

    main.py no longer:
        - creates research plans
        - creates worker questions
        - launches workers
        - evaluates destinations
        - ranks destinations
        - asks Gemini to select final trips
        - calls Pexels directly for recommendation images
    """

    initialize_systems()

    # ----------------------------------------------------------
    # Get current budget state.
    # ----------------------------------------------------------

    budget_state = budget.get_status()

    # ----------------------------------------------------------
    # TravelAgent owns the complete recommendation pipeline.
    # ----------------------------------------------------------

    result = travel_agent.get_trip_recommendations(

        user_input=
            user_input,

        preferences=
            trip_requirements,

        budget=
            budget_state,

        trip_information=
            trip_information
    )

    if not isinstance(
        result,
        dict
    ):

        raise ValueError(
            "TravelAgent returned invalid recommendation data."
        )

    # ----------------------------------------------------------
    # TravelAgent already returns exactly three enriched
    # destinations.
    # ----------------------------------------------------------

    candidates = extract_candidates(
        result
    )

    # ----------------------------------------------------------
    # Return a structure that is easy for the session state
    # and frontend to consume.
    # ----------------------------------------------------------

    return {

        "success":
            result.get(
                "success",
                False
            ),

        "research_strategy":
            result.get(
                "research_strategy",
                ""
            ),

        "candidate_result": {

            "research_strategy":
                result.get(
                    "research_strategy",
                    ""
                ),

            "candidates":
                candidates
        },

        "candidates":
            candidates,

        # TravelAgent's enriched destination objects are already
        # suitable as the three frontend travel options.
        "travel_options":
            candidates,

        "research":
            result.get(
                "research",
                {}
            )
    }


# ==============================================================
# START TRIP
# ==============================================================

def start_trip(
    trip_data
):

    initialize_systems()

    # ==========================================================
    # STEP 1 — VALIDATE USER REQUEST
    # ==========================================================

    (
        trip_id,
        user_input
    ) = validate_start_request(
        trip_data
    )

    # ==========================================================
    # STEP 2 — LOAD BASIC TRIP INFORMATION
    # ==========================================================

    trip_information = get_saved_trip(
        trip_id
    )

    # ==========================================================
    # STEP 3 — CREATE BUDGET
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
    # STEP 4 — CREATE SESSION
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
    # STEP 5 — MOOD AGENT
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

    # Compatibility alias.
    trip[
        "preferences"
    ] = trip_requirements

    # ==========================================================
    # STEP 6 — COMPLETE NEW AI PIPELINE
    # ==========================================================

    orchestration = (
        run_travel_orchestration(

            user_input=
                user_input,

            trip_requirements=
                trip_requirements,

            trip_information=
                trip_information,

            budget=
                budget
        )
    )

    # ==========================================================
    # STEP 7 — SAVE RESULTS
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
        trip[
            "candidates"
        ]
    )

    trip[
        "research"
    ] = orchestration.get(
        "research",
        {}
    )

    trip[
        "travel_options"
    ] = orchestration.get(
        "travel_options",
        []
    )

    # ==========================================================
    # STEP 8 — READY FOR USER SELECTION
    # ==========================================================

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

    return make_json_safe({

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
        # MOOD
        # ------------------------------------------------------

        "trip_requirements":
            trip["trip_requirements"],

        "preferences":
            trip["preferences"],

        # ------------------------------------------------------
        # RECOMMENDATIONS
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

        # ------------------------------------------------------
        # RESEARCH
        # ------------------------------------------------------

        "research":
            trip["research"],

        # ------------------------------------------------------
        # FINAL FRONTEND OPTIONS
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
    })


# ==============================================================
# UPDATE TRIP THROUGH CHAT
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

    # ----------------------------------------------------------
    # Preserve the entire conversation/change history.
    # ----------------------------------------------------------

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
    # RE-RUN MOOD AGENT
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
    # RE-RUN COMPLETE NEW PIPELINE
    # ==========================================================

    orchestration = (
        run_travel_orchestration(

            user_input=
                updated_request,

            trip_requirements=
                trip_requirements,

            trip_information=
                trip_information,

            budget=
                budget
        )
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
        trip[
            "candidates"
        ]
    )

    trip[
        "research"
    ] = orchestration.get(
        "research",
        {}
    )

    trip[
        "travel_options"
    ] = orchestration.get(
        "travel_options",
        []
    )

    # ----------------------------------------------------------
    # Clear old selection.
    # ----------------------------------------------------------

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

        if (
            isinstance(
                result,
                dict
            )
            and
            result.get(
                "found",
                False
            )
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
# SELECT TRIP
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
            "No travel options are available."
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

        requested_destination = str(
            selected_destination or ""
        ).strip().lower()

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
                "three travel options."
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
    # MAP
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
    # GET THE RESEARCH FOR THE SELECTED DESTINATION
    # ==========================================================

    selected_research = {}

    if isinstance(
        selected_option,
        dict
    ):

        selected_research = selected_option.get(
            "research",
            {}
        )

    if not isinstance(
        selected_research,
        dict
    ):

        selected_research = {}

    # ==========================================================
    # BUILD DETAILED SELECTED TRIP
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
            selected_research,

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

    # ----------------------------------------------------------
    # Preserve which option the user selected.
    # ----------------------------------------------------------

    trip[
        "selected_destination"
    ] = selected_destination

    trip[
        "selected_trip"
    ] = {

        "option":
            selected_option,

        "details":
            detailed_trip
    }

    trip[
        "status"
    ] = "selected"

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

    if not trip.get(
        "selected_trip"
    ):

        raise ValueError(
            "No trip has been selected."
        )

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
        "status"
    ] = "cancelled"

    trip[
        "selected_destination"
    ] = None

    trip[
        "selected_trip"
    ] = None

    trip[
        "map_data"
    ] = []

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

    normalized_query = search_request[
        "query"
    ]

    database_results = (
        database.search_destinations(
            normalized_query
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
                normalized_query,

            database_results=
                [destination]
        )

    # ----------------------------------------------------------
    # MAPTILER FALLBACK
    # ----------------------------------------------------------

    live_result = (
        map_service.get_destination_info(
            normalized_query
        )
    )

    if not live_result.get(
        "found",
        False
    ):

        return search_destinations(

            query=
                normalized_query,

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
            normalized_query,

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
    print("WANDERLUST AI TRAVEL PLANNER BACKEND")
    print("=" * 60)

    print()
    print("Start the web application with:")
    print()
    print("    python app.py")


if __name__ == "__main__":

    main()