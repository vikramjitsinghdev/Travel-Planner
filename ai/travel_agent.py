import json
import os

from dotenv import load_dotenv
from google import genai


class TravelAgent:
    """
    Main AI travel planning agent.

    TravelAgent is responsible for reasoning about the
    user's travel request using Gemini.

    It receives information from main.py.

    It does NOT communicate directly with MoodAgent
    or Budget.

    main.py acts as the controller between the systems.
    """

    def __init__(self):

        load_dotenv()

        api_key = os.getenv(
            "GEMINI_API_KEY"
        )

        if not api_key:
            raise ValueError(
                "GEMINI_API_KEY is not set in the .env file."
            )

        self.client = genai.Client(
            api_key=api_key
        )

        # Keep the Gemini model that is currently
        # working in your project.
        self.model = "gemini-3.6-flash"

    # ==========================================================
    # MAIN TRAVEL REQUEST
    # ==========================================================

    def ask(
        self,
        user_input,
        preferences,
        budget
    ):
        """
        Generate a travel recommendation using:

            1. Original user request
            2. MoodAgent interpretation
            3. Canonical mood categories
            4. Numerical mood scores
            5. Raw AI interpretation
            6. Current travel budget

        main.py passes all of this information.

        TravelAgent does not call MoodAgent or Budget itself.
        """

        # ------------------------------------------------------
        # Validate user input.
        # ------------------------------------------------------

        if not isinstance(
            user_input,
            str
        ):
            raise TypeError(
                "user_input must be a string."
            )

        # ------------------------------------------------------
        # Validate mood preferences.
        # ------------------------------------------------------

        if not isinstance(
            preferences,
            dict
        ):
            raise TypeError(
                "preferences must be a dictionary."
            )

        # ------------------------------------------------------
        # Validate budget.
        # ------------------------------------------------------

        if not isinstance(
            budget,
            dict
        ):
            raise TypeError(
                "budget must be a dictionary."
            )

        # ------------------------------------------------------
        # Convert the structured mood information to JSON.
        # ------------------------------------------------------

        preferences_json = json.dumps(
            preferences,
            indent=4
        )

        # ------------------------------------------------------
        # Convert the current budget information to JSON.
        # ------------------------------------------------------

        budget_json = json.dumps(
            budget,
            indent=4
        )

        # ------------------------------------------------------
        # Build the Gemini prompt.
        #
        # The original prompt structure is preserved.
        # Budget information is added as another input.
        # ------------------------------------------------------

        prompt = f"""
You are the main AI travel planning agent.

Your job is to understand the user's travel request
and provide useful travel recommendations.

You have received:

1. The ORIGINAL USER REQUEST.
2. A structured TRAVEL PREFERENCE PROFILE created
   by a separate AI interpretation system.
3. The CURRENT TRAVEL BUDGET maintained by the
   application's budget system.

The structured profile contains:

- wanted:
  Canonical preferences the user wants.

- avoid:
  Canonical preferences the user wants to avoid.

- scores:
  Numerical importance of those preferences.

- score_details:
  Additional information about the scoring.

- summary:
  A natural-language summary.

- raw_wanted:
  The original preference phrases extracted by
  the interpretation AI.

- raw_avoid:
  The original rejected preference phrases.

The budget information contains:

- total_budget:
  The user's original total travel budget.

- spent:
  The amount already allocated or spent.

- remaining:
  The amount currently remaining.

- currency:
  The currency being used.

- expenses:
  Current recorded expenses.

IMPORTANT:

The original user request is the ultimate source of truth.

The structured preference profile is supporting information.

If there is any disagreement between the original
request and the structured profile, carefully interpret
the original request and do not blindly follow the
structured profile.

Use the mood scores as preference-strength information.

Positive scores indicate desired characteristics.

Negative scores indicate characteristics the user wants
to avoid.

Do NOT treat a negative preference as something the user
wants.

For example:

    urban: -0.8

means the user wants to avoid urban environments.

------------------------------------------------------------
BUDGET RULES
------------------------------------------------------------

The current travel budget is an important planning
constraint.

Respect the user's remaining budget when making
recommendations.

For example, if the remaining budget is:

    1500 CAD

do not recommend an obviously expensive travel plan
that would require substantially more money.

The budget is currently being maintained by a separate
Budget class.

Do not modify the budget yourself.

Do not assume that a recommendation has been purchased.

Do not invent exact current prices.

Do not claim that a hotel, flight, activity, or
transportation option is currently available.

If exact costs are unknown, clearly state that they
will need to be verified through the future travel
research system.

If the budget appears restrictive, prioritize
destinations and travel styles that are more likely
to fit within the available budget.

If the budget is generous, do not automatically
recommend luxury travel unless it matches the user's
preferences.

------------------------------------------------------------
CURRENT TRAVEL BUDGET
------------------------------------------------------------

{budget_json}

------------------------------------------------------------
ORIGINAL USER REQUEST
------------------------------------------------------------

{user_input}

------------------------------------------------------------
STRUCTURED TRAVEL PREFERENCES
------------------------------------------------------------

{preferences_json}

------------------------------------------------------------
TASK
------------------------------------------------------------

Based on the original request, structured preferences,
mood scores, and current budget, recommend suitable
travel destinations.

For each destination, explain:

- Why it matches the user's preferences.
- Which desired characteristics it provides.
- Which avoided characteristics it may have.
- How well it appears to fit the current budget.
- Any important limitations or considerations.

Use the budget as a constraint rather than as a
destination preference.

For now, provide a basic travel recommendation.

Do not pretend that you performed live web searches,
Google Maps searches, hotel searches, flight searches,
or real-time availability checks.

Those capabilities will be added through a separate
research system later.

Do not invent precise live information such as
current hotel prices, current availability, flight
availability, or real-time transportation conditions.
"""

        # ------------------------------------------------------
        # Gemini request
        # ------------------------------------------------------

        response = self.client.interactions.create(
            model=self.model,
            input=prompt
        )

        return response.output_text