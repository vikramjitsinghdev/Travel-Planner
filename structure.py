import json

from typing import Dict, Any, List, Optional


class StructureAgent:
    """
    Structure Agent

    Responsibility:
        1. Receive the three verified worker results.
        2. Receive the three TravelAgent results.
        3. Match information belonging to the SAME destination.
        4. Combine the information.
        5. Preserve destination ordering.
        6. Return one clean structured JSON object for main.py.

    StructureAgent does NOT:
        - perform web searches
        - use Tavily
        - use Pexels
        - use MapTiler
        - call RecheckAgent
        - call Workers
        - retry workers
        - calculate budgets
        - generate destinations
        - modify researched information
        - generate new information

    The retry/recheck process is controlled by main.py.

    Input:

        verified_worker_results:

        [
            {
                "destination": "...",
                "country": "...",
                "major_attractions": [...],
                "traveling_cost": ...,
                "residence_cost": ...,
                "average_food_cost": ...,
                "daily_average_travel_cost": ...,
                "summary": "..."
            },
            ...
        ]

        travel_results:

        {
            "destinations": [
                {
                    "destination": "...",
                    "country": "...",
                    "basic_info": "...",
                    "images": [...],
                    "map_coordinates": {
                        "latitude": ...,
                        "longitude": ...
                    }
                },
                ...
            ]
        }

    Output:

        {
            "destinations": [
                {
                    "destination": "...",
                    "country": "...",
                    "research": {...},
                    "travel": {
                        "basic_info": "...",
                        "images": [...],
                        "map_coordinates": {...}
                    }
                },
                ...
            ]
        }
    """

    # =========================================================
    # PUBLIC METHOD
    # =========================================================

    def build(
        self,
        verified_worker_results: List[Dict[str, Any]],
        travel_results: Any
    ) -> Dict[str, Any]:
        """
        Combine verified worker information with TravelAgent
        information.

        Matching is performed using BOTH:

            destination
            country

        This prevents information from one destination from
        accidentally being attached to another destination.

        Args:
            verified_worker_results:
                Final PASS results from the workers/recheck loop.

            travel_results:
                Output from TravelAgent.

        Returns:
            Final structured JSON-compatible dictionary.
        """

        # -----------------------------------------------------
        # Validate inputs
        # -----------------------------------------------------

        self._validate_worker_results(
            verified_worker_results
        )

        travel_destinations = (
            self._extract_travel_destinations(
                travel_results
            )
        )

        self._validate_travel_results(
            travel_destinations
        )

        # -----------------------------------------------------
        # Create lookup table for TravelAgent results
        # -----------------------------------------------------

        travel_lookup = (
            self._create_destination_lookup(
                travel_destinations
            )
        )

        # -----------------------------------------------------
        # Combine results in worker/destination order
        # -----------------------------------------------------

        final_destinations = []

        for worker_result in verified_worker_results:

            destination = worker_result[
                "destination"
            ]

            country = worker_result[
                "country"
            ]

            key = self._make_destination_key(
                destination,
                country
            )

            travel_result = travel_lookup.get(
                key
            )

            if travel_result is None:

                raise ValueError(
                    "TravelAgent result not found for "
                    f"{destination}, {country}."
                )

            # -------------------------------------------------
            # Combine the two sources
            # -------------------------------------------------

            combined = self._combine_destination(
                worker_result=worker_result,
                travel_result=travel_result
            )

            final_destinations.append(
                combined
            )

        # -----------------------------------------------------
        # Final validation
        # -----------------------------------------------------

        self._validate_final_destinations(
            final_destinations
        )

        return {
            "destinations": final_destinations
        }

    # =========================================================
    # EXTRACT TRAVEL DESTINATIONS
    # =========================================================

    def _extract_travel_destinations(
        self,
        travel_results: Any
    ) -> List[Dict[str, Any]]:
        """
        Extract destination objects from TravelAgent output.

        Accepts either:

            {
                "destinations": [...]
            }

        or directly:

            [...]
        """

        if isinstance(
            travel_results,
            dict
        ):

            destinations = travel_results.get(
                "destinations"
            )

            if destinations is None:

                raise ValueError(
                    "TravelAgent result does not contain "
                    "'destinations'."
                )

            return destinations

        if isinstance(
            travel_results,
            list
        ):

            return travel_results

        raise TypeError(
            "travel_results must be either a dictionary "
            "or a list."
        )

    # =========================================================
    # WORKER RESULT VALIDATION
    # =========================================================

    def _validate_worker_results(
        self,
        worker_results: List[Dict[str, Any]]
    ) -> None:
        """
        Validate the final verified Worker/Recheck results.

        These should already have passed the RecheckAgent.
        """

        if not isinstance(
            worker_results,
            list
        ):

            raise TypeError(
                "verified_worker_results must be a list."
            )

        if len(worker_results) != 3:

            raise ValueError(
                "StructureAgent requires exactly "
                "3 verified worker results."
            )

        required_fields = [
            "destination",
            "country",
            "major_attractions",
            "traveling_cost",
            "residence_cost",
            "average_food_cost",
            "daily_average_travel_cost",
            "summary"
        ]

        seen = set()

        for index, result in enumerate(
            worker_results,
            start=1
        ):

            if not isinstance(
                result,
                dict
            ):

                raise TypeError(
                    f"Worker result {index} must be "
                    "a dictionary."
                )

            for field in required_fields:

                if field not in result:

                    raise ValueError(
                        f"Worker result {index} is missing "
                        f"field: {field}"
                    )

            destination = result[
                "destination"
            ]

            country = result[
                "country"
            ]

            if not isinstance(
                destination,
                str
            ) or not destination.strip():

                raise ValueError(
                    f"Worker result {index} has an "
                    "invalid destination."
                )

            if not isinstance(
                country,
                str
            ) or not country.strip():

                raise ValueError(
                    f"Worker result {index} has an "
                    "invalid country."
                )

            key = self._make_destination_key(
                destination,
                country
            )

            if key in seen:

                raise ValueError(
                    "Duplicate worker destination found: "
                    f"{destination}, {country}."
                )

            seen.add(
                key
            )

    # =========================================================
    # TRAVEL RESULT VALIDATION
    # =========================================================

    def _validate_travel_results(
        self,
        travel_destinations: List[Dict[str, Any]]
    ) -> None:
        """
        Validate TravelAgent's three destination results.
        """

        if not isinstance(
            travel_destinations,
            list
        ):

            raise TypeError(
                "TravelAgent destinations must be a list."
            )

        if len(travel_destinations) != 3:

            raise ValueError(
                "TravelAgent must provide exactly "
                "3 destinations."
            )

        required_fields = [
            "destination",
            "country",
            "basic_info",
            "images",
            "map_coordinates"
        ]

        seen = set()

        for index, result in enumerate(
            travel_destinations,
            start=1
        ):

            if not isinstance(
                result,
                dict
            ):

                raise TypeError(
                    f"TravelAgent destination {index} "
                    "must be a dictionary."
                )

            for field in required_fields:

                if field not in result:

                    raise ValueError(
                        f"TravelAgent destination {index} "
                        f"is missing field: {field}"
                    )

            destination = result[
                "destination"
            ]

            country = result[
                "country"
            ]

            key = self._make_destination_key(
                destination,
                country
            )

            if key in seen:

                raise ValueError(
                    "Duplicate TravelAgent destination found: "
                    f"{destination}, {country}."
                )

            seen.add(
                key
            )

    # =========================================================
    # DESTINATION LOOKUP
    # =========================================================

    def _create_destination_lookup(
        self,
        travel_destinations: List[Dict[str, Any]]
    ) -> Dict[str, Dict[str, Any]]:
        """
        Create a lookup dictionary:

            destination + country
                    ↓
            TravelAgent result
        """

        lookup = {}

        for result in travel_destinations:

            destination = result[
                "destination"
            ]

            country = result[
                "country"
            ]

            key = self._make_destination_key(
                destination,
                country
            )

            lookup[key] = result

        return lookup

    # =========================================================
    # DESTINATION KEY
    # =========================================================

    def _make_destination_key(
        self,
        destination: str,
        country: str
    ) -> str:
        """
        Create a normalized destination key.

        Both destination and country are used to ensure
        correct matching.
        """

        return (
            f"{destination.strip().lower()}|"
            f"{country.strip().lower()}"
        )

    # =========================================================
    # COMBINE DESTINATION
    # =========================================================

    def _combine_destination(
        self,
        worker_result: Dict[str, Any],
        travel_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Combine Worker/Recheck information with TravelAgent
        information for the SAME destination.

        Worker information:
            - major attractions
            - traveling cost
            - residence cost
            - food cost
            - local travel cost
            - research summary

        TravelAgent information:
            - basic information
            - images
            - coordinates
        """

        return {
            "destination": worker_result[
                "destination"
            ],

            "country": worker_result[
                "country"
            ],

            # -------------------------------------------------
            # Research/Recheck information
            # -------------------------------------------------

            "research": {
                "major_attractions": worker_result[
                    "major_attractions"
                ],

                "traveling_cost": worker_result[
                    "traveling_cost"
                ],

                "residence_cost": worker_result[
                    "residence_cost"
                ],

                "average_food_cost": worker_result[
                    "average_food_cost"
                ],

                "daily_average_travel_cost": worker_result[
                    "daily_average_travel_cost"
                ],

                "summary": worker_result[
                    "summary"
                ]
            },

            # -------------------------------------------------
            # TravelAgent information
            # -------------------------------------------------

            "travel": {
                "basic_info": travel_result[
                    "basic_info"
                ],

                "images": travel_result[
                    "images"
                ],

                "map_coordinates": travel_result[
                    "map_coordinates"
                ]
            }
        }

    # =========================================================
    # FINAL VALIDATION
    # =========================================================

    def _validate_final_destinations(
        self,
        destinations: List[Dict[str, Any]]
    ) -> None:
        """
        Validate the final structured output.
        """

        if len(destinations) != 3:

            raise RuntimeError(
                "Final structure must contain exactly "
                "3 destinations."
            )

        seen = set()

        for destination in destinations:

            name = destination.get(
                "destination"
            )

            country = destination.get(
                "country"
            )

            key = self._make_destination_key(
                name,
                country
            )

            if key in seen:

                raise RuntimeError(
                    "Final structure contains duplicate "
                    "destinations."
                )

            seen.add(
                key
            )

            if "research" not in destination:

                raise RuntimeError(
                    f"Missing research data for {name}."
                )

            if "travel" not in destination:

                raise RuntimeError(
                    f"Missing TravelAgent data for {name}."
                )

    # =========================================================
    # SAVE JSON
    # =========================================================

    def save_json(
        self,
        result: Dict[str, Any],
        file_path: str = "final_results.json"
    ) -> str:
        """
        Save the final structured result to a JSON file.
        """

        with open(
            file_path,
            "w",
            encoding="utf-8"
        ) as file:

            json.dump(
                result,
                file,
                indent=4,
                ensure_ascii=False
            )

        return file_path