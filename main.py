import json

from ai.mood_agent import MoodAgent
from ai.travel_agent import TravelAgent
from ai.research_agent import ResearchAgent

from travel.budget import Budget
from location.map import MapService


# ==============================================================
# DISPLAY HELPERS
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
            indent=4
        )
    )


# ==============================================================
# INPUT HELPERS
# ==============================================================

def ask_required(prompt):
    """
    Ask the user for required text input.
    """

    while True:

        value = input(
            prompt
        ).strip()

        if value:

            return value

        print(
            "Please enter a value."
        )


def ask_optional(prompt):
    """
    Ask the user for optional text input.

    Empty input becomes None.
    """

    value = input(
        prompt
    ).strip()

    if not value:

        return None

    return value


def ask_positive_integer(
    prompt,
    minimum=1
):
    """
    Ask for a positive integer.
    """

    while True:

        value = input(
            prompt
        ).strip()

        try:

            number = int(
                value
            )

            if number < minimum:

                print(
                    f"Please enter a number "
                    f"greater than or equal to {minimum}."
                )

                continue

            return number

        except ValueError:

            print(
                "Please enter a valid whole number."
            )


def ask_positive_float(
    prompt,
    minimum=0
):
    """
    Ask for a valid non-negative number.
    """

    while True:

        value = input(
            prompt
        ).strip()

        try:

            number = float(
                value
            )

            if number < minimum:

                print(
                    f"Please enter a number "
                    f"greater than or equal to {minimum}."
                )

                continue

            return number

        except ValueError:

            print(
                "Please enter a valid number."
            )

def infer_country_from_departure(
    departure
):
    """
    Try to determine the departure country from the
    user's departure location.

    This is intentionally conservative.

    We only infer a country when there is a strong
    indication.

    Returns:
        country name or None
    """

    if not isinstance(
        departure,
        str
    ):

        return None

    text = departure.strip().lower()

    if not text:

        return None

    # ----------------------------------------------------------
    # Explicit country names.
    # ----------------------------------------------------------

    explicit_countries = {

        "canada": "Canada",

        "united states": "United States",

        "usa": "United States",

        "u.s.a": "United States",

        "united states of america": "United States",

        "mexico": "Mexico",

        "france": "France",

        "germany": "Germany",

        "italy": "Italy",

        "spain": "Spain",

        "japan": "Japan",

        "india": "India",

        "australia": "Australia",

        "new zealand": "New Zealand",

        "switzerland": "Switzerland",

        "united kingdom": "United Kingdom",

        "uk": "United Kingdom"
    }

    for text_name, country in explicit_countries.items():

        if text_name in text:

            return country

    # ----------------------------------------------------------
    # Canadian provinces / territories.
    #
    # If the departure contains one of these, we can safely
    # infer Canada.
    # ----------------------------------------------------------

    canadian_regions = [

        "ab",
        "alberta",

        "bc",
        "b.c",
        "british columbia",

        "mb",
        "manitoba",

        "nb",
        "n.b",
        "new brunswick",

        "nl",
        "n.l",
        "newfoundland",
        "newfoundland and labrador",

        "ns",
        "n.s",
        "nova scotia",

        "nt",
        "n.t",
        "northwest territories",

        "nu",
        "n.u",
        "nunavut",

        "on",
        "ontario",

        "pe",
        "p.e",
        "prince edward island",

        "qc",
        "quebec",

        "sk",
        "saskatchewan",

        "yt",
        "y.t",
        "yukon"
    ]

    # ----------------------------------------------------------
    # Check explicit region words first.
    # ----------------------------------------------------------

    for region in canadian_regions:

        if region in text:

            return "Canada"

    # ----------------------------------------------------------
    # Common Canadian city + location combinations.
    #
    # This is intentionally limited.
    # ----------------------------------------------------------

    canadian_cities = [

        "saint john",

        "fredericton",

        "moncton",

        "halifax",

        "toronto",

        "ottawa",

        "montreal",

        "quebec city",

        "vancouver",

        "victoria",

        "calgary",

        "edmonton",

        "winnipeg",

        "saskatoon",

        "regina",

        "kelowna",

        "hamilton",

        "london"
    ]

    for city in canadian_cities:

        if city in text:

            return "Canada"

    # ----------------------------------------------------------
    # Unknown.
    # ----------------------------------------------------------

    return None
# ==============================================================
# COLLECT BASIC TRIP INFORMATION
# ==============================================================

