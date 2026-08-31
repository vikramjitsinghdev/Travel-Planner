import os
import requests

from dotenv import load_dotenv


# ==========================================================
# ENVIRONMENT
# ==========================================================

load_dotenv()


PEXELS_API_KEY = os.getenv(
    "PEXELS_API_KEY"
)


PEXELS_URL = (
    "https://api.pexels.com/v1/search"
)


# ==========================================================
# SEARCH DESTINATION IMAGE
# ==========================================================

def get_destination_image(
    destination_name,
    country=None
):
    """
    Search Pexels for an image.

    This module does NOT communicate with database.py.

    main.py is responsible for deciding whether the image
    should be stored in SQLite.
    """

    if not PEXELS_API_KEY:

        return {

            "image_url":
                None,

            "pexels_url":
                None,

            "photographer":
                None
        }

    destination_name = str(
        destination_name or ""
    ).strip()

    country = str(
        country or ""
    ).strip()

    if not destination_name:

        return {

            "image_url":
                None,

            "pexels_url":
                None,

            "photographer":
                None
        }

    query_parts = [
        destination_name
    ]

    if country:

        query_parts.append(
            country
        )

    query_parts.append(
        "travel"
    )

    query = " ".join(
        query_parts
    )

    try:

        response = requests.get(

            PEXELS_URL,

            headers={
                "Authorization":
                    PEXELS_API_KEY
            },

            params={

                "query":
                    query,

                "orientation":
                    "landscape",

                "per_page":
                    1
            },

            timeout=8
        )

        if response.status_code != 200:

            return {

                "image_url":
                    None,

                "pexels_url":
                    None,

                "photographer":
                    None
            }

        data = response.json()

        photos = data.get(
            "photos",
            []
        )

        if not photos:

            return {

                "image_url":
                    None,

                "pexels_url":
                    None,

                "photographer":
                    None
            }

        photo = photos[0]

        image_url = (
            photo
            .get(
                "src",
                {}
            )
            .get(
                "large2x"
            )
        )

        return {

            "image_url":
                image_url,

            "pexels_url":
                photo.get(
                    "url"
                ),

            "photographer":
                photo.get(
                    "photographer"
                )
        }

    except Exception:

        return {

            "image_url":
                None,

            "pexels_url":
                None,

            "photographer":
                None
        }