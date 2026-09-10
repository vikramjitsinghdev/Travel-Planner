import os
import requests
from dotenv import load_dotenv


class PexelsService:
    """
    Centralized Pexels image search service.

    The Travel Agent uses this class whenever it needs
    images for a destination.

    The Pexels API key is loaded from:

        PEXELS_API_KEY

    The Travel Agent should NEVER access the API key directly.
    """

    BASE_URL = "https://api.pexels.com/v1"

    def __init__(self):
        load_dotenv()

        api_key = os.getenv("PEXELS_API_KEY")

        if not api_key:
            raise ValueError(
                "PEXELS_API_KEY was not found in the environment variables."
            )

        self.headers = {
            "Authorization": api_key
        }

    # =========================================================
    # SEARCH IMAGES
    # =========================================================

    def search(self, query, per_page=5, page=1):
        """
        Search Pexels for images.

        Args:
            query (str):
                Image search query.

            per_page (int):
                Number of images to return.

            page (int):
                Page number.

        Returns:
            list:
                List of image results.
        """

        if not query or not query.strip():
            raise ValueError(
                "Image search query cannot be empty."
            )

        params = {
            "query": query.strip(),
            "per_page": per_page,
            "page": page
        }

        response = requests.get(
            f"{self.BASE_URL}/search",
            headers=self.headers,
            params=params,
            timeout=10
        )

        response.raise_for_status()

        data = response.json()

        return data.get("photos", [])

    # =========================================================
    # SEARCH DESTINATION
    # =========================================================

    def search_destination(self, destination, per_page=5):
        """
        Search for images related to a travel destination.

        Args:
            destination (str):
                Destination name.

            per_page (int):
                Number of images to return.

        Returns:
            list:
                Clean image information for the destination.
        """

        if not destination or not destination.strip():
            raise ValueError(
                "Destination cannot be empty."
            )

        photos = self.search(
            query=destination,
            per_page=per_page
        )

        results = []

        for photo in photos:
            results.append({
                "id": photo.get("id"),
                "photographer": photo.get("photographer"),
                "alt": photo.get("alt"),
                "width": photo.get("width"),
                "height": photo.get("height"),
                "url": photo.get("url"),
                "image_url": photo.get("src", {}).get("original"),
                "large_url": photo.get("src", {}).get("large"),
                "medium_url": photo.get("src", {}).get("medium"),
                "small_url": photo.get("src", {}).get("small")
            })

        return results

    # =========================================================
    # GET ONE IMAGE
    # =========================================================

    def get_destination_image(self, destination):
        """
        Get the best available first image for a destination.

        Args:
            destination (str):
                Destination name.

        Returns:
            dict or None:
                Information about the selected image.
        """

        images = self.search_destination(
            destination=destination,
            per_page=1
        )

        if not images:
            return None

        return images[0]