import os
import requests

from database import (
    get_connection
)


PEXELS_API_KEY = os.getenv(
    "PEXELS_API_KEY"
)


PEXELS_URL = (
    "https://api.pexels.com/v1/search"
)


def get_destination_image(
    destination_name,
    country
):

    if not PEXELS_API_KEY:

        return None, None, None


    query = (
        f"{destination_name} "
        f"{country} travel"
    )


    try:

        response = requests.get(

            PEXELS_URL,

            headers={
                "Authorization":
                    PEXELS_API_KEY
            },

            params={
                "query": query,
                "orientation": "landscape",
                "per_page": 1
            },

            timeout=8

        )


        if response.status_code != 200:

            return None, None, None


        data = response.json()

        photos = data.get(
            "photos",
            []
        )


        if not photos:

            return None, None, None


        photo = photos[0]


        image_url = (
            photo
            .get("src", {})
            .get("large2x")
        )


        pexels_url = photo.get(
            "url"
        )


        photographer = photo.get(
            "photographer"
        )


        return (
            image_url,
            pexels_url,
            photographer
        )


    except Exception:

        return None, None, None


def preload_missing_images():

    connection = get_connection()

    cursor = connection.cursor()


    cursor.execute("""
        SELECT
            id,
            name,
            country

        FROM destinations

        WHERE image_url IS NULL
           OR image_url = ''
    """)


    destinations = cursor.fetchall()

    connection.close()


    for destination in destinations:

        image_url, pexels_url, photographer = (
            get_destination_image(
                destination["name"],
                destination["country"]
            )
        )


        if image_url:

            connection = get_connection()

            cursor = connection.cursor()


            cursor.execute("""
                UPDATE destinations

                SET
                    image_url = ?,
                    pexels_url = ?,
                    photo_credit = ?

                WHERE id = ?
            """, (

                image_url,
                pexels_url,
                photographer,
                destination["id"]

            ))


            connection.commit()

            connection.close()