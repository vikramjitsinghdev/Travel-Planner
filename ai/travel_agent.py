import json
import os

from dotenv import load_dotenv
from google import genai


class TravelAgent:
    """
    Main AI travel planning agent.

    TravelAgent uses Gemini for the main travel reasoning.

    It communicates ONLY through main.py.

    Architecture:

        main.py
            |
            +--> TravelAgent
            |       |
            |       +--> Gemini
            |
            +--> ResearchAgent
                    |
                    +--> Ollama

    TravelAgent does NOT directly communicate with:

        - MoodAgent
        - Budget
        - ResearchAgent

    main.py is responsible for passing information between
    all systems.
    """

    def __init__(self):

        load_dotenv()

        api_key = os.getenv(
            "GEMINI_API_KEY"
        )

        if not api_key:

            raise ValueError(
                "GEMINI_API_KEY is not set "
                "in the .env file."
            )

        self.client = genai.Client(
            api_key=api_key
        )

        # Gemini model currently used by the project.
        self.model = "gemini-3.6-flash"

    # ==========================================================
    # FIND CANDIDATE DESTINATIONS
    # ==========================================================

    def find_candidates(
        self,
        user_input,
        preferences,
        budget
    ):
        """
        First Gemini planning stage.

        Receives information from main.py:

            - Original user request
            - Mood preferences
            - Current budget

        Gemini then selects several candidate destinations.

        The candidates are returned to main.py.

        main.py will then send those candidates to
        ResearchAgent.

        TravelAgent does NOT communicate directly with
        ResearchAgent.
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

        if not user_input.strip():

            raise ValueError(
                "user_input cannot be empty."
            )

        # ------------------------------------------------------
        # Validate preferences.
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
        # Convert structured information to JSON.
        # ------------------------------------------------------

        preferences_json = json.dumps(
            preferences,
            indent=4
        )

        budget_json = json.dumps(
            budget,
            indent=4
        )

        # ------------------------------------------------------
        # Build candidate-generation prompt.
        # ------------------------------------------------------

        prompt = f"""
You are the main AI travel planning agent.

Your job in this stage is to identify suitable candidate
travel destinations that can later be researched by a
separate travel research system.

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

Prefer candidate destinations and travel styles that
could reasonably fit within the user's remaining budget.

Do not invent exact current prices.

Do not claim that flights, hotels, activities, or
transportation are currently available.

The ResearchAgent will later investigate the candidates.

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

Identify between 3 and 5 strong candidate destinations
for the user.

The candidates should be selected based on:

- User's original request.
- Wanted preferences.
- Avoided preferences.
- Mood scores.
- Current remaining budget.
- Desired travel experience.

Do NOT provide a final itinerary.

Do NOT perform live searches.

Do NOT claim that prices or availability are current.

Do NOT make the final destination decision.

The candidates will be researched by a separate
ResearchAgent before the final decision is made.

Return ONLY valid JSON.

Use exactly this structure:

