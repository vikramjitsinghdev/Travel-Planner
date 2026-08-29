import json

from travel.budget import Budget
from ai.travel_agent import TravelAgent


def print_section(title):
    """Print a formatted test section."""

    print("\n" + "=" * 60)
    print(title)
    print("=" * 60)


def test_budget_creation():
    """Test creation of a new travel budget."""

    print_section("TEST 1 — BUDGET CREATION")

    budget = Budget(
        total_budget=5000,
        currency="CAD"
    )

    status = budget.get_status()

    print(json.dumps(status, indent=4))

    assert status["total_budget"] == 5000.0
    assert status["spent"] == 0.0
    assert status["remaining"] == 5000.0
    assert status["currency"] == "CAD"

    print("\n✓ Budget creation test passed.")


def test_budget_expenses():
    """Test adding expenses and updating remaining budget."""

    print_section("TEST 2 — BUDGET EXPENSES")

    budget = Budget(
        total_budget=5000,
        currency="CAD"
    )

    print("\nInitial budget:")

    print(
        json.dumps(
            budget.get_status(),
            indent=4
        )
    )

    # ----------------------------------------------------------
    # Add hotel estimate
    # ----------------------------------------------------------

    budget.add_expense(
        amount=1200,
        category="hotel",
        description="7 nights"
    )

    # ----------------------------------------------------------
    # Add transportation estimate
    # ----------------------------------------------------------

    budget.add_expense(
        amount=800,
        category="transportation",
        description="Travel costs"
    )

    # ----------------------------------------------------------
    # Add activities estimate
    # ----------------------------------------------------------

    budget.add_expense(
        amount=300,
        category="activities",
        description="Activities and attractions"
    )

    status = budget.get_status()

    print("\nBudget after estimated expenses:")

    print(
        json.dumps(
            status,
            indent=4
        )
    )

    assert status["spent"] == 2300.0
    assert status["remaining"] == 2700.0

    print("\n✓ Budget expense test passed.")


def test_budget_affordability():
    """Test whether Budget correctly determines affordability."""

    print_section("TEST 3 — BUDGET AFFORDABILITY")

    budget = Budget(
        total_budget=5000,
        currency="CAD"
    )

    budget.add_expense(
        amount=2000,
        category="hotel",
        description="Accommodation"
    )

    print(
        f"\nRemaining budget: "
        f"{budget.get_remaining()} CAD"
    )

    affordable = budget.can_afford(
        1500
    )

    not_affordable = budget.can_afford(
        3500
    )

    print(
        f"Can afford 1500 CAD: "
        f"{affordable}"
    )

    print(
        f"Can afford 3500 CAD: "
        f"{not_affordable}"
    )

    assert affordable is True
    assert not_affordable is False

    print("\n✓ Budget affordability test passed.")


def test_budget_reset():
    """Test resetting the budget."""

    print_section("TEST 4 — BUDGET RESET")

    budget = Budget(
        total_budget=5000,
        currency="CAD"
    )

    budget.add_expense(
        amount=1500,
        category="hotel",
        description="Hotel"
    )

    print("\nBefore reset:")

    print(
        json.dumps(
            budget.get_status(),
            indent=4
        )
    )

    budget.reset()

    print("\nAfter reset:")

    print(
        json.dumps(
            budget.get_status(),
            indent=4
        )
    )

    status = budget.get_status()

    assert status["spent"] == 0.0
    assert status["remaining"] == 5000.0
    assert status["expenses"] == []

    print("\n✓ Budget reset test passed.")


def test_travel_agent_with_budget():
    """
    Test the communication between Budget and TravelAgent.

    main.py normally acts as the communication layer:

        Budget
           ↓
        main.py
           ↓
        TravelAgent
           ↓
        Gemini

    This test reproduces that communication.
    """

    print_section(
        "TEST 5 — TRAVEL AGENT + BUDGET"
    )

    # ----------------------------------------------------------
    # Create budget
    # ----------------------------------------------------------

    budget = Budget(
        total_budget=5000,
        currency="CAD"
    )

    # ----------------------------------------------------------
    # Simulate an existing estimated expense.
    # ----------------------------------------------------------

    budget.add_expense(
        amount=1000,
        category="transportation",
        description="Estimated transportation"
    )

    budget.add_expense(
        amount=1200,
        category="hotel",
        description="Estimated accommodation"
    )

    # ----------------------------------------------------------
    # Get current budget state.
    # ----------------------------------------------------------

    budget_state = budget.get_status()

    print("\nBudget state sent to TravelAgent:")

    print(
        json.dumps(
            budget_state,
            indent=4
        )
    )

    # ----------------------------------------------------------
    # Simulate MoodAgent output.
    #
    # We do not need to test MoodAgent here because it has
    # its own test.
    # ----------------------------------------------------------

    preferences = {
        "wanted": [
            "nature",
            "mountains",
            "relaxation"
        ],

        "avoid": [
            "crowded",
            "urban"
        ],

        "scores": {
            "nature": 1.0,
            "mountains": 1.0,
            "relaxation": 0.8,
            "crowded": -1.0,
            "urban": -0.8
        },

        "summary": (
            "User wants a peaceful natural "
            "mountain experience."
        ),

        "raw_wanted": [
            "nature",
            "mountains",
            "peaceful"
        ],

        "raw_avoid": [
            "crowded",
            "urban"
        ]
    }

    # ----------------------------------------------------------
    # Create TravelAgent.
    # ----------------------------------------------------------

    print(
        "\nInitializing TravelAgent..."
    )

    travel_agent = TravelAgent()

    print(
        "TravelAgent initialized."
    )

    # ----------------------------------------------------------
    # Test original user request.
    # ----------------------------------------------------------

    user_input = (
        "I want a peaceful mountain vacation "
        "with beautiful nature and relaxation, "
        "but I don't want crowded urban areas."
    )

    # ----------------------------------------------------------
    # Send information exactly like main.py does.
    # ----------------------------------------------------------

    print_section(
        "SENDING BUDGET + PREFERENCES TO GEMINI"
    )

    print("\nOriginal user request:")

    print(user_input)

    print("\nSending budget:")

    print(
        json.dumps(
            budget_state,
            indent=4
        )
    )

    print("\nSending preferences:")

    print(
        json.dumps(
            preferences,
            indent=4
        )
    )

    # ----------------------------------------------------------
    # Call TravelAgent.
    # ----------------------------------------------------------

    response = travel_agent.ask(
        user_input=user_input,

        preferences=preferences,

        budget=budget_state
    )

    # ----------------------------------------------------------
    # Validate response.
    # ----------------------------------------------------------

    print_section(
        "TRAVEL AGENT RESPONSE"
    )

    print(response)

    assert isinstance(
        response,
        str
    )

    assert len(
        response.strip()
    ) > 0

    print(
        "\n✓ TravelAgent successfully "
        "received the Budget state."
    )


