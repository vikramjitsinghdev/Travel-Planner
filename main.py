import json
from datetime import datetime

from ai.mood_agent import MoodAgent
from ai.travel_agent import TravelAgent
from ai.research_agent import ResearchAgent

from travel.budget import Budget

from location.map import MapService


# ==============================================================
# FORMATTING
# ==============================================================

def print_section(title):
    """Print a formatted section heading."""

    print("\n" + "=" * 60)
    print(title)
    print("=" * 60)


def print_json(data):
    """Print formatted JSON."""

    print(
        json.dumps(
            data,
            indent=4,
            ensure_ascii=False
        )
    )


# ==============================================================
# INPUT HELPERS
# ==============================================================

def ask_required(prompt):
    """
    Ask for a required text input.
    """

    while True:

        value = input(prompt).strip()

        if value:
            return value

        print(
            "Please enter a value."
        )


def ask_optional(prompt):
    """
    Ask for an optional text input.
    """

    return input(prompt).strip()


def ask_positive_integer(prompt):
    """
    Ask for a positive integer.
    """

    while True:

        value = input(prompt).strip()

        try:

            number = int(value)

            if number <= 0:

                print(
                    "Please enter a number greater than 0."
                )

                continue

            return number

        except ValueError:

            print(
                "Please enter a valid whole number."
            )


def ask_budget():
    """
    Ask for the total travel budget.
    """

    while True:

        value = input(
            "\nWhat is your total travel budget in CAD?\n> "
        ).strip()

        try:

            amount = float(value)

            if amount < 0:

                print(
                    "Budget cannot be negative."
                )

                continue

            return amount

        except ValueError:

            print(
                "Please enter a valid number."
            )


# ==============================================================
# DEPARTURE COUNTRY DETECTION
# ==============================================================

def detect_country_from_departure(
    departure_location
):
    """
    Basic country detection from the departure
    location.

    This is intentionally simple.

    The purpose is to support the domestic-trip
    workflow without requiring the user to manually
    enter the country when it can reasonably be
    inferred.

    Example:

        Saint John, NB, Canada

    returns:

        Canada
    """

    text = departure_location.lower()

    country_map = {

        "canada": "Canada",

        "usa": "United States",
        "u.s.a": "United States",
        "united states": "United States",
        "america": "United States",

        "india": "India",

        "japan": "Japan",

        "switzerland": "Switzerland",

        "france": "France",

        "germany": "Germany",

        "uk": "United Kingdom",
        "united kingdom": "United Kingdom",

        "australia": "Australia",

        "new zealand": "New Zealand"
    }

    for keyword, country in country_map.items():

        if keyword in text:

            return country

    # Canadian province detection.

    canadian_provinces = {

        "nb": "Canada",
        "new brunswick": "Canada",

        "ns": "Canada",
        "nova scotia": "Canada",

        "pei": "Canada",
        "prince edward island": "Canada",

        "nl": "Canada",
        "newfoundland": "Canada",

        "qc": "Canada",
        "quebec": "Canada",

        "on": "Canada",
        "ontario": "Canada",

        "mb": "Canada",
        "manitoba": "Canada",

        "sk": "Canada",
        "saskatchewan": "Canada",

        "ab": "Canada",
        "alberta": "Canada",

        "bc": "Canada",
        "british columbia": "Canada",

        "yt": "Canada",
        "yukon": "Canada",

        "nt": "Canada",
        "northwest territories": "Canada",

        "nu": "Canada",
        "nunavut": "Canada"
    }

    for keyword, country in canadian_provinces.items():

        if keyword in text:

            return country

    return None


# ==============================================================
# TRIP SCOPE
# ==============================================================

