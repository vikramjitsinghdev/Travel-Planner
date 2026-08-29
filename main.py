import json
import uuid

from ai.mood_agent import MoodAgent
from ai.travel_agent import TravelAgent
from ai.research_agent import ResearchAgent

from travel.budget import Budget
from location.map import MapService


# ==============================================================
# TRIP STORAGE
# ==============================================================

# Temporary in-memory storage for active trips.
#
# Later this can be replaced with:
#
#     SQLite
#     PostgreSQL
#     MongoDB
#     Redis
#     etc.
#
# For now this is enough for development.

TRIPS = {}


# ==============================================================
# SYSTEM INITIALIZATION
# ==============================================================

mood_agent = None
travel_agent = None
research_agent = None
map_service = None


def initialize_systems():
    """
    Initialize all AI and map systems.

    The systems are initialized once and then reused.
    """

    global mood_agent
    global travel_agent
    global research_agent
    global map_service

    if mood_agent is None:

        mood_agent = MoodAgent()

    if travel_agent is None:

        travel_agent = TravelAgent()

    if research_agent is None:

        research_agent = ResearchAgent()

    if map_service is None:

        map_service = MapService()


# ==============================================================
# BASIC VALIDATION
# ==============================================================

def validate_trip_data(trip_data):
    """
    Validate the basic information received from the frontend.
    """

    if not isinstance(
        trip_data,
        dict
    ):

        raise TypeError(
            "trip_data must be a dictionary."
        )

    required_fields = [

        "departure_location",

        "trip_scope",

        "travelers",

        "duration_days",

        "travel_dates",

        "budget",

        "user_preferences"
    ]

    for field in required_fields:

        if field not in trip_data:

            raise ValueError(
                f"Missing required field: {field}"
            )


# ==============================================================
# CANDIDATE EXTRACTION
# ==============================================================

def extract_candidates(
    candidate_result
):
    """
    Extract clean destination names from TravelAgent output.
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

            country = candidate.get(
                "country"
            )

            if not name:

                continue

            if country:

                destination = (
                    f"{name}, {country}"
                )

            else:

                destination = name

            candidates.append(
                destination
            )

        elif isinstance(
            candidate,
            str
        ):

            candidates.append(
                candidate
            )

    return candidates


# ==============================================================
# MAP VALIDATION
# ==============================================================

def validate_map_results(
    map_results
):
    """
    Keep only valid MapTiler location results.
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

        if coordinates.get(
            "latitude"
        ) is None:

            continue

        if coordinates.get(
            "longitude"
        ) is None:

            continue

        valid_results.append(
            location
        )

    return valid_results


# ==============================================================
# START TRIP
# ==============================================================