{{
    "candidates": [
        {{
            "name": "Destination name",
            "country": "Country",
            "reason": "Short explanation of why this destination should be researched."
        }}
    ]
}}
"""

        # ------------------------------------------------------
        # Gemini request.
        # ------------------------------------------------------

        response = self.client.interactions.create(
            model=self.model,
            input=prompt
        )

        # ------------------------------------------------------
        # Extract Gemini output.
        # ------------------------------------------------------

        content = response.output_text

        # ------------------------------------------------------
        # Parse JSON.
        # ------------------------------------------------------

        try:

            result = json.loads(
                content
            )

        except json.JSONDecodeError as error:

            raise ValueError(
                "Gemini returned invalid JSON while "
                "generating candidate destinations."
            ) from error

        # ------------------------------------------------------
        # Validate top-level structure.
        # ------------------------------------------------------

        if not isinstance(
            result,
            dict
        ):

            raise ValueError(
                "Gemini candidate response must be "
                "a dictionary."
            )

        if "candidates" not in result:

            raise ValueError(
                "Gemini candidate response is missing "
                "'candidates'."
            )

        candidates = result["candidates"]

        if not isinstance(
            candidates,
            list
        ):

            raise ValueError(
                "'candidates' must be a list."
            )

        if not candidates:

            raise ValueError(
                "Gemini returned an empty candidate list."
            )

        # ------------------------------------------------------
        # Validate individual candidates.
        # ------------------------------------------------------

        for index, candidate in enumerate(
            candidates,
            start=1
        ):

            if not isinstance(
                candidate,
                dict
            ):

                raise ValueError(
                    f"Candidate {index} must be a dictionary."
                )

            if not candidate.get(
                "name"
            ):

                raise ValueError(
                    f"Candidate {index} is missing "
                    "'name'."
                )

            if not candidate.get(
                "country"
            ):

                raise ValueError(
                    f"Candidate {index} is missing "
                    "'country'."
                )

            if not candidate.get(
                "reason"
            ):

                raise ValueError(
                    f"Candidate {index} is missing "
                    "'reason'."
                )

        # ------------------------------------------------------
        # Return candidate information to main.py.
        # ------------------------------------------------------

        return result

    # ==========================================================
    # FINAL TRAVEL REQUEST
    # ==========================================================

    def ask(
        self,
        user_input,
        preferences,
        budget,
        research=None
    ):
        """
        Generate the final travel recommendation.

        main.py provides:

            1. Original user request
            2. Mood preferences
            3. Current budget
            4. ResearchAgent results

        ResearchAgent information is optional.

        If research is provided, Gemini uses it as
        supporting evidence for the final recommendation.

        TravelAgent does NOT communicate directly with
        ResearchAgent.
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

        if not user_input.strip():

            raise ValueError(
                "user_input cannot be empty."
            )

        # ------------------------------------------------------
        # Validate preferences.
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
        # Validate research.
        # ------------------------------------------------------

        if research is not None:

            if not isinstance(
                research,
                dict
            ):

                raise TypeError(
                    "research must be a dictionary."
                )

        # ------------------------------------------------------
        # Convert information to JSON.
        # ------------------------------------------------------

        preferences_json = json.dumps(
            preferences,
            indent=4
        )

        budget_json = json.dumps(
            budget,
            indent=4
        )

        research_json = json.dumps(
            research or {},
            indent=4
        )

        # ------------------------------------------------------
        # Build final Gemini prompt.
        #
        # Existing mood and budget structure is preserved.
        # Research is added as another information source.
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
4. TRAVEL RESEARCH INFORMATION from a separate
   research system.

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

The research information contains information
collected and organized by a separate research system.

IMPORTANT:

The original user request is the ultimate source of truth.

The structured travel preference profile is supporting
information.

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

The budget is maintained by a separate Budget class.

Do not modify the budget yourself.

Do not assume that a recommendation has been purchased.

Do not invent exact current prices.

Do not claim that a hotel, flight, activity, or
transportation option is currently available unless
that information is explicitly provided by the
research data.

If exact costs are unknown, clearly state that they
must be verified.

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
TRAVEL RESEARCH INFORMATION
------------------------------------------------------------

{research_json}

------------------------------------------------------------
RESEARCH RULES
------------------------------------------------------------

The research information comes from a separate
ResearchAgent.

If research information is provided:

- Use it as evidence when evaluating destinations.
- Prefer researched information over unsupported
  assumptions.
- Do not invent information that is missing.
- Clearly identify important unknowns.
- Use research to evaluate the user's preferences.
- Use research to evaluate potential budget issues.
- Use research to evaluate potential travel fatigue.
- Compare destinations using the information available.

The ResearchAgent is not responsible for making the
final travel decision.

You are responsible for the final reasoning and
recommendation.

If research information is empty:

- Provide a basic recommendation using the available
  user information.
- Do not pretend that live research was performed.

------------------------------------------------------------
TASK
------------------------------------------------------------

Based on the original request, structured preferences,
mood scores, current budget, and available research,
recommend the most suitable travel destinations.

For each recommended destination, explain:

- Why it matches the user's preferences.
- Which desired characteristics it provides.
- Which avoided characteristics it may have.
- How well it appears to fit the current budget.
- How well it fits the desired travel pace.
- Any important limitations or considerations.

Use the research information whenever available.

Do not simply repeat the research.

Reason about the research and use it to make the
final recommendation.

If multiple destinations are suitable, compare them
and explain the differences.

Do not claim that information is live unless the
research information explicitly identifies it as
live/current.

Do not invent precise live information such as:

- Current hotel prices.
- Current flight prices.
- Current hotel availability.
- Current flight availability.
- Real-time transportation conditions.

Provide a useful final travel recommendation.
"""

        # ------------------------------------------------------
        # Gemini request.
        # ------------------------------------------------------

        response = self.client.interactions.create(
            model=self.model,
            input=prompt
        )

        # ------------------------------------------------------
        # Return final Gemini response to main.py.
        # ------------------------------------------------------

        return response.output_text