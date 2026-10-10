"""MapTiler geocoding and static-map service."""
import os
import requests
from urllib.parse import quote
from dotenv import load_dotenv


class MapService:
    BASE_URL = "https://api.maptiler.com"

    def __init__(self):
        load_dotenv()
        self.api_key = os.getenv("MAPTILER_API_KEY")

    def geocode(self, location):
        if not self.api_key or not location or not location.strip():
            return None
        url = f"{self.BASE_URL}/geocoding/{quote(location.strip(), safe=',')}.json"
        response = requests.get(url, params={"key": self.api_key, "limit": 1}, timeout=15)
        response.raise_for_status()
        features = response.json().get("features", [])
        if not features:
            return None
        feature = features[0]
        center = feature.get("center") or []
        if len(center) < 2:
            return None
        return {"name": feature.get("place_name", location), "longitude": center[0], "latitude": center[1]}

    def get_static_map(self, longitude, latitude, zoom=10, width=900, height=560):
        if not self.api_key:
            return None
        return (
            f"{self.BASE_URL}/maps/streets-v2/static/"
            f"{longitude},{latitude},{zoom}/{width}x{height}.png?key={self.api_key}"
        )

    def get_destination_map(self, destination, country=None):
        label = ", ".join(part for part in [destination, country] if part)
        location = self.geocode(label)
        if not location:
            return None
        return {
            **location,
            "map_url": self.get_static_map(location["longitude"], location["latitude"]),
        }