def test_complete_budget_travel_workflow():
    """
    Test the basic workflow used by main.py.

        User
         ↓
        Budget
         ↓
        main.py
         ↓
        TravelAgent
         ↓
        Gemini
    """

    print_section(
        "TEST 6 — COMPLETE BUDGET/TRAVEL WORKFLOW"
    )

    # ----------------------------------------------------------
    # USER DATA
    # ----------------------------------------------------------

    user_input = (
        "I want a relaxing nature vacation "
        "with mountains and beautiful scenery. "
        "I want to avoid crowded cities."
    )

    # ----------------------------------------------------------
    # BUDGET
    # ----------------------------------------------------------

    budget = Budget(
        total_budget=6000,
        currency="CAD"
    )

    # ----------------------------------------------------------
    # Simulate estimated costs discovered during planning.
    # ----------------------------------------------------------

    budget.add_expense(
        amount=1500,
        category="transportation",
        description="Estimated travel cost"
    )

    budget.add_expense(
        amount=1800,
        category="hotel",
        description="Estimated accommodation"
    )

    budget.add_expense(
        amount=500,
        category="activities",
        description="Estimated activities"
    )

    budget_state = budget.get_status()

    print("\nCurrent budget state:")

    print(
        json.dumps(
            budget_state,
            indent=4
        )
    )

    # ----------------------------------------------------------
    # PREFERENCES
    # ----------------------------------------------------------

    preferences = {
        "wanted": [
            "nature",
            "mountains",
            "relaxation"
        ],

        "avoid": [
            "crowded",
            "urban"
        ],

        "scores": {
            "nature": 1.0,
            "mountains": 1.0,
            "relaxation": 0.8,
            "crowded": -1.0,
            "urban": -0.8
        }
    }

    # ----------------------------------------------------------
    # TRAVEL AGENT
    # ----------------------------------------------------------

    print(
        "\nInitializing TravelAgent..."
    )

    travel_agent = TravelAgent()

    print(
        "TravelAgent initialized."
    )

    # ----------------------------------------------------------
    # Send everything through the same interface that
    # main.py uses.
    # ----------------------------------------------------------

    response = travel_agent.ask(
        user_input=user_input,

        preferences=preferences,

        budget=budget_state
    )

    # ----------------------------------------------------------
    # DISPLAY RESULT
    # ----------------------------------------------------------

    print_section(
        "FINAL TRAVEL AGENT OUTPUT"
    )

    print(response)

    # ----------------------------------------------------------
    # VALIDATION
    # ----------------------------------------------------------

    assert isinstance(
        response,
        str
    )

    assert len(
        response.strip()
    ) > 0

    # ----------------------------------------------------------
    # Verify that Budget itself was not modified by
    # TravelAgent.
    #
    # TravelAgent receives a COPY of the budget state.
    # Budget remains controlled by main.py.
    # ----------------------------------------------------------

    final_budget = budget.get_status()

    assert final_budget["total_budget"] == 6000.0
    assert final_budget["spent"] == 3800.0
    assert final_budget["remaining"] == 2200.0

    print_section(
        "FINAL BUDGET STATE"
    )

    print(
        json.dumps(
            final_budget,
            indent=4
        )
    )

    print(
        "\n✓ Complete Budget/TravelAgent "
        "workflow test passed."
    )


def main():
    """Run the complete Budget + TravelAgent test suite."""

    print("=" * 60)
    print("BUDGET + TRAVEL AGENT TEST SUITE")
    print("=" * 60)

    print(
        """
Testing:

  • Budget creation
  • Budget expenses
  • Budget affordability
  • Budget reset
  • Budget → main.py → TravelAgent
  • Complete Budget/TravelAgent workflow

NOTE:
Tests 5 and 6 make real Gemini API requests.
"""
    )

    try:

        test_budget_creation()

        test_budget_expenses()

        test_budget_affordability()

        test_budget_reset()

        test_travel_agent_with_budget()

        test_complete_budget_travel_workflow()

    except AssertionError as error:

        print_section(
            "TEST FAILED"
        )

        print(
            f"Assertion failed: {error}"
        )

        return

    except Exception as error:

        print_section(
            "TEST FAILED"
        )

        print(
            f"Error: {error}"
        )

        return

    print_section(
        "ALL BUDGET + TRAVEL AGENT TESTS PASSED"
    )


if __name__ == "__main__":
    main()