def collect_trip_information():
    """
    Collect the basic constraints of the trip.

    This information is separate from the user's moods.

    Example:

        departure_location
        trip_scope
        country
        travelers
        duration_days
        travel_dates
        maximum_total_travel_time
        transportation_preference
        accommodation_preference
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

    # ----------------------------------------------------------
    # Trip scope
    # ----------------------------------------------------------

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

            trip_scope = "domestic"

            # ------------------------------------------------------
            # Try to determine the country from the departure
            # location.
            # ------------------------------------------------------

            inferred_country = (
                infer_country_from_departure(
                    departure_location
                )
            )

            if inferred_country:

                country = inferred_country

                print(
                    f"\nDetected departure country: "
                    f"{country}"
                )

                print(
                    "Using this as the domestic travel country."
                )

            else:

                # --------------------------------------------------
                # Only ask the question when the country could
                # NOT be reliably determined.
                # --------------------------------------------------

                country = ask_required(
                    "\nWhich country are you traveling within?\n> "
                )

            break

        elif choice == "2":

            trip_scope = "international"

            country = ask_optional(
                "Is there a specific country you want to visit? "
                "(Press Enter for any country)\n> "
            )

            break

        elif choice == "3":

            trip_scope = "anywhere"

            country = None

            break

        else:

            print(
                "Please choose 1, 2, or 3."
            )

    # ----------------------------------------------------------
    # Number of travelers
    # ----------------------------------------------------------

    travelers = ask_positive_integer(
        "\nHow many people are traveling?\n> "
    )

    # ----------------------------------------------------------
    # Trip duration
    # ----------------------------------------------------------

    duration_days = ask_positive_integer(
        "\nHow many days do you want the trip to be?\n> "
    )

    # ----------------------------------------------------------
    # Travel dates
    # ----------------------------------------------------------

    travel_dates = ask_optional(
        "\nWhen do you want to travel? "
        "(Example: July 2027, July 10-17 2027)\n> "
    )

    # ----------------------------------------------------------
    # Maximum travel time
    # ----------------------------------------------------------

    maximum_total_travel_time = ask_optional(
        "\nWhat is the maximum travel time you are comfortable "
        "with from your departure location?\n"
        "(Example: 6 hours, 12 hours, no preference)\n> "
    )

    # ----------------------------------------------------------
    # Maximum distance
    # ----------------------------------------------------------

    maximum_distance = ask_optional(
        "\nDo you have a maximum travel distance?\n"
        "(Example: 1000 km, no preference)\n> "
    )

    # ----------------------------------------------------------
    # Transportation
    # ----------------------------------------------------------

    transportation_preference = ask_optional(
        "\nPreferred transportation?\n"
        "(Example: flight, car, train, bus, no preference)\n> "
    )

    # ----------------------------------------------------------
    # Accommodation
    # ----------------------------------------------------------

    accommodation_preference = ask_optional(
        "\nPreferred accommodation?\n"
        "(Example: hotel, hostel, resort, Airbnb, no preference)\n> "
    )

    # ----------------------------------------------------------
    # Safety
    # ----------------------------------------------------------

    safety_requirement = ask_optional(
        "\nAny safety requirements or concerns?\n"
        "(Press Enter if none)\n> "
    )

    # ----------------------------------------------------------
    # Additional requirements
    # ----------------------------------------------------------

    other = ask_optional(
        "\nAny other trip requirements?\n"
        "(Press Enter if none)\n> "
    )

    # ----------------------------------------------------------
    # Construct trip information
    # ----------------------------------------------------------

    return {

        "trip_scope": trip_scope,

        "country": country,

        "region": None,

        "travelers": travelers,

        "duration_days": duration_days,

        "departure_location": departure_location,

        "maximum_total_travel_time": (
            maximum_total_travel_time
        ),

        "maximum_distance": (
            maximum_distance
        ),

        "safety_requirement": (
            safety_requirement
        ),

        "transportation_preference": (
            transportation_preference
        ),

        "accommodation_preference": (
            accommodation_preference
        ),

        "travel_dates": travel_dates,

        "other": (
            [other]
            if other
            else []
        )
    }


# ==============================================================
# GET BUDGET
# ==============================================================

def collect_budget():
    """
    Ask for the user's total CAD budget.
    """

    print_section(
        "TRAVEL BUDGET"
    )

    total_budget = ask_positive_float(
        "\nWhat is your total travel budget in CAD?\n> "
    )

    return Budget(
        total_budget=total_budget,
        currency="CAD"
    )


# ==============================================================
# EXTRACT CANDIDATES
# ==============================================================

def extract_candidates(
    candidate_result
):
    """
    Extract destination names from TravelAgent output.

    Expected:

        {
            "candidates": [
                {
                    "name": "Vancouver",
                    "country": "Canada"
                }
            ]
        }
    """

    if not isinstance(
        candidate_result,
        dict
    ):

        return []

    candidates = []

    for candidate in candidate_result.get(
        "candidates",
        []
    ):

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

                candidates.append(
                    f"{name}, {country}"
                )

            else:

                candidates.append(
                    name
                )

        elif isinstance(
            candidate,
            str
        ):

            candidate = candidate.strip()

            if candidate:

                candidates.append(
                    candidate
                )

    # ----------------------------------------------------------
    # Remove duplicates while preserving order.
    # ----------------------------------------------------------

    unique_candidates = []

    for candidate in candidates:

        if candidate not in unique_candidates:

            unique_candidates.append(
                candidate
            )

    return unique_candidates


# ==============================================================
# MAIN
# ==============================================================

def main():
    """
    Main controller for the AI Travel Planner.

    ============================================================
    CURRENT ARCHITECTURE
    ============================================================

    User
      |
      v
    main.py
      |
      +--------------------+
      |                    |
      v                    v
    Trip Info            User Request
      |                    |
      +---------+----------+
                |
                v
           MoodAgent
              Groq
                |
                v
             main.py
                |
                v
          TravelAgent
             Gemini
                |
                v
       Candidate Destinations
                |
          +-----+------+
          |            |
          v            v
      MapService   ResearchAgent
       MapTiler      Ollama
          |            |
          +-----+------+
                |
                v
             main.py
                |
                v
          TravelAgent
             Gemini
                |
                v
        Final Trip Options
    """

    # ==========================================================
    # HEADER
    # ==========================================================

    print("=" * 60)
    print("AI TRAVEL PLANNER")
    print("=" * 60)

    # ==========================================================
    # 1. BASIC TRIP INFORMATION
    # ==========================================================

    trip_information = (
        collect_trip_information()
    )

    # ==========================================================
    # 2. USER'S PERSONAL TRAVEL PREFERENCES
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

    budget = collect_budget()

    # ==========================================================
    # 4. CREATE SYSTEM COMPONENTS
    # ==========================================================

    print_section(
        "INITIALIZING TRAVEL SYSTEMS"
    )

    print(
        "\nInitializing travel systems..."
    )

    try:

        mood_agent = MoodAgent()

        travel_agent = TravelAgent()

        research_agent = ResearchAgent()

        map_service = MapService()

    except Exception as error:

        print(
            "\nFailed to initialize travel systems."
        )

        print(
            f"Error: {error}"
        )

        return

    print(
        "All systems initialized."
    )

    # ==========================================================
    # 5. MOOD ANALYSIS
    # ==========================================================

    print_section(
        "ANALYZING TRAVEL PREFERENCES"
    )

    try:

        mood_preferences = mood_agent.interpret(
            user_input=user_input,
            trip_information=trip_information
        )

    except Exception as error:

        print(
            "\nMoodAgent failed."
        )

        print(
            f"Error: {error}"
        )

        return

    print(
        "\n--- Mood Analysis ---"
    )

    print_json(
        mood_preferences
    )

    # ==========================================================
    # 6. COMBINE TRIP CONSTRAINTS
    # ==========================================================

    print(
        "\n--- Trip Constraints ---"
    )

    print_json(
        trip_information
    )

    # ----------------------------------------------------------
    # Put the manually collected constraints into the mood
    # profile so TravelAgent has one complete preference object.
    # ----------------------------------------------------------

    if isinstance(
        mood_preferences,
        dict
    ):

        mood_preferences[
            "constraints"
        ] = trip_information

    # ==========================================================
    # 7. INITIAL BUDGET
    # ==========================================================

    budget_state = (
        budget.get_status()
    )

    print(
        "\n--- Current Budget ---"
    )

    print_json(
        budget_state
    )

    # ==========================================================
    # 8. GEMINI CANDIDATE GENERATION
    # ==========================================================

    print_section(
        "SELECTING CANDIDATE DESTINATIONS"
    )

    try:

        candidate_result = (
            travel_agent.find_candidates(

                user_input=user_input,

                preferences=mood_preferences,

                budget=budget_state,

                trip_information=trip_information
            )
        )

    except TypeError:

        # ------------------------------------------------------
        # Temporary compatibility fallback.
        #
        # If your current TravelAgent.find_candidates()
        # does not yet accept trip_information, this keeps
        # the rest of the program working.
        #
        # We will remove this once TravelAgent is rewritten.
        # ------------------------------------------------------

        try:

            candidate_result = (
                travel_agent.find_candidates(

                    user_input=user_input,

                    preferences=mood_preferences,

                    budget=budget_state
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

    except Exception as error:

        print(
            "\nTravelAgent candidate generation failed."
        )

        print(
            f"Error: {error}"
        )

        return

    # ==========================================================
    # 9. DISPLAY CANDIDATES
    # ==========================================================

    print(
        "\n--- Candidate Destinations ---"
    )

    print_json(
        candidate_result
    )

    # ==========================================================
    # 10. EXTRACT DESTINATIONS
    # ==========================================================

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

    for candidate in candidates:

        print(
            f"• {candidate}"
        )

    # ==========================================================
    # 11. MAPTILER
    # ==========================================================

    print_section(
        "MAPPING DESTINATIONS"
    )

    print(
        "\nGetting geographic information from MapTiler..."
    )

    try:

        map_results = (
            map_service.get_locations(
                candidates
            )
        )

    except Exception as error:

        print(
            "\nMapService failed."
        )

        print(
            f"Error: {error}"
        )

        map_results = []

    # ==========================================================
    # 12. DISPLAY MAP INFORMATION
    # ==========================================================

    print(
        "\n--- Map Information ---"
    )

    print_json(
        map_results
    )

    # ==========================================================
    # 13. RESEARCH AGENT
    # ==========================================================

    print_section(
        "RESEARCHING DESTINATIONS"
    )
    valid_map_results = []

    for location in map_results:

        if not isinstance(location, dict):
            continue

        if not location.get("found", False):
            continue

        coordinates = location.get(
            "coordinates",
            {}
        )

        if not isinstance(coordinates, dict):
            continue

        if coordinates.get("latitude") is None:
            continue

        if coordinates.get("longitude") is None:
            continue

        valid_map_results.append(location)

    try:

        research_result = research_agent.research(
            destinations=candidates,
            preferences=mood_preferences,
            budget=budget_state,
            map_data=map_results
        )

    except Exception as error:

        print(
            "\nResearchAgent failed."
        )

        print(
            f"Error: {error}"
        )

        return

    # ==========================================================
    # 14. DISPLAY RESEARCH
    # ==========================================================

    print(
        "\n--- Research Information ---"
    )

    print_json(
        research_result
    )

    # ==========================================================
    # 15. FINAL GEMINI PASS
    # ==========================================================

    print_section(
        "GENERATING FINAL TRAVEL OPTIONS"
    )

    try:

        final_response = (
            travel_agent.ask(

                user_input=user_input,

                preferences=mood_preferences,

                budget=budget.get_status(),

                research=research_result,

                map_data=map_results,

                trip_information=trip_information
            )
        )

    except TypeError:

        # ------------------------------------------------------
        # Compatibility fallback for current TravelAgent.
        # ------------------------------------------------------

        try:

            final_response = (
                travel_agent.ask(

                    user_input=user_input,

                    preferences=mood_preferences,

                    budget=budget.get_status(),

                    research=research_result,

                    map_data=map_results
                )
            )

        except Exception as error:

            print(
                "\nFinal TravelAgent failed."
            )

            print(
                f"Error: {error}"
            )

            return

    except Exception as error:

        print(
            "\nFinal TravelAgent failed."
        )

        print(
            f"Error: {error}"
        )

        return

    # ==========================================================
    # 16. DISPLAY FINAL OPTIONS
    # ==========================================================

    print_section(
        "TRAVEL OPTIONS"
    )

    print(
        final_response
    )

    # ==========================================================
    # 17. USER DECISION
    # ==========================================================

    print_section(
        "WHAT WOULD YOU LIKE TO DO?"
    )

    print(
        "1. Continue with these options"
    )

    print(
        "2. Change something about the trip"
    )

    print(
        "3. Exit"
    )

    while True:

        choice = input(
            "\n> "
        ).strip()

        if choice == "1":

            print(
                "\nYour current travel options have been kept."
            )

            break

        elif choice == "2":

            print(
                "\nTrip modification mode will be "
                "connected to the refinement workflow next."
            )

            break

        elif choice == "3":

            print(
                "\nTravel planning ended."
            )

            return

        else:

            print(
                "Please choose 1, 2, or 3."
            )

    # ==========================================================
    # 18. CURRENT BUDGET
    # ==========================================================

    print_section(
        "CURRENT BUDGET"
    )

    print_json(
        budget.get_status()
    )


# ==============================================================
# PROGRAM ENTRY POINT
# ==============================================================

if __name__ == "__main__":

    main()