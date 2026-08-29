import os
from urllib.parse import quote

import requests
from dotenv import load_dotenv


class MapService:
    """
    MapTiler-based geographic and mapping service.

    ============================================================
    ARCHITECTURE
    ============================================================

        main.py
           |
           v
       MapService
           |
           v
        MapTiler
           |
           v
    Geographic information
    """

    def __init__(
        self,
        api_key=None
    ):
        """
        Initialize MapTiler.

        The API key can be supplied directly or loaded from:

            MAPTILER_API_KEY

        in the .env file.
        """

        # ======================================================
        # LOAD ENVIRONMENT
        # ======================================================

        load_dotenv()

        # ======================================================
        # API KEY
        # ======================================================

        if api_key is None:

            api_key = os.getenv(
                "MAPTILER_API_KEY"
            )

        if not api_key:

            raise ValueError(
                "MAPTILER_API_KEY is not set "
                "in the .env file."
            )

        self.api_key = api_key

        # ======================================================
        # MAPTILER BASE URL
        # ======================================================

        self.base_url = (
            "https://api.maptiler.com"
        )

    # ==========================================================
    # INTERNAL GET REQUEST
    # ==========================================================

    def _get(
        self,
        endpoint,
        params=None
    ):
        """
        Perform a GET request to MapTiler.
        """

        if params is None:

            params = {}

        params = params.copy()

        params["key"] = self.api_key

        url = (
            f"{self.base_url}"
            f"{endpoint}"
        )

        response = requests.get(
            url,
            params=params,
            timeout=15
        )

        response.raise_for_status()

        return response.json()

    # ==========================================================
    # FORWARD GEOCODING
    # ==========================================================

    def geocode(
        self,
        location,
        limit=5,
        language="en"
    ):
        """
        Search for a location using MapTiler geocoding.

        Example:

            geocode("Zurich, Switzerland")
        """

        if not isinstance(
            location,
            str
        ):

            raise TypeError(
                "location must be a string."
            )

        location = location.strip()

        if not location:

            raise ValueError(
                "location cannot be empty."
            )

        encoded_location = quote(
            location,
            safe=""
        )

        endpoint = (
            f"/geocoding/"
            f"{encoded_location}.json"
        )

        params = {
            "limit": limit,
            "language": language
        }

        return self._get(
            endpoint,
            params
        )

    # ==========================================================
    # SIMPLIFIED LOCATION
    # ==========================================================

    def get_location(
        self,
        location
    ):
        """
        Return the best MapTiler result in a simplified format.

        This is the main location method used by main.py.
        """

        result = self.geocode(
            location,
            limit=1
        )

        features = result.get(
            "features",
            []
        )

        if not features:

            return {
                "query": location,
                "found": False,
                "name": None,
                "place_id": None,
                "latitude": None,
                "longitude": None,
                "country": None,
                "region": None,
                "place_type": None,
                "categories": []
            }

        feature = features[0]

        # ======================================================
        # COORDINATES
        # ======================================================

        geometry = feature.get(
            "geometry",
            {}
        )

        coordinates = geometry.get(
            "coordinates",
            []
        )

        longitude = None
        latitude = None

        if (
            isinstance(
                coordinates,
                list
            )
            and len(coordinates) >= 2
        ):

            longitude = coordinates[0]
            latitude = coordinates[1]

        # ======================================================
        # PROPERTIES
        # ======================================================

        properties = feature.get(
            "properties",
            {}
        )

        # ======================================================
        # CONTEXT
        # ======================================================

        context = feature.get(
            "context",
            []
        )

        country = None
        region = None

        for item in context:

            if not isinstance(
                item,
                dict
            ):

                continue

            kind = item.get(
                "kind"
            )

            value = (
                item.get("text")
                or item.get("name")
            )

            if kind == "country":

                country = value

            elif kind in (
                "region",
                "state"
            ):

                region = value

        # ======================================================
        # RESULT
        # ======================================================

        return {
            "query": location,

            "found": True,

            "name": (
                feature.get("text")
                or feature.get("place_name")
                or location
            ),

            "place_id": feature.get(
                "id"
            ),

            "latitude": latitude,

            "longitude": longitude,

            "country": (
                country
                or properties.get("country")
            ),

            "region": (
                region
                or properties.get("region")
            ),

            "place_type": (
                properties.get(
                    "place_designation"
                )
                or feature.get(
                    "place_type"
                )
            ),

            "categories": properties.get(
                "categories",
                []
            )
        }

    # ==========================================================
    # DESTINATION INFORMATION
    # ==========================================================

    def get_destination_info(
        self,
        destination
    ):
        """
        Get geographic information for a destination.

        This creates a clean structure for the rest of the
        application.
        """

        location = self.get_location(
            destination
        )

        return {
            "destination": destination,

            "found": location.get(
                "found",
                False
            ),

            "name": location.get(
                "name"
            ),

            "country": location.get(
                "country"
            ),

            "region": location.get(
                "region"
            ),

            "coordinates": {
                "latitude": location.get(
                    "latitude"
                ),

                "longitude": location.get(
                    "longitude"
                )
            },

            "place_id": location.get(
                "place_id"
            ),

            "place_type": location.get(
                "place_type"
            ),

            "categories": location.get(
                "categories",
                []
            )
        }

    # ==========================================================
    # MULTIPLE DESTINATIONS
    # ==========================================================

    def get_locations(
        self,
        locations
    ):
        """
        Get geographic information for multiple locations.

        Example:

            [
                "Vancouver, Canada",
                "Montreal, Canada",
                "Zurich, Switzerland"
            ]
        """

        if not isinstance(
            locations,
            list
        ):

            raise TypeError(
                "locations must be a list."
            )

        if not locations:

            return []

        results = []

        for location in locations:

            try:

                result = self.get_destination_info(
                    location
                )

                results.append(
                    result
                )

            except Exception as error:

                results.append(
                    {
                        "destination": location,
                        "found": False,
                        "error": str(error)
                    }
                )

        return results

    # ==========================================================
    # REVERSE GEOCODING
    # ==========================================================

    def reverse_geocode(
        self,
        longitude,
        latitude
    ):
        """
        Convert coordinates into geographic information.
        """

        if not isinstance(
            longitude,
            (int, float)
        ):

            raise TypeError(
                "longitude must be a number."
            )

        if not isinstance(
            latitude,
            (int, float)
        ):

            raise TypeError(
                "latitude must be a number."
            )

        endpoint = (
            f"/geocoding/"
            f"{longitude},{latitude}.json"
        )

        return self._get(
            endpoint
        )

    # ==========================================================
    # ROUTE
    # ==========================================================

    def get_route(
        self,
        start,
        destination,
        profile="driving"
    ):
        """
        Prepare geographic information for a route.

        NOTE:

        MapTiler geocoding gives us the coordinates needed
        to build a route, but actual routing should be connected
        to a routing API/service.

        This method therefore resolves both endpoints and
        returns their coordinates.

        Supported conceptual profiles:

            driving
            walking
            cycling

        """

        if not isinstance(
            start,
            str
        ):

            raise TypeError(
                "start must be a string."
            )

        if not isinstance(
            destination,
            str
        ):

            raise TypeError(
                "destination must be a string."
            )

        start_location = self.get_destination_info(
            start
        )

        destination_location = (
            self.get_destination_info(
                destination
            )
        )

        if not start_location.get(
            "found"
        ):

            raise ValueError(
                f"Could not locate start location: "
                f"{start}"
            )

        if not destination_location.get(
            "found"
        ):

            raise ValueError(
                f"Could not locate destination: "
                f"{destination}"
            )

        return {
            "start": start_location,

            "destination": destination_location,

            "profile": profile,

            "route_available": False,

            "message": (
                "Coordinates resolved. "
                "Connect a routing service for "
                "distance and travel-time calculations."
            )
        }

    # ==========================================================
    # MAP CONFIGURATION
    # ==========================================================

    def get_map_config(
        self,
        map_style="streets-v4"
    ):
        """
        Return MapTiler configuration for the frontend.

        This can later be used with MapLibre or another
        compatible map renderer.
        """

        style_url = (
            f"https://api.maptiler.com/"
            f"maps/{map_style}/style.json"
            f"?key={self.api_key}"
        )

        return {
            "provider": "MapTiler",

            "map_style": map_style,

            "style_url": style_url
        }

    # ==========================================================
    # 3D GLOBE DATA
    # ==========================================================

    def get_globe_coordinates(
        self,
        destination
    ):
        """
        Return coordinates in a simple structure suitable
        for future 3D globe visualization.
        """

        location = self.get_destination_info(
            destination
        )

        return {
            "destination": destination,

            "latitude": (
                location["coordinates"]["latitude"]
            ),

            "longitude": (
                location["coordinates"]["longitude"]
            ),

            "place_id": location.get(
                "place_id"
            ),

            "country": location.get(
                "country"
            )
        }