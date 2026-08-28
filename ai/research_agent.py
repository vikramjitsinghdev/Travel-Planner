import json
import os

from dotenv import load_dotenv
from ollama import Client


class ResearchAgent:
    """
    Local AI travel research agent.

    This agent uses an Ollama model to analyze and organize
    travel research information.

    IMPORTANT ARCHITECTURE:

        TravelAgent
             ↓
          main.py
             ↓
        ResearchAgent
             ↓
           Ollama

    ResearchAgent does NOT communicate directly with
    TravelAgent.

    main.py is responsible for passing information between
    the two agents.

    This class currently performs AI-based analysis of
    supplied research information.

    Actual web / Maps / hotel / travel API searching can
    be connected later.
    """

    def __init__(
        self,
        model="gemma4:latest",
        host=None
    ):
        """
        Initialize the local Ollama research agent.

        model:
            Ollama model used for research processing.

        host:
            Ollama server address.

            If no host is provided, the value from
            OLLAMA_HOST in the .env file is used.

            If OLLAMA_HOST is not set, the default
            localhost address is used.
        """

        # ------------------------------------------------------
        # Load environment variables.
        # ------------------------------------------------------

        load_dotenv()

        # ------------------------------------------------------
        # Get Ollama API key.
        # ------------------------------------------------------

        api_key = os.getenv(
            "OLLAMA_API_KEY"
        )

        if not api_key:

            raise ValueError(
                "OLLAMA_API_KEY is not set "
                "in the .env file."
            )

        # ------------------------------------------------------
        # Get Ollama model.
        #
        # The constructor value takes priority.
        # ------------------------------------------------------

        self.model = model

        # ------------------------------------------------------
        # Get Ollama host.
        # ------------------------------------------------------

        if host is None:

            host = os.getenv(
                "OLLAMA_HOST",
                "http://localhost:11434"
            )

        self.host = host

        # ------------------------------------------------------
        # Create Ollama client.
        #
        # The API key is passed through the Authorization
        # header.
        # ------------------------------------------------------

        self.client = Client(
            host=self.host,
            headers={
                "Authorization": (
                    f"Bearer {api_key}"
                )
            }
        )

    # ==========================================================
    # RESEARCH DESTINATIONS
    # ==========================================================

    def research(
        self,
        destinations,
        preferences=None,
        budget=None
    ):
        """
        Research a list of candidate destinations.

        Information is received from main.py.

        Example:

            destinations = [
                "Vancouver",
                "Montreal",
                "Seattle"
            ]

        preferences contains the output from MoodAgent.

        budget contains the current Budget state.

        Returns structured research information.
        """

        # ------------------------------------------------------
        # Validate destinations.
        # ------------------------------------------------------

        if not isinstance(
            destinations,
            list
        ):
            raise TypeError(
                "destinations must be a list."
            )

        if not destinations:

            raise ValueError(
                "At least one destination is required."
            )

        # ------------------------------------------------------
        # Default values.
        # ------------------------------------------------------

        if preferences is None:
            preferences = {}

        if budget is None:
            budget = {}

        # ------------------------------------------------------
        # Convert information into JSON.
        # ------------------------------------------------------

        preferences_json = json.dumps(
            preferences,
            indent=4
        )

        budget_json = json.dumps(
            budget,
            indent=4
        )

        destinations_json = json.dumps(
            destinations,
            indent=4
        )

        # ------------------------------------------------------
        # Build research prompt.
        # ------------------------------------------------------

        prompt = f"""
You are a local AI travel research assistant.

Your job is to research and organize information about
candidate travel destinations.

You are NOT the final travel planner.

Another AI agent is responsible for making the final
travel recommendation.

You have received candidate destinations through the
application's main controller.

------------------------------------------------------------
CANDIDATE DESTINATIONS
------------------------------------------------------------

{destinations_json}

------------------------------------------------------------
USER TRAVEL PREFERENCES
------------------------------------------------------------

{preferences_json}

------------------------------------------------------------
CURRENT TRAVEL BUDGET
------------------------------------------------------------

{budget_json}

------------------------------------------------------------
YOUR RESPONSIBILITIES
------------------------------------------------------------

For each candidate destination, identify useful information
that can help the main travel AI evaluate it.

Focus on:

- location
- country
- natural environment
- mountains
- beaches
- ocean/coast
- hiking
- activities
- nightlife
- urban environment
- crowd level
- relaxation
- accessibility
- general travel difficulty
- approximate travel characteristics
- potential budget considerations
- important limitations

Compare each destination against the user's preferences.

Pay particular attention to:

1. Wanted preferences.
2. Avoided preferences.
3. Current remaining budget.
4. Potential travel fatigue.

------------------------------------------------------------
IMPORTANT LIMITATIONS
------------------------------------------------------------

You are currently operating as a local Ollama model.

You do NOT have guaranteed live internet access.

Do NOT claim that you performed a live web search.

Do NOT invent current hotel prices.

Do NOT invent current flight prices.

Do NOT invent hotel availability.

Do NOT invent current crowd statistics.

Do NOT claim that information is real-time.

If information is unavailable, clearly mark it as
"unknown" rather than inventing it.

The application will eventually provide actual web,
Maps, hotel, flight, and travel API information to you.

------------------------------------------------------------
OUTPUT
------------------------------------------------------------

Return ONLY valid JSON.

Use this structure:

{{
    "destinations": [
        {{
            "name": "destination name",
            "country": "country",
            "overview": "short overview",

            "characteristics": {{
                "nature": "description",
                "mountains": "description",
                "beaches": "description",
                "ocean_coast": "description",
                "hiking": "description",
                "nightlife": "description",
                "urban": "description",
                "relaxation": "description",
                "crowds": "description"
            }},

            "activities": [],

            "accessibility": "description",

            "budget_notes": "description",

            "fatigue_notes": "description",

            "advantages": [],

            "limitations": []
        }}
    ]
}}

Do not provide a final ranking.

Do not choose the winner.

Your job is to provide useful research information
for the main TravelAgent.
"""

        # ------------------------------------------------------
        # Send request to Ollama.
        # ------------------------------------------------------

        response = self.client.chat(
            model=self.model,

            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a careful travel research "
                        "assistant. Return only valid JSON."
                    )
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],

            format="json"
        )

        # ------------------------------------------------------
        # Extract response.
        # ------------------------------------------------------

        content = response["message"]["content"]

        try:

            result = json.loads(
                content
            )

        except json.JSONDecodeError:

            raise ValueError(
                "Ollama returned invalid JSON."
            )

        return result

    # ==========================================================
    # RESEARCH ONE DESTINATION
    # ==========================================================

    def research_destination(
        self,
        destination,
        preferences=None,
        budget=None
    ):
        """
        Convenience method for researching a single
        destination.

        Internally uses research() so the application's
        research format remains consistent.
        """

        result = self.research(
            destinations=[
                destination
            ],

            preferences=preferences,

            budget=budget
        )

        return result