def ask_trip_scope(
    departure_country
):
    """
    Ask whether the user wants domestic,
    international, or anywhere travel.

    If domestic is selected and the departure
    country is already known, the country question
    is skipped.
    """

    print(
        "\nWhere do you want to travel?"
    )

    print(
        "1. Anywhere in my country"
    )

    print(
        "2. International / abroad"
    )

    print(
        "3. Anywhere"
    )

    while True:

        choice = input(
            "> "
        ).strip()

        if choice == "1":

            if departure_country:

                print(
                    f"\nDetected departure country: "
                    f"{departure_country}"
                )

                print(
                    "Using this as the domestic "
                    "travel country."
                )

                return {
                    "trip_scope": "domestic",
                    "country": departure_country
                }

            country = ask_required(
                "\nWhich country are you traveling within?\n> "
            )

            return {
                "trip_scope": "domestic",
                "country": country
            }

        if choice == "2":

            return {
                "trip_scope": "international",
                "country": None
            }

        if choice == "3":

            return {
                "trip_scope": "anywhere",
                "country": None
            }

        print(
            "Please choose 1, 2, or 3."
        )


# ==============================================================
# BASIC TRIP INFORMATION
# ==============================================================

def collect_trip_information():
    """
    Collect the user's basic trip constraints.

    These are passed to MoodAgent and TravelAgent
    as structured information.
    """

    print_section(
        "BASIC TRIP INFORMATION"
    )

    # ----------------------------------------------------------
    # Departure
    # ----------------------------------------------------------

    departure_location = ask_required(
        "\nWhere will the trip start from?\n> "
    )

    departure_country = detect_country_from_departure(
        departure_location
    )

    # ----------------------------------------------------------
    # Destination scope
    # ----------------------------------------------------------

    scope_information = ask_trip_scope(
        departure_country
    )

    # ----------------------------------------------------------
    # Travelers
    # ----------------------------------------------------------

    travelers = ask_positive_integer(
        "\nHow many people are traveling?\n> "
    )

    # ----------------------------------------------------------
    # Duration
    # ----------------------------------------------------------

    duration_days = ask_positive_integer(
        "\nHow many days do you want the trip to be?\n> "
    )

    # ----------------------------------------------------------
    # Travel dates
    # ----------------------------------------------------------

    travel_dates = ask_required(
        "\nWhen do you want to travel? "
        "(Example: July 2027, July 10-17 2027)\n> "
    )

    # ----------------------------------------------------------
    # Maximum travel time
    # ----------------------------------------------------------

    maximum_total_travel_time = ask_optional(
        "\nWhat is the maximum travel time you are "
        "comfortable with from your departure location?\n"
        "(Example: 6 hours, 12 hours, no preference)\n> "
    )

    if not maximum_total_travel_time:

        maximum_total_travel_time = "no preference"

    # ----------------------------------------------------------
    # Maximum distance
    # ----------------------------------------------------------

    maximum_distance = ask_optional(
        "\nDo you have a maximum travel distance?\n"
        "(Example: 1000 km, no preference)\n> "
    )

    if not maximum_distance:

        maximum_distance = "no preference"

    # ----------------------------------------------------------
    # Transportation
    # ----------------------------------------------------------

    transportation_preference = ask_optional(
        "\nPreferred transportation?\n"
        "(Example: flight, car, train, bus, no preference)\n> "
    )

    if not transportation_preference:

        transportation_preference = "no preference"

    # ----------------------------------------------------------
    # Accommodation
    # ----------------------------------------------------------

    accommodation_preference = ask_optional(
        "\nPreferred accommodation?\n"
        "(Example: hotel, hostel, resort, Airbnb, no preference)\n> "
    )

    if not accommodation_preference:

        accommodation_preference = "no preference"

    # ----------------------------------------------------------
    # Safety
    # ----------------------------------------------------------

    safety_requirement = ask_optional(
        "\nAny safety requirements or concerns?\n"
        "(Press Enter if none)\n> "
    )

    if not safety_requirement:

        safety_requirement = None

    # ----------------------------------------------------------
    # Other
    # ----------------------------------------------------------

    other_requirements = ask_optional(
        "\nAny other trip requirements?\n"
        "(Press Enter if none)\n> "
    )

    if not other_requirements:

        other_requirements = []

    else:

        other_requirements = [
            other_requirements
        ]

    # ----------------------------------------------------------
    # Construct structured information.
    # ----------------------------------------------------------

    return {

        "trip_scope": scope_information.get(
            "trip_scope"
        ),

        "country": scope_information.get(
            "country"
        ),

        "region": None,

        "travelers": travelers,

        "duration_days": duration_days,

        "departure_location": departure_location,

        "maximum_total_travel_time":
            maximum_total_travel_time,

        "maximum_distance":
            maximum_distance,

        "safety_requirement":
            safety_requirement,

        "transportation_preference":
            transportation_preference,

        "accommodation_preference":
            accommodation_preference,

        "travel_dates":
            travel_dates,

        "other":
            other_requirements
    }


