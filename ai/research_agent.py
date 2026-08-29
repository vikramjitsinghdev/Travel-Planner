import json

from ollama import Client


class ResearchAgent:
    """
    Local AI travel research agent.

    Architecture:

        main.py
             ↓
        ResearchAgent
             ↓
           Ollama

    ResearchAgent does NOT communicate directly with
    TravelAgent, MoodAgent, Budget, or MapService.

    main.py is responsible for passing information
    between the systems.

    The agent researches candidate destinations one
    at a time to prevent large Ollama responses from
    being truncated.
    """

    def __init__(
        self,
        model="gemma4:latest",
        host="http://localhost:11434"
    ):
        """
        Initialize the Ollama research agent.
        """

        self.model = model

        self.client = Client(
            host=host
        )

    # ==========================================================
    # RESEARCH MULTIPLE DESTINATIONS
    # ==========================================================

    def research(
        self,
        destinations,
        preferences=None,
        budget=None,
        map_data=None
    ):
        """
        Research multiple candidate destinations.

        Each destination is researched separately.

        This prevents Ollama from having to generate one
        extremely large JSON response.

        Parameters:

            destinations:
                List of destination names.

            preferences:
                MoodAgent output.

            budget:
                Current Budget state.

            map_data:
                MapTiler results supplied by main.py.
        """

        # ------------------------------------------------------
        # Validate destinations
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
        # Default values
        # ------------------------------------------------------

        if preferences is None:
            preferences = {}

        if budget is None:
            budget = {}

        if map_data is None:
            map_data = []

        # ------------------------------------------------------
        # Research each destination separately
        # ------------------------------------------------------

        researched_destinations = []

        for destination in destinations:

            print(
                f"\nResearching: {destination}"
            )

            # --------------------------------------------------
            # Find matching MapTiler information.
            # --------------------------------------------------

            location_data = self._find_map_data(
                destination,
                map_data
            )

            # --------------------------------------------------
            # Research one destination.
            # --------------------------------------------------

            result = self._research_one(
                destination=destination,
                preferences=preferences,
                budget=budget,
                map_data=location_data
            )

            # --------------------------------------------------
            # Combine MapTiler data with Ollama research.
            #
            # MapTiler is authoritative for coordinates.
            # --------------------------------------------------

            if location_data:

                result["location"] = {
                    "latitude": location_data.get(
                        "coordinates",
                        {}
                    ).get(
                        "latitude"
                    ),

                    "longitude": location_data.get(
                        "coordinates",
                        {}
                    ).get(
                        "longitude"
                    ),

                    "place_id": location_data.get(
                        "place_id"
                    )
                }

            researched_destinations.append(
                result
            )

        # ------------------------------------------------------
        # Return one combined research object.
        # ------------------------------------------------------

        return {
            "destinations": researched_destinations
        }

    # ==========================================================
    # RESEARCH ONE DESTINATION
    # ==========================================================

    def _research_one(
        self,
        destination,
        preferences,
        budget,
        map_data=None
    ):
        """
        Research one destination using Ollama.

        Keeping the request small makes JSON generation
        much more reliable.
        """

        if map_data is None:
            map_data = {}

        preferences_json = json.dumps(
            preferences,
            indent=2
        )

        budget_json = json.dumps(
            budget,
            indent=2
        )

        # ------------------------------------------------------
        # Build a compact prompt.
        # ------------------------------------------------------

        prompt = f"""
You are a travel research assistant.

Research the following candidate destination:

DESTINATION:
{destination}

USER TRAVEL PREFERENCES:
{preferences_json}

CURRENT TRAVEL BUDGET:
{budget_json}

Your job is to provide useful information that another
AI travel planner can use to evaluate this destination.

Focus on:

- general location
- natural environment
- beaches
- ocean/coast
- mountains
- hiking
- nightlife
- urban environment
- relaxation
- crowd level
- activities
- accessibility
- transportation
- accommodation
- budget considerations
- travel fatigue
- advantages
- limitations
- how well it matches the user's preferences

IMPORTANT:

You are NOT the final travel planner.

Do NOT choose the final winner.

Do NOT create an itinerary.

Do NOT claim that you performed a live web search.

Do NOT invent current hotel prices.

Do NOT invent current flight prices.

Do NOT invent availability.

Do NOT claim that information is real-time.

If something is unknown, write "unknown".

Keep each description concise.

Return ONLY valid JSON.

Use EXACTLY this structure:

{{
    "name": "{destination}",
    "country": "country name or unknown",
    "overview": "short overview",

    "characteristics": {{
        "nature": "short description",
        "mountains": "short description",
        "beaches": "short description",
        "ocean_coast": "short description",
        "hiking": "short description",
        "nightlife": "short description",
        "urban": "short description",
        "relaxation": "short description",
        "crowds": "short description"
    }},

    "activities": [
        "activity 1",
        "activity 2",
        "activity 3"
    ],

    "accessibility": "short description",

    "transportation": "short description",

    "accommodation": "short description",

    "budget_notes": "short description",

    "fatigue_notes": "short description",

    "preference_match": "short description",

    "advantages": [
        "advantage 1",
        "advantage 2"
    ],

    "limitations": [
        "limitation 1",
        "limitation 2"
    ]
}}
"""

        # ------------------------------------------------------
        # Ask Ollama.
        # ------------------------------------------------------

        response = self.client.chat(
            model=self.model,

            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a careful travel research "
                        "assistant. Return ONLY valid JSON."
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
        # Extract content.
        # ------------------------------------------------------

        try:

            content = response["message"]["content"]

        except (
            KeyError,
            TypeError
        ):

            raise ValueError(
                f"Ollama returned an unexpected response "
                f"for {destination}."
            )

        # ------------------------------------------------------
        # Parse JSON.
        # ------------------------------------------------------

        try:

            result = json.loads(
                content
            )

        except json.JSONDecodeError as error:

            print(
                "\n--- RAW OLLAMA RESPONSE ---"
            )

            print(
                content
            )

            raise ValueError(
                f"Ollama returned invalid JSON for "
                f"{destination}: {error}"
            )

        # ------------------------------------------------------
        # Validate basic structure.
        # ------------------------------------------------------

        if not isinstance(
            result,
            dict
        ):
            raise ValueError(
                f"Ollama returned a non-object JSON "
                f"response for {destination}."
            )

        # ------------------------------------------------------
        # Ensure destination name exists.
        # ------------------------------------------------------

        result["name"] = destination

        return result

    # ==========================================================
    # FIND MAP DATA
    # ==========================================================

    def _find_map_data(
        self,
        destination,
        map_data
    ):
        """
        Find the MapTiler result corresponding to a
        destination.

        MapTiler data is passed through main.py.

        ResearchAgent does not call MapService itself.
        """

        if not isinstance(
            map_data,
            list
        ):
            return {}

        destination_lower = (
            str(destination)
            .strip()
            .lower()
        )

        for location in map_data:

            if not isinstance(
                location,
                dict
            ):
                continue

            query = str(
                location.get(
                    "destination",
                    ""
                )
            ).strip().lower()

            if query == destination_lower:

                return location

        # ------------------------------------------------------
        # Fallback: partial matching.
        # ------------------------------------------------------

        for location in map_data:

            if not isinstance(
                location,
                dict
            ):
                continue

            query = str(
                location.get(
                    "destination",
                    ""
                )
            ).strip().lower()

            if (
                destination_lower in query
                or query in destination_lower
            ):

                return location

        return {}

    # ==========================================================
    # RESEARCH ONE DESTINATION
    # ==========================================================

    def research_destination(
        self,
        destination,
        preferences=None,
        budget=None,
        map_data=None
    ):
        """
        Research a single destination.
        """

        return self.research(
            destinations=[
                destination
            ],

            preferences=preferences,

            budget=budget,

            map_data=map_data
        )