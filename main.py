# main.py

from mood.mood_keywords import MoodKeywords
from mood.mood_score import MoodScore
from travel.budget import BudgetManager


def get_float_input(prompt):
    """
    Safely gets a positive/zero floating-point number.
    """

    while True:

        try:

            value = float(
                input(prompt)
            )

            if value < 0:
                print(
                    "Please enter a number "
                    "greater than or equal to 0."
                )
                continue

            return value

        except ValueError:

            print(
                "Please enter a valid number."
            )


def get_int_input(
    prompt,
    minimum=1,
):
    """
    Safely gets an integer.
    """

    while True:

        try:

            value = int(
                input(prompt)
            )

            if value < minimum:

                print(
                    f"Please enter a number "
                    f"of at least {minimum}."
                )

                continue

            return value

        except ValueError:

            print(
                "Please enter a valid "
                "whole number."
            )


def collect_mood_preferences():
    """
    Collect and analyze the user's travel description.
    """

    print("\n")
    print("=" * 50)
    print("          TRAVEL MOOD")
    print("=" * 50)

    print(
        "\nDescribe the type of trip you want."
    )

    print(
        "You can write a complete paragraph."
    )

    print(
        "\nExample:"
    )

    print(
        "I want a peaceful trip surrounded by "
        "nature and mountains. I would like "
        "good food and some adventure, but I "
        "don't want a crowded or modern city."
    )

    print()

    user_input = input(
        "Your trip description:\n> "
    )

    # ------------------------------------------------------
    # Create mood keyword engine
    # ------------------------------------------------------

    mood_finder = MoodKeywords()

    # ------------------------------------------------------
    # Analyze the paragraph
    # ------------------------------------------------------

    # Split the paragraph into sentences.
    sentences = re_split_sentences(
        user_input
    )

    positive_moods = []
    negative_moods = []

    # ------------------------------------------------------
    # Analyze every sentence
    # ------------------------------------------------------

    for sentence in sentences:

        result = (
            mood_finder.analyze_sentence(
                sentence
            )
        )

        # Positive moods
        for mood in result["positive"]:

            if mood not in positive_moods:

                positive_moods.append(
                    mood
                )

        # Negative moods
        for mood in result["negative"]:

            if mood not in negative_moods:

                negative_moods.append(
                    mood
                )

    # ------------------------------------------------------
    # Display detected preferences
    # ------------------------------------------------------

    print(
        "\nDetected preferences:"
    )

    if positive_moods:

        print(
            "\nWanted:"
        )

        for rank, mood in enumerate(
            positive_moods,
            start=1,
        ):

            print(
                f"  {rank}. {mood}"
            )

    else:

        print(
            "\nNo positive moods detected."
        )

    if negative_moods:

        print(
            "\nRejected:"
        )

        for mood in negative_moods:

            print(
                f"  - {mood}"
            )

    return (
        positive_moods,
        negative_moods,
    )


def re_split_sentences(
    text,
):
    """
    Simple sentence splitter.

    This is intentionally basic for now.

    Later this can be replaced with a more advanced
    NLP sentence tokenizer.
    """

    import re

    sentences = re.split(
        r"[.!?]+",
        text,
    )

    return [
        sentence.strip()
        for sentence in sentences
        if sentence.strip()
    ]


def calculate_mood_scores(
    positive_moods,
    negative_moods,
    mood_finder,
):
    """
    Convert detected moods into the final percentage
    distribution.
    """

    print("\n")
    print("=" * 50)
    print("          MOOD CALCULATION")
    print("=" * 50)

    # ------------------------------------------------------
    # Create scorer
    # ------------------------------------------------------

    mood_scorer = MoodScore(
        mood_finder.get_moods()
    )

    # ------------------------------------------------------
    # Calculate percentages
    # ------------------------------------------------------

    percentages = (
        mood_scorer.calculate_scores(
            selected_moods=positive_moods,
            rejected_moods=negative_moods,
        )
    )

    # ------------------------------------------------------
    # Display
    # ------------------------------------------------------

    mood_scorer.display_scores(
        percentages
    )

    return percentages