def start_trip(
    trip_data
):
    """
    Start a completely new travel planning session.

    Workflow:

        Frontend
            ↓
        app.py
            ↓
        start_trip()
            ↓
        MoodAgent
            ↓
        TravelAgent
            ↓
        MapService
            ↓
        ResearchAgent
            ↓
        TravelAgent
            ↓
        Trip Options
    """

    validate_trip_data(
        trip_data
    )

    initialize_systems()

    # ==========================================================
    # 1. CREATE TRIP ID
    # ==========================================================

    trip_id = str(
        uuid.uuid4()
    )

    # ==========================================================
    # 2. EXTRACT USER INFORMATION
    # ==========================================================

    user_preferences = trip_data.get(
        "user_preferences"
    )

    if not isinstance(
        user_preferences,
        str
    ):

        raise TypeError(
            "user_preferences must be a string."
        )

    # ----------------------------------------------------------
    # Copy the user's basic trip information.
    # ----------------------------------------------------------

    trip_information = {

        "trip_scope":
            trip_data.get("trip_scope"),

        "country":
            trip_data.get("country"),

        "region":
            trip_data.get("region"),

        "travelers":
            trip_data.get("travelers"),

        "duration_days":
            trip_data.get("duration_days"),

        "departure_location":
            trip_data.get("departure_location"),

        "maximum_total_travel_time":
            trip_data.get(
                "maximum_total_travel_time",
                "no preference"
            ),

        "maximum_distance":
            trip_data.get(
                "maximum_distance",
                "no preference"
            ),

        "safety_requirement":
            trip_data.get(
                "safety_requirement"
            ),

        "transportation_preference":
            trip_data.get(
                "transportation_preference",
                "no preference"
            ),

        "accommodation_preference":
            trip_data.get(
                "accommodation_preference",
                "no preference"
            ),

        "travel_dates":
            trip_data.get("travel_dates"),

        "other":
            trip_data.get(
                "other",
                []
            )
    }

    # ==========================================================
    # 3. CREATE BUDGET
    # ==========================================================

    total_budget = float(
        trip_data.get(
            "budget"
        )
    )

    budget = Budget(
        total_budget=total_budget,
        currency="CAD"
    )

    # ==========================================================
    # 4. MOOD ANALYSIS
    # ==========================================================

    mood_agent_input = {

        "user_input":
            user_preferences,

        "trip_information":
            trip_information
    }

    mood_preferences = mood_agent.interpret(
        mood_agent_input
    )

    # ==========================================================
    # 5. FIND CANDIDATE DESTINATIONS
    # ==========================================================

    budget_state = budget.get_status()

    candidate_result = travel_agent.find_candidates(

        user_input=
            user_preferences,

        preferences=
            mood_preferences,

        budget=
            budget_state,

        trip_information=
            trip_information
    )

    candidates = extract_candidates(
        candidate_result
    )

    if not candidates:

        raise ValueError(
            "TravelAgent did not return any destinations."
        )

    # ==========================================================
    # 6. MAP DESTINATIONS
    # ==========================================================

    try:

        map_results = map_service.get_locations(
            candidates
        )

    except Exception:

        map_results = []

    valid_map_results = validate_map_results(
        map_results
    )

    # ==========================================================
    # 7. RESEARCH DESTINATIONS
    # ==========================================================

    try:

        research_result = research_agent.research(

            destinations=
                candidates,

            preferences=
                mood_preferences,

            budget=
                budget.get_status()
        )

    except Exception as error:

        raise RuntimeError(
            f"ResearchAgent failed: {error}"
        )

    # ==========================================================
    # 8. FINAL TRAVEL AGENT PASS
    # ==========================================================

    final_response = travel_agent.ask(

        user_input=
            user_preferences,

        preferences=
            mood_preferences,

        budget=
            budget.get_status(),

        research=
            research_result,

        map_data=
            valid_map_results,

        trip_information=
            trip_information
    )

    # ==========================================================
    # 9. SAVE TRIP STATE
    # ==========================================================

    TRIPS[trip_id] = {

        "trip_id":
            trip_id,

        "status":
            "awaiting_selection",

        "original_user_input":
            user_preferences,

        "trip_information":
            trip_information,

        "preferences":
            mood_preferences,

        "budget":
            budget,

        "candidate_result":
            candidate_result,

        "candidates":
            candidates,

        "map_data":
            valid_map_results,

        "research":
            research_result,

        "travel_options":
            final_response,

        "selected_destination":
            None,

        "selected_trip":
            None
    }

    # ==========================================================
    # 10. RETURN FRONTEND-SAFE DATA
    # ==========================================================

    return get_trip_status({
        "trip_id": trip_id
    })


# ==============================================================
# GET TRIP STATUS
# ==============================================================

