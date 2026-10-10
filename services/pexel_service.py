"""Pexels image search service."""
import os
import requests
from dotenv import load_dotenv


class PexelsService:
    BASE_URL = "https://api.pexels.com/v1"

    def __init__(self):
        load_dotenv()
        self.api_key = os.getenv("PEXELS_API_KEY")

    def search_destination(self, destination, country=None, per_page=4):
        if not self.api_key:
            return []
        query = ", ".join(part for part in [destination, country, "travel"] if part)
        response = requests.get(
            f"{self.BASE_URL}/search",
            headers={"Authorization": self.api_key},
            params={"query": query, "per_page": max(1, min(int(per_page), 10)), "orientation": "landscape"},
            timeout=15,
        )
        response.raise_for_status()
        photos = response.json().get("photos", [])
        return [
            {
                "id": photo.get("id"),
                "photographer": photo.get("photographer"),
                "alt": photo.get("alt"),
                "url": photo.get("url"),
                "image_url": (photo.get("src") or {}).get("large"),
                "large_url": (photo.get("src") or {}).get("large"),
                "medium_url": (photo.get("src") or {}).get("medium"),
                "photographer_url": photo.get("photographer_url"),
            }
            for photo in photos
            if (photo.get("src") or {}).get("large")
        ]
