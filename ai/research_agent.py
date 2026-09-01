import json
from concurrent.futures import ThreadPoolExecutor, as_completed

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

        research_preferences = {
            "wanted": preferences.get("wanted", []),
            "avoid": preferences.get("avoid", [])
        }

        max_workers = min(3, len(destinations))
        researched_destinations = [None] * len(destinations)

        def research_one(index, destination):

            print(
                f"\nResearching: {destination}"
            )

            location_data = self._find_map_data(
                destination,
                map_data
            )

            result = self._research_one(
                destination=destination,
                preferences=research_preferences,
                budget=budget,
                map_data=location_data
            )

            if location_data:

                result["location"] = {

                    "latitude":
                        location_data.get(
                            "coordinates", {}
                        ).get(
                            "latitude"
                        ),

                    "longitude":
                        location_data.get(
                            "coordinates", {}
                        ).get(
                            "longitude"
                        ),

                    "place_id":
                        location_data.get(
                            "place_id"
                        )
                }

            return index, result

        with ThreadPoolExecutor(
            max_workers=max_workers
        ) as executor:

            futures = [
                executor.submit(
                    research_one,
                    index,
                    destination
                )
                for index, destination
                in enumerate(destinations)
            ]

            for future in as_completed(futures):

                index, result = future.result()

                researched_destinations[index] = result

        researched_destinations = [
            result
            for result in researched_destinations
            if result is not None
        ]

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
            separators=(",", ":")
        )

        budget_json = json.dumps(
            budget,
            separators=(",", ":")
        )

        # ------------------------------------------------------
        # Build a compact prompt.
        # ------------------------------------------------------

        prompt = f"""
You are a compact travel research assistant.

DESTINATION:
{destination}

PREFERENCES:
{preferences_json}

BUDGET:
{budget_json}

MAP DATA:
{json.dumps(map_data, separators=(",", ":"))}

Provide concise supporting information for the MAIN travel planner.
You are not the final decision maker.

Cover:
- general character/location
- nature, mountains, beaches/coast
- hiking and activities
- nightlife/urban environment
- relaxation/crowds
- accessibility/transportation
- accommodation
- budget considerations
- travel effort/fatigue
- advantages and limitations

Do not create an itinerary.
Do not claim live prices, bookings, availability, or live web research.
Do not invent missing facts. Use "unknown".
Return ONLY valid JSON:

{{
  "name": "{destination}",
  "country": "country or unknown",
  "overview": "short",
  "characteristics": {{
    "nature": "short",
    "mountains": "short",
    "beaches": "short",
    "ocean_coast": "short",
    "hiking": "short",
    "nightlife": "short",
    "urban": "short",
    "relaxation": "short",
    "crowds": "short"
  }},
  "activities": [],
  "accessibility": "short",
  "transportation": "short",
  "accommodation": "short",
  "budget_notes": "short",
  "fatigue_notes": "short",
  "preference_match": "short",
  "advantages": [],
  "limitations": []
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

            format="json",
            options={
                "temperature": 0.1,
                "num_predict": 700
            }
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