def get_trip_status(
    trip_data
):
    """
    Return the current state of a trip.

    This is what the frontend uses to refresh
    the current planning session.
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

    if not trip_id:

        raise ValueError(
            "trip_id is required."
        )

    trip = TRIPS.get(
        trip_id
    )

    if trip is None:

        raise ValueError(
            "Trip was not found."
        )

    budget = trip["budget"]

    return {

        "trip_id":
            trip["trip_id"],

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


# ==============================================================
# UPDATE TRIP
# ==============================================================

def update_trip(
    trip_data
):
    """
    Update an existing travel planning session.

    The user can provide a change such as:

        "I don't want mountains anymore."

        "Make it cheaper."

        "I want somewhere closer."

        "I want more nightlife."

    For the current version, the safest behavior is to
    run the planning pipeline again using the updated
    request.

    Later, TravelAgent can determine whether existing
    research can be reused.
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

    change_request = trip_data.get(
        "change_request"
    )

    if not trip_id:

        raise ValueError(
            "trip_id is required."
        )

    if not change_request:

        raise ValueError(
            "change_request is required."
        )

    trip = TRIPS.get(
        trip_id
    )

    if trip is None:

        raise ValueError(
            "Trip was not found."
        )

    # ==========================================================
    # UPDATE USER REQUEST
    # ==========================================================

    old_request = trip[
        "original_user_input"
    ]

    updated_request = (
        f"{old_request}\n\n"
        f"USER REQUESTED CHANGE:\n"
        f"{change_request}"
    )

    # ==========================================================
    # REBUILD TRIP DATA
    # ==========================================================

    original_trip_information = (
        trip[
            "trip_information"
        ].copy()
    )

    # ==========================================================
    # CREATE NEW PLANNING REQUEST
    # ==========================================================

    new_trip_data = {

        "departure_location":
            original_trip_information.get(
                "departure_location"
            ),

        "trip_scope":
            original_trip_information.get(
                "trip_scope"
            ),

        "country":
            original_trip_information.get(
                "country"
            ),

        "region":
            original_trip_information.get(
                "region"
            ),

        "travelers":
            original_trip_information.get(
                "travelers"
            ),

        "duration_days":
            original_trip_information.get(
                "duration_days"
            ),

        "travel_dates":
            original_trip_information.get(
                "travel_dates"
            ),

        "maximum_total_travel_time":
            original_trip_information.get(
                "maximum_total_travel_time"
            ),

        "maximum_distance":
            original_trip_information.get(
                "maximum_distance"
            ),

        "transportation_preference":
            original_trip_information.get(
                "transportation_preference"
            ),

        "accommodation_preference":
            original_trip_information.get(
                "accommodation_preference"
            ),

        "safety_requirement":
            original_trip_information.get(
                "safety_requirement"
            ),

        "other":
            original_trip_information.get(
                "other"
            ),

        "budget":
            trip["budget"].get_total(),

        "user_preferences":
            updated_request
    }

    # ==========================================================
    # PRESERVE ORIGINAL BUDGET
    # ==========================================================

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
    # MOOD ANALYSIS
    # ==========================================================

    mood_agent_input = {

        "user_input":
            updated_request,

        "trip_information":
            original_trip_information
    }

    mood_preferences = mood_agent.interpret(
        mood_agent_input
    )

    # ==========================================================
    # FIND NEW CANDIDATES
    # ==========================================================

    candidate_result = travel_agent.find_candidates(

        user_input=
            updated_request,

        preferences=
            mood_preferences,

        budget=
            new_budget.get_status(),

        trip_information=
            original_trip_information
    )

    candidates = extract_candidates(
        candidate_result
    )

    if not candidates:

        raise ValueError(
            "TravelAgent did not return any destinations."
        )

    # ==========================================================
    # MAP
    # ==========================================================

    try:

        map_results = map_service.get_locations(
            candidates
        )

    except Exception:

        map_results = []

    valid_map_results = validate_map_results(
        map_results
    )

    # ==========================================================
    # RESEARCH
    # ==========================================================

    research_result = research_agent.research(

        destinations=
            candidates,

        preferences=
            mood_preferences,

        budget=
            new_budget.get_status()
    )

    # ==========================================================
    # FINAL TRAVEL OPTIONS
    # ==========================================================

    final_response = travel_agent.ask(

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
            original_trip_information
    )

    # ==========================================================
    # UPDATE EXISTING TRIP
    # ==========================================================

    trip["status"] = (
        "awaiting_selection"
    )

    trip["original_user_input"] = (
        updated_request
    )

    trip["preferences"] = (
        mood_preferences
    )

    trip["budget"] = (
        new_budget
    )

    trip["candidate_result"] = (
        candidate_result
    )

    trip["candidates"] = (
        candidates
    )

    trip["map_data"] = (
        valid_map_results
    )

    trip["research"] = (
        research_result
    )

    trip["travel_options"] = (
        final_response
    )

    trip["selected_destination"] = (
        None
    )

    trip["selected_trip"] = (
        None
    )

    return get_trip_status({
        "trip_id": trip_id
    })


