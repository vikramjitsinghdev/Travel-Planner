import json

from ai.mood_agent import MoodAgent
from ai.travel_agent import TravelAgent
from travel.budget import Budget


def print_section(title):
    """Print a formatted section heading."""

    print("\n" + "=" * 60)
    print(title)
    print("=" * 60)


def main():
    """
    Main controller for the AI Travel Planner.

    Current architecture:

        User
          ↓
        main.py
          │
          ├── MoodAgent
          │      ↓
          │   Groq
          │      ↓
          │   Preferences + Mood Scores
          │
          ├── Budget
          │      ↓
          │   Budget State
          │
          └── TravelAgent
                 ↓
              Gemini
                 ↓
          Travel Recommendation

    main.py is the communication layer.

    MoodAgent and TravelAgent do NOT communicate
    directly with each other.

    Budget also does NOT communicate directly with
    TravelAgent.
    """

    print("=" * 60)
    print("AI TRAVEL PLANNER")
    print("=" * 60)

    # ==========================================================
    # 1. GET USER TRAVEL REQUEST
    # ==========================================================

    user_input = input(
        "\nWhere would you like to travel?\n> "
    ).strip()

    if not user_input:
        print("\nPlease enter a travel request.")
        return

    # ==========================================================
    # 2. GET USER BUDGET
    # ==========================================================

    while True:

        budget_input = input(
            "\nWhat is your total travel budget in CAD?\n> "
        ).strip()

        try:

            total_budget = float(
                budget_input
            )

            if total_budget < 0:
                print(
                    "Budget cannot be negative."
                )
                continue

            break

        except ValueError:

            print(
                "Please enter a valid number."
            )

    # ==========================================================
    # 3. CREATE BUDGET OBJECT
    # ==========================================================

    budget = Budget(
        total_budget=total_budget,
        currency="CAD"
    )

    # ==========================================================
    # 4. CREATE MOOD AGENT
    # ==========================================================

    mood_agent = MoodAgent()

    print_section(
        "ANALYZING TRAVEL PREFERENCES"
    )

    # ----------------------------------------------------------
    # main.py sends the user input to MoodAgent.
    # ----------------------------------------------------------

    mood_preferences = mood_agent.interpret(
        user_input
    )

    # ==========================================================
    # 5. DISPLAY MOOD INFORMATION
    # ==========================================================

    print("\n--- Mood Analysis ---")

    print(
        json.dumps(
            mood_preferences,
            indent=4
        )
    )

    # ==========================================================
    # 6. DISPLAY INITIAL BUDGET
    # ==========================================================

    print("\n--- Initial Budget ---")

    print(
        json.dumps(
            budget.get_status(),
            indent=4
        )
    )

    # ==========================================================
    # 7. CREATE TRAVEL AGENT
    # ==========================================================

    travel_agent = TravelAgent()

    # ==========================================================
    # 8. GET CURRENT BUDGET STATE
    # ==========================================================

    budget_state = budget.get_status()

    # ==========================================================
    # 9. SEND EVERYTHING TO GEMINI
    # ==========================================================

    print_section(
        "GENERATING TRAVEL RECOMMENDATION"
    )

    travel_response = travel_agent.ask(
        user_input=user_input,

        preferences=mood_preferences,

        budget=budget_state
    )

    # ==========================================================
    # 10. DISPLAY GEMINI RESPONSE
    # ==========================================================

    print_section(
        "TRAVEL AGENT"
    )

    print(
        travel_response
    )

    # ==========================================================
    # 11. DISPLAY CURRENT BUDGET
    # ==========================================================

    print_section(
        "CURRENT BUDGET"
    )

    print(
        json.dumps(
            budget.get_status(),
            indent=4
        )
    )


if __name__ == "__main__":
    main()