# ==============================================================
# CANDIDATE EXTRACTION
# ==============================================================

def extract_candidates(
    candidate_result
):
    """
    Convert TravelAgent candidate output into
    a clean list of destination strings.
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
    Keep only usable MapTiler results.
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
# RESEARCH + MAP
# ==============================================================

def gather_destination_information(
    candidates,
    mood_preferences,
    budget,
    research_agent,
    map_service
):
    """
    Research candidates using ResearchAgent and
    MapService.

    main.py remains the communication layer.
    """

    print_section(
        "MAPPING DESTINATIONS"
    )

    print(
        "\nGetting geographic information from MapTiler..."
    )

    try:

        map_results = map_service.get_locations(
            candidates
        )

    except Exception as error:

        print(
            "\nMapTiler failed."
        )

        print(
            f"Error: {error}"
        )

        map_results = []

    valid_map_results = validate_map_results(
        map_results
    )

    print(
        "\n--- Map Information ---"
    )

    print_json(
        map_results
    )

    print_section(
        "RESEARCHING DESTINATIONS"
    )

    try:

        research_result = research_agent.research(
            destinations=candidates,

            preferences=mood_preferences,

            budget=budget
        )

    except Exception as error:

        print(
            "\nResearchAgent failed."
        )

        print(
            f"Error: {error}"
        )

        research_result = {
            "destinations": []
        }

    print(
        "\n--- Research Information ---"
    )

    print_json(
        research_result
    )

    return (
        research_result,
        valid_map_results
    )


# ==============================================================
# DISPLAY FINAL OPTIONS
# ==============================================================

def display_final_options(
    response
):
    """
    Display the final Gemini travel options.
    """

    print_section(
        "TRAVEL OPTIONS"
    )

    print(
        response
    )


# ==============================================================
# SELECT DESTINATION
# ==============================================================

def select_destination(
    candidates
):
    """
    Ask the user to select one of the candidate
    destinations.

    Returns:

        index
        None
    """

    if not candidates:

        return None

    print_section(
        "SELECT YOUR TRIP"
    )

    print(
        "\nAvailable destinations:"
    )

    for index, destination in enumerate(
        candidates,
        start=1
    ):

        print(
            f"{index}. {destination}"
        )

    print(
        "\n0. Go back / change requirements"
    )

    while True:

        choice = input(
            "\nWhich trip would you like?\n> "
        ).strip()

        try:

            number = int(
                choice
            )

        except ValueError:

            print(
                "Please enter a valid number."
            )

            continue

        if number == 0:

            return None

        if 1 <= number <= len(candidates):

            return number - 1

        print(
            "Please choose one of the listed options."
        )


# ==============================================================
# SELECTED TRIP COST DISPLAY
# ==============================================================

def display_selected_trip(
    selected_trip,
    budget
):
    """
    Display the selected trip's temporary cost
    estimate.
    """

    print_section(
        "SELECTED TRIP COST ESTIMATE"
    )

    print(
        f"\nDestination: "
        f"{selected_trip.get('destination')}"
    )

    print(
        "\n--- Estimated Costs ---"
    )

    costs = selected_trip.get(
        "costs",
        []
    )

    if not costs:

        print(
            "No known costs were returned."
        )

    else:

        for cost in costs:

            category = cost.get(
                "category",
                "other"
            )

            amount = cost.get(
                "amount"
            )

            description = cost.get(
                "description",
                ""
            )

            if amount is None:

                print(
                    f"• {category}: UNKNOWN"
                )

            else:

                print(
                    f"• {category}: "
                    f"{amount:.2f} CAD"
                )

            if description:

                print(
                    f"  {description}"
                )

    # ----------------------------------------------------------
    # Add known costs temporarily to Budget.
    # ----------------------------------------------------------

    known_costs = [
        cost
        for cost in costs
        if cost.get("amount") is not None
    ]

    try:

        budget.set_estimates(
            known_costs
        )

    except Exception as error:

        print(
            "\nCould not create budget estimate."
        )

        print(
            f"Error: {error}"
        )

        return False

    status = budget.get_status()

    print(
        "\n--- Budget Impact ---"
    )

    print(
        f"Current budget: "
        f"{status['remaining']:.2f} "
        f"{status['currency']}"
    )

    print(
        f"Estimated trip cost: "
        f"{status['estimated_total']:.2f} "
        f"{status['currency']}"
    )

    print(
        f"Remaining after trip: "
        f"{status['estimated_remaining']:.2f} "
        f"{status['currency']}"
    )

    if status[
        "estimates_affordable"
    ]:

        print(
            "\n✓ The known estimated costs "
            "fit within the current budget."
        )

    else:

        print(
            "\n✗ The known estimated costs "
            "exceed the current budget."
        )

    unknown_costs = selected_trip.get(
        "unknown_costs",
        []
    )

    if unknown_costs:

        print(
            "\n--- Unknown Costs ---"
        )

        for item in unknown_costs:

            print(
                f"• {item}"
            )

    notes = selected_trip.get(
        "notes",
        []
    )

    if notes:

        print(
            "\n--- Notes ---"
        )

        for note in notes:

            print(
                f"• {note}"
            )

    return True


# ==============================================================
# FINAL TRIP CONFIRMATION
# ==============================================================

def confirm_trip(
    budget
):
    """
    Ask the user whether the temporary trip
    should be committed.
    """

    while True:

        print(
            "\nWhat would you like to do?"
        )

        print(
            "1. Confirm this trip"
        )

        print(
            "2. Change something"
        )

        print(
            "3. Choose another destination"
        )

        print(
            "4. Cancel"
        )

        choice = input(
            "> "
        ).strip()

        if choice == "1":

            try:

                budget.confirm_estimates()

                return "confirmed"

            except Exception as error:

                print(
                    "\nTrip could not be confirmed."
                )

                print(
                    f"Error: {error}"
                )

                return "cancel"

        if choice == "2":

            return "change"

        if choice == "3":

            return "another"

        if choice == "4":

            return "cancel"

        print(
            "Please choose 1, 2, 3, or 4."
        )


# ==============================================================
# MAIN
# ==============================================================

def main():
    """
    Main controller for the AI Travel Planner.

    ============================================================
    COMPLETE WORKFLOW
    ============================================================

        User
          ↓
        Basic Trip Information
          ↓
        User Preferences
          ↓
        Budget
          ↓
        MoodAgent
          ↓
        main.py
          ↓
        TravelAgent.find_candidates()
          ↓
        Candidate Destinations
          ↓
        ┌──────────────────────┐
        │                      │
        ▼                      ▼
    MapService            ResearchAgent
     MapTiler                Ollama
        │                      │
        └──────────┬───────────┘
                   ↓
                main.py
                   ↓
        TravelAgent.ask()
                   ↓
          Final Trip Options
                   ↓
             User Selection
                   ↓
        TravelAgent.build_selected_trip()
                   ↓
          Temporary Budget
             Estimate
                   ↓
             User Review
             /        \
         Change      Confirm
           │            │
           ↓            ↓
       Re-search     Commit
                         ↓
                   Final Budget

    main.py is the communication layer.
    """

    print("=" * 60)
    print("AI TRAVEL PLANNER")
    print("=" * 60)

    # ==========================================================
    # 1. BASIC TRIP INFORMATION
    # ==========================================================

    trip_information = collect_trip_information()

    # ==========================================================
    # 2. USER TRAVEL PREFERENCES
    # ==========================================================

    print_section(
        "YOUR TRAVEL PREFERENCES"
    )

    user_input = ask_required(
        "\nWhat do you want from your trip?\n> "
    )

    # ==========================================================
    # 3. BUDGET
    # ==========================================================

    print_section(
        "TRAVEL BUDGET"
    )

    total_budget = ask_budget()

    budget = Budget(
        total_budget=total_budget,
        currency="CAD"
    )

    # ==========================================================
    # 4. INITIALIZE SYSTEMS
    # ==========================================================

    print_section(
        "INITIALIZING TRAVEL SYSTEMS"
    )

    try:

        print(
            "\nInitializing travel systems..."
        )

        mood_agent = MoodAgent()

        travel_agent = TravelAgent()

        research_agent = ResearchAgent()

        map_service = MapService()

        print(
            "All systems initialized."
        )

    except Exception as error:

        print(
            "\nFailed to initialize travel systems."
        )

        print(
            f"Error: {error}"
        )

        return

    # ==========================================================
    # SEARCH / RESEARCH LOOP
    # ==========================================================
    #
    # This loop allows the user to change requirements
    # without ending the program.
    #
    # ==========================================================

    while True:

        # ------------------------------------------------------
        # 5. MOOD ANALYSIS
        # ------------------------------------------------------

        print_section(
            "ANALYZING TRAVEL PREFERENCES"
        )

        try:

            mood_agent_input = {
                "user_input": user_input,

                "trip_information":
                    trip_information
            }

            mood_preferences = mood_agent.interpret(
                mood_agent_input
            )

        except Exception as error:

            # --------------------------------------------------
            # Compatibility fallback.
            #
            # If MoodAgent currently accepts only a string,
            # use the original user preference text.
            # --------------------------------------------------

            try:

                mood_preferences = mood_agent.interpret(
                    user_input
                )

            except Exception as second_error:

                print(
                    "\nMoodAgent failed."
                )

                print(
                    f"Error: {second_error}"
                )

                return

        print(
            "\n--- Mood Analysis ---"
        )

        print_json(
            mood_preferences
        )

        # ------------------------------------------------------
        # 6. CURRENT TRIP CONSTRAINTS
        # ------------------------------------------------------

        print(
            "\n--- Trip Constraints ---"
        )

        print_json(
            trip_information
        )

        # ------------------------------------------------------
        # 7. CURRENT BUDGET
        # ------------------------------------------------------

        print(
            "\n--- Current Budget ---"
        )

        print_json(
            budget.get_status()
        )

        # ------------------------------------------------------
        # 8. FIND CANDIDATES
        # ------------------------------------------------------

        print_section(
            "SELECTING CANDIDATE DESTINATIONS"
        )

        try:

            candidate_result = (
                travel_agent.find_candidates(
                    user_input=user_input,

                    preferences=mood_preferences,

                    budget=budget.get_status(),

                    trip_information=trip_information
                )
            )

        except Exception as error:

            print(
                "\nTravelAgent candidate generation failed."
            )

            print(
                f"Error: {error}"
            )

            return

        print(
            "\n--- Candidate Destinations ---"
        )

        print_json(
            candidate_result
        )

        candidates = extract_candidates(
            candidate_result
        )

        if not candidates:

            print(
                "\nNo candidate destinations were returned."
            )

            return

        print(
            "\nDestinations selected for research:"
        )

        for destination in candidates:

            print(
                f"• {destination}"
            )

        # ------------------------------------------------------
        # 9. MAP + RESEARCH
        # ------------------------------------------------------

        (
            research_result,
            map_results
        ) = gather_destination_information(

            candidates=candidates,

            mood_preferences=mood_preferences,

            budget=budget.get_status(),

            research_agent=research_agent,

            map_service=map_service
        )

        # ------------------------------------------------------
        # 10. FINAL GEMINI COMPARISON
        # ------------------------------------------------------

        print_section(
            "GENERATING TRAVEL OPTIONS"
        )

        try:

            final_response = travel_agent.ask(

                user_input=user_input,

                preferences=mood_preferences,

                budget=budget.get_status(),

                research=research_result,

                map_data=map_results,

                trip_information=trip_information
            )

        except Exception as error:

            print(
                "\nTravelAgent final planning failed."
            )

            print(
                f"Error: {error}"
            )

            return

        # ------------------------------------------------------
        # 11. DISPLAY OPTIONS
        # ------------------------------------------------------

        display_final_options(
            final_response
        )

        # ------------------------------------------------------
        # 12. USER DECIDES WHAT TO DO
        # ------------------------------------------------------

        print_section(
            "WHAT WOULD YOU LIKE TO DO?"
        )

        print(
            "1. Select one of these trips"
        )

        print(
            "2. Change my requirements"
        )

        print(
            "3. Show the options again"
        )

        print(
            "4. Exit"
        )

        while True:

            choice = input(
                "\n> "
            ).strip()

            if choice in {
                "1",
                "2",
                "3",
                "4"
            }:

                break

            print(
                "Please choose 1, 2, 3, or 4."
            )

        # ======================================================
        # OPTION 4 — EXIT
        # ======================================================

        if choice == "4":

            budget.clear_estimates()

            print(
                "\nNo trip was committed."
            )

            print(
                "Thank you for using AI Travel Planner."
            )

            return

        # ======================================================
        # OPTION 3 — SHOW AGAIN
        # ======================================================

        if choice == "3":

            continue

        # ======================================================
        # OPTION 2 — CHANGE REQUIREMENTS
        # ======================================================

        if choice == "2":

            print_section(
                "CHANGE TRIP REQUIREMENTS"
            )

            change_request = ask_required(
                "\nWhat would you like to change?\n> "
            )

            # --------------------------------------------------
            # Combine the original request with the change.
            #
            # The next MoodAgent / TravelAgent pass receives
            # the complete updated request.
            # --------------------------------------------------

            user_input = (
                f"{user_input}\n\n"
                f"USER REQUESTED CHANGE:\n"
                f"{change_request}"
            )

            # --------------------------------------------------
            # Discard temporary budget estimates.
            # --------------------------------------------------

            budget.clear_estimates()

            print(
                "\nPrevious temporary trip estimates "
                "have been discarded."
            )

            continue

        # ======================================================
        # OPTION 1 — SELECT DESTINATION
        # ======================================================

        selected_index = select_destination(
            candidates
        )

        # ------------------------------------------------------
        # User selected "go back".
        # ------------------------------------------------------

        if selected_index is None:

            print_section(
                "CHANGE TRIP REQUIREMENTS"
            )

            change_request = ask_required(
                "\nWhat would you like to change?\n> "
            )

            user_input = (
                f"{user_input}\n\n"
                f"USER REQUESTED CHANGE:\n"
                f"{change_request}"
            )

            budget.clear_estimates()

            continue

        selected_destination = candidates[
            selected_index
        ]

        print(
            f"\nYou selected:"
            f"\n{selected_destination}"
        )

        # ======================================================
        # 13. BUILD SELECTED TRIP
        # ======================================================

        print_section(
            "BUILDING SELECTED TRIP"
        )

        print(
            "\nCalculating the selected trip..."
        )

        try:

            selected_trip = (
                travel_agent.build_selected_trip(

                    selected_destination=
                        selected_destination,

                    user_input=
                        user_input,

                    preferences=
                        mood_preferences,

                    budget=
                        budget.get_status(),

                    research=
                        research_result,

                    map_data=
                        map_results,

                    trip_information=
                        trip_information
                )
            )

        except Exception as error:

            print(
                "\nCould not build the selected trip."
            )

            print(
                f"Error: {error}"
            )

            budget.clear_estimates()

            continue

        # ======================================================
        # 14. TEMPORARY BUDGET ESTIMATE
        # ======================================================

        estimate_created = display_selected_trip(
            selected_trip=selected_trip,

            budget=budget
        )

        if not estimate_created:

            budget.clear_estimates()

            continue

        # ======================================================
        # 15. CONFIRM / CHANGE / ANOTHER / CANCEL
        # ======================================================

        action = confirm_trip(
            budget
        )

        # ======================================================
        # CONFIRMED
        # ======================================================

        if action == "confirmed":

            print_section(
                "TRIP CONFIRMED"
            )

            print(
                f"\n✓ {selected_destination}"
            )

            print(
                "\nThe estimated trip costs have "
                "been committed to your budget."
            )

            print(
                "\n--- Updated Budget ---"
            )

            print_json(
                budget.get_status()
            )

            print(
                "\nYour trip planning session is complete."
            )

            return

        # ======================================================
        # CHANGE SOMETHING
        # ======================================================

        if action == "change":

            print_section(
                "CHANGE SELECTED TRIP"
            )

            change_request = ask_required(
                "\nWhat would you like to change?\n> "
            )

            user_input = (
                f"{user_input}\n\n"
                f"USER REQUESTED CHANGE:\n"
                f"{change_request}"
            )

            # --------------------------------------------------
            # Discard temporary estimate.
            # --------------------------------------------------

            budget.clear_estimates()

            continue

        # ======================================================
        # CHOOSE ANOTHER DESTINATION
        # ======================================================

        if action == "another":

            budget.clear_estimates()

            print(
                "\nTemporary trip estimate discarded."
            )

            # --------------------------------------------------
            # Go back to the already researched candidates.
            #
            # We do NOT need to call Gemini again.
            # --------------------------------------------------

            selected_index = select_destination(
                candidates
            )

            if selected_index is None:

                continue

            selected_destination = candidates[
                selected_index
            ]

            # --------------------------------------------------
            # Build the newly selected trip.
            # --------------------------------------------------

            try:

                selected_trip = (
                    travel_agent.build_selected_trip(

                        selected_destination=
                            selected_destination,

                        user_input=
                            user_input,

                        preferences=
                            mood_preferences,

                        budget=
                            budget.get_status(),

                        research=
                            research_result,

                        map_data=
                            map_results,

                        trip_information=
                            trip_information
                    )
                )

            except Exception as error:

                print(
                    "\nCould not build the selected trip."
                )

                print(
                    f"Error: {error}"
                )

                budget.clear_estimates()

                continue

            estimate_created = display_selected_trip(
                selected_trip=selected_trip,

                budget=budget
            )

            if not estimate_created:

                budget.clear_estimates()

                continue

            second_action = confirm_trip(
                budget
            )

            if second_action == "confirmed":

                print_section(
                    "TRIP CONFIRMED"
                )

                print(
                    f"\n✓ {selected_destination}"
                )

                print(
                    "\nThe trip has been committed "
                    "to the budget."
                )

                print(
                    "\n--- Updated Budget ---"
                )

                print_json(
                    budget.get_status()
                )

                return

            if second_action == "change":

                change_request = ask_required(
                    "\nWhat would you like to change?\n> "
                )

                user_input = (
                    f"{user_input}\n\n"
                    f"USER REQUESTED CHANGE:\n"
                    f"{change_request}"
                )

                budget.clear_estimates()

                continue

            budget.clear_estimates()

            continue

        # ======================================================
        # CANCEL
        # ======================================================

        budget.clear_estimates()

        print_section(
            "TRIP CANCELLED"
        )

        print(
            "\nNo temporary trip estimate was committed."
        )

        print(
            "\n--- Current Budget ---"
        )

        print_json(
            budget.get_status()
        )

        return


# ==============================================================
# PROGRAM ENTRY POINT
# ==============================================================

if __name__ == "__main__":
    main()