import json

from ai.mood_agent import MoodAgent
from ai.travel_agent import TravelAgent
from ai.research_agent import ResearchAgent
from travel.budget import Budget


def print_section(title):
    """Print a formatted section heading."""

    print("\n" + "=" * 60)
    print(title)
    print("=" * 60)


def main():
    """
    Main controller for the AI Travel Planner.

    ============================================================
    ARCHITECTURE
    ============================================================

        User
          ↓
        main.py
          │
          ├── MoodAgent
          │      ↓
          │    Groq
          │      ↓
          │   Preferences
          │
          ├── Budget
          │      ↓
          │   Budget State
          │
          ↓
        TravelAgent
          ↓
        Gemini
          ↓
      Candidate Destinations
          ↓
        main.py
          ↓
      ResearchAgent
          ↓
        Ollama
          ↓
      Research Information
          ↓
        main.py
          ↓
      TravelAgent
          ↓
        Gemini
          ↓
      Final Recommendation

    ============================================================

    IMPORTANT:

    main.py is the communication layer.

    None of the AI agents communicate directly with each other.

        MoodAgent      ─┐
                        │
        Budget         ─┼──→ main.py
                        │
        TravelAgent    ─┤
                        │
        ResearchAgent  ─┘

    main.py decides what information is passed from one
    system to another.
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

        print(
            "\nPlease enter a travel request."
        )

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
    # 3. CREATE BUDGET
    # ==========================================================

    budget = Budget(
        total_budget=total_budget,
        currency="CAD"
    )

    # ==========================================================
    # 4. CREATE AI AGENTS
    # ==========================================================

    mood_agent = MoodAgent()

    travel_agent = TravelAgent()

    research_agent = ResearchAgent()

    # ==========================================================
    # 5. ANALYZE USER TRAVEL PREFERENCES
    # ==========================================================

    print_section(
        "ANALYZING TRAVEL PREFERENCES"
    )

    # ----------------------------------------------------------
    # main.py → MoodAgent
    # ----------------------------------------------------------

    mood_preferences = mood_agent.interpret(
        user_input
    )

    # ==========================================================
    # 6. DISPLAY MOOD ANALYSIS
    # ==========================================================

    print(
        "\n--- Mood Analysis ---"
    )

    print(
        json.dumps(
            mood_preferences,
            indent=4
        )
    )

    # ==========================================================
    # 7. GET CURRENT BUDGET
    # ==========================================================

    budget_state = budget.get_status()

    print(
        "\n--- Initial Budget ---"
    )

    print(
        json.dumps(
            budget_state,
            indent=4
        )
    )

    # ==========================================================
    # 8. GEMINI — FIND CANDIDATE DESTINATIONS
    # ==========================================================
    #
    # main.py sends:
    #
    #     user input
    #     mood preferences
    #     budget
    #
    # to TravelAgent.
    #
    # TravelAgent sends this to Gemini.
    #
    # Gemini returns:
    #
    #     candidate destinations
    #
    # TravelAgent does NOT send anything directly
    # to ResearchAgent.
    #
    # ==========================================================

    print_section(
        "SELECTING CANDIDATE DESTINATIONS"
    )

    candidate_result = travel_agent.find_candidates(
        user_input=user_input,

        preferences=mood_preferences,

        budget=budget_state
    )

    # ==========================================================
    # 9. DISPLAY CANDIDATES
    # ==========================================================

    print(
        "\n--- Gemini Candidate Destinations ---"
    )

    print(
        json.dumps(
            candidate_result,
            indent=4
        )
    )

    # ==========================================================
    # 10. EXTRACT DESTINATION NAMES
    # ==========================================================

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

            if name:

                candidates.append(
                    name
                )

        elif isinstance(
            candidate,
            str
        ):

            candidates.append(
                candidate
            )

    # ==========================================================
    # 11. VALIDATE CANDIDATES
    # ==========================================================

    if not candidates:

        print(
            "\nGemini did not return any candidate destinations."
        )

        print(
            "\nThe travel planning process cannot continue."
        )

        return

    # ==========================================================
    # 12. DISPLAY RESEARCH TARGETS
    # ==========================================================

    print(
        "\n--- Destinations Being Researched ---"
    )

    for destination in candidates:

        print(
            f"• {destination}"
        )

    # ==========================================================
    # 13. OLLAMA — RESEARCH DESTINATIONS
    # ==========================================================
    #
    # main.py now takes Gemini's candidates and gives them
    # to ResearchAgent.
    #
    # ResearchAgent communicates with Ollama.
    #
    # ResearchAgent does NOT communicate with TravelAgent.
    #
    # ==========================================================

    print_section(
        "RESEARCHING DESTINATIONS"
    )

    research_result = research_agent.research(
        destinations=candidates,

        preferences=mood_preferences,

        budget=budget_state
    )

    # ==========================================================
    # 14. DISPLAY RESEARCH
    # ==========================================================

    print(
        "\n--- Ollama Research ---"
    )

    print(
        json.dumps(
            research_result,
            indent=4
        )
    )

    # ==========================================================
    # 15. VALIDATE RESEARCH
    # ==========================================================

    if not isinstance(
        research_result,
        dict
    ):

        print(
            "\nResearchAgent returned an invalid result."
        )

        return

    researched_destinations = (
        research_result.get(
            "destinations",
            []
        )
    )

    if not researched_destinations:

        print(
            "\nResearchAgent did not return "
            "any research information."
        )

        return

    # ==========================================================
    # 16. FINAL GEMINI PASS
    # ==========================================================
    #
    # main.py now sends ALL relevant information back
    # to TravelAgent:
    #
    #     Original user request
    #     Mood preferences
    #     Current budget
    #     Ollama research
    #
    # TravelAgent sends this to Gemini.
    #
    # Gemini now makes the FINAL recommendation.
    #
    # ==========================================================

    print_section(
        "GENERATING FINAL TRAVEL RECOMMENDATION"
    )

    final_response = travel_agent.ask(
        user_input=user_input,

        preferences=mood_preferences,

        budget=budget_state,

        research=research_result
    )

    # ==========================================================
    # 17. DISPLAY FINAL RESULT
    # ==========================================================

    print_section(
        "TRAVEL AGENT"
    )

    print(
        final_response
    )

    # ==========================================================
    # 18. DISPLAY FINAL BUDGET
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