# ==============================================================
# SELECT TRIP
# ==============================================================

def select_trip(
    trip_data
):
    """
    Select a destination from the candidate list.

    This does NOT commit the budget.

    It asks TravelAgent to construct the detailed
    selected-trip cost estimate.
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

    selected_index = trip_data.get(
        "selected_index"
    )

    selected_destination = trip_data.get(
        "destination"
    )

    if not trip_id:

        raise ValueError(
            "trip_id is required."
        )

    trip = TRIPS.get(
        trip_id
    )

    if trip is None:

        raise ValueError(
            "Trip was not found."
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

        if selected_index < 0:

            raise ValueError(
                "selected_index cannot be negative."
            )

        if selected_index >= len(
            candidates
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
    # SELECT BY DESTINATION NAME
    # ==========================================================

    if not selected_destination:

        raise ValueError(
            "A destination or selected_index is required."
        )

    if selected_destination not in candidates:

        raise ValueError(
            "Selected destination is not one of the candidates."
        )

    # ==========================================================
    # CLEAR OLD ESTIMATE
    # ==========================================================

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

    # ==========================================================
    # TEMPORARY ESTIMATE
    # ==========================================================

    costs = selected_trip.get(
        "costs",
        []
    )

    known_costs = [

        cost

        for cost in costs

        if isinstance(
            cost,
            dict
        )

        and cost.get(
            "amount"
        ) is not None
    ]

    budget.set_estimates(
        known_costs
    )

    # ==========================================================
    # SAVE STATE
    # ==========================================================

    trip["selected_destination"] = (
        selected_destination
    )

    trip["selected_trip"] = (
        selected_trip
    )

    trip["status"] = (
        "awaiting_confirmation"
    )

    return get_trip_status({
        "trip_id": trip_id
    })


# ==============================================================
# CONFIRM TRIP
# ==============================================================

def confirm_trip(
    trip_data
):
    """
    Permanently commit the selected trip's known
    estimated expenses to the Budget.

    This should only happen after user confirmation.
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

    if not trip_id:

        raise ValueError(
            "trip_id is required."
        )

    trip = TRIPS.get(
        trip_id
    )

    if trip is None:

        raise ValueError(
            "Trip was not found."
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

    # ==========================================================
    # COMMIT TEMPORARY ESTIMATES
    # ==========================================================

    budget.confirm_estimates()

    trip["status"] = (
        "confirmed"
    )

    return get_trip_status({
        "trip_id": trip_id
    })


# ==============================================================
# CANCEL TRIP
# ==============================================================

def cancel_trip(
    trip_data
):
    """
    Cancel the current planning session.

    Any temporary budget estimate is discarded.
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

    if not trip_id:

        raise ValueError(
            "trip_id is required."
        )

    trip = TRIPS.get(
        trip_id
    )

    if trip is None:

        raise ValueError(
            "Trip was not found."
        )

    trip["budget"].clear_estimates()

    trip["status"] = (
        "cancelled"
    )

    return get_trip_status({
        "trip_id": trip_id
    })


# ==============================================================
# DELETE TRIP
# ==============================================================

def delete_trip(
    trip_data
):
    """
    Completely remove a temporary trip session.
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

    if not trip_id:

        raise ValueError(
            "trip_id is required."
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
# CLI TEST MODE
# ==============================================================

def main():
    """
    Minimal CLI test.

    The Flask application is now the primary interface.

    This function exists only so that:

        python main.py

    still works for backend testing.
    """

    print("=" * 60)
    print("AI TRAVEL PLANNER BACKEND TEST")
    print("=" * 60)

    print(
        "\nmain.py is now designed to be controlled "
        "through app.py / Flask."
    )

    print(
        "\nUse:"
    )

    print(
        "    python app.py"
    )

    print(
        "\nto start the web application."
    )


if __name__ == "__main__":

    main()