def collect_budget():
    """
    Collect rough budget information from the user.
    """

    print("\n")
    print("=" * 50)
    print("          TRAVEL BUDGET")
    print("=" * 50)

    # ------------------------------------------------------
    # Create budget manager
    # ------------------------------------------------------

    budget = BudgetManager()

    # ------------------------------------------------------
    # Basic trip information
    # ------------------------------------------------------

    currency = input(
        "\nCurrency (CAD/USD/EUR/etc.): "
    ).strip()

    if currency:

        budget.set_currency(
            currency
        )

    total_budget = get_float_input(
        "Total travel budget: "
    )

    budget.set_total_budget(
        total_budget
    )

    travelers = get_int_input(
        "Number of travelers: "
    )

    budget.set_number_of_travelers(
        travelers
    )

    trip_days = get_int_input(
        "Number of trip days: "
    )

    budget.set_trip_days(
        trip_days
    )

    # ------------------------------------------------------
    # Expenses
    # ------------------------------------------------------

    print(
        "\nEnter your rough expected expenses."
    )

    print(
        "You can enter 0 if you don't know yet."
    )

    categories = [
        "transportation",
        "accommodation",
        "food",
        "activities",
        "shopping",
        "insurance",
        "miscellaneous",
        "emergency",
    ]

    for category in categories:

        amount = get_float_input(
            f"{category.capitalize()}: "
        )

        budget.set_expense(
            category,
            amount,
        )

    # ------------------------------------------------------
    # Display summary
    # ------------------------------------------------------

    budget.display_summary()

    return budget


def main():
    """
    Main application controller.

    Currently:

        1. Collect mood
        2. Analyze mood
        3. Calculate mood percentages
        4. Collect budget
        5. Display budget

    Later:

        6. Destination search
        7. Transportation
        8. Reviews
        9. Weather
        10. Itinerary
        11. Optimization
    """

    print("\n")
    print("=" * 60)
    print("           TRAVEL EXPERIENCE PLANNER")
    print("=" * 60)

    print(
        "\nLet's build your trip."
    )

    # ======================================================
    # STEP 1 — MOOD
    # ======================================================

    (
        positive_moods,
        negative_moods,
    ) = collect_mood_preferences()

    # Create the keyword engine again so it can be passed
    # to the scoring stage.
    mood_finder = MoodKeywords()

    # ======================================================
    # STEP 2 — MOOD SCORE
    # ======================================================

    mood_percentages = (
        calculate_mood_scores(
            positive_moods,
            negative_moods,
            mood_finder,
        )
    )

    # ======================================================
    # STEP 3 — BUDGET
    # ======================================================

    budget = collect_budget()

    # ======================================================
    # CURRENT SUMMARY
    # ======================================================

    print("\n")
    print("=" * 60)
    print("              TRIP PROFILE")
    print("=" * 60)

    print(
        "\nMOOD PRIORITIES:"
    )

    for mood, percentage in sorted(
        mood_percentages.items(),
        key=lambda item: item[1],
        reverse=True,
    ):

        if percentage > 0:

            print(
                f"  {mood:<22}"
                f"{percentage:>7.2f}%"
            )

    print(
        "\nBUDGET:"
    )

    print(
        f"  Total: "
        f"{budget.currency} "
        f"{budget.total_budget:.2f}"
    )

    print(
        f"  Remaining: "
        f"{budget.currency} "
        f"{budget.get_remaining_budget():.2f}"
    )

    print(
        f"  Trip length: "
        f"{budget.trip_days} days"
    )

    print(
        f"  Travelers: "
        f"{budget.number_of_travelers}"
    )

    print(
        "\n"
        "The basic trip profile has been created."
    )

    print(
        "\nDestination searching and transportation "
        "optimization will be added next."
    )


# ==========================================================
# PROGRAM ENTRY POINT
# ==========================================================

if __name__ == "__main__":

    main()