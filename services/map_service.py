import os
import requests
from dotenv import load_dotenv


class MapService:
    """
    Centralized MapTiler service.

    The Travel Agent uses this class whenever it needs
    map/location information for a destination.

    The MapTiler API key is loaded from:

        MAPTILER_API_KEY

    The Travel Agent should NEVER access the API key directly.
    """

    BASE_URL = "https://api.maptiler.com"

    def __init__(self):
        load_dotenv()

        api_key = os.getenv("MAPTILER_API_KEY")

        if not api_key:
            raise ValueError(
                "MAPTILER_API_KEY was not found in the environment variables."
            )

        self.api_key = api_key

    # =========================================================
    # GEOCODING
    # =========================================================

    def geocode(self, location):
        """
        Convert a destination name into geographic coordinates.

        Args:
            location (str):
                Destination name, city, or place.

        Returns:
            dict:
                {
                    "name": "...",
                    "latitude": ...,
                    "longitude": ...
                }
        """

        if not location or not location.strip():
            raise ValueError(
                "Location cannot be empty."
            )

        url = f"{self.BASE_URL}/geocoding/{location.strip()}.json"

        params = {
            "key": self.api_key,
            "limit": 1
        }

        response = requests.get(
            url,
            params=params,
            timeout=10
        )

        response.raise_for_status()

        data = response.json()

        features = data.get("features", [])

        if not features:
            return None

        feature = features[0]

        coordinates = feature.get("center")

        if not coordinates or len(coordinates) < 2:
            return None

        return {
            "name": feature.get("place_name", location.strip()),
            "longitude": coordinates[0],
            "latitude": coordinates[1]
        }

    # =========================================================
    # STATIC MAP
    # =========================================================

    def get_static_map(
        self,
        longitude,
        latitude,
        zoom=10,
        width=800,
        height=500
    ):
        """
        Generate a MapTiler static map URL.

        Args:
            longitude (float):
                Longitude of the destination.

            latitude (float):
                Latitude of the destination.

            zoom (int):
                Map zoom level.

            width (int):
                Image width.

            height (int):
                Image height.

        Returns:
            str:
                Static map URL.
        """

        return (
            f"{self.BASE_URL}/maps/streets-v2/"
            f"static/"
            f"{longitude},{latitude},{zoom}/"
            f"{width}x{height}.png"
            f"?key={self.api_key}"
        )

    # =========================================================
    # DESTINATION MAP
    # =========================================================

    def get_destination_map(
        self,
        destination,
        zoom=10,
        width=800,
        height=500
    ):
        """
        Geocode a destination and generate its static map.

        Args:
            destination (str):
                Destination name.

        Returns:
            dict or None:
                {
                    "name": "...",
                    "latitude": ...,
                    "longitude": ...,
                    "map_url": "..."
                }
        """

        location = self.geocode(destination)

        if not location:
            return None

        map_url = self.get_static_map(
            longitude=location["longitude"],
            latitude=location["latitude"],
            zoom=zoom,
            width=width,
            height=height
        )

        return {
            "name": location["name"],
            "latitude": location["latitude"],
            "longitude": location["longitude"],
            "map_url": map_url
        }