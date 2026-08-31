"""
Destination Search Service

IMPORTANT ARCHITECTURE RULE:

This module does NOT directly communicate with:

    - database.py
    - pexels.py
    - map.py
    - TravelAgent
    - ResearchAgent

main.py is the orchestration layer.
"""


# ==========================================================
# NORMALIZE QUERY
# ==========================================================

def normalize_query(
    query
):
    """
    Clean a destination search query.
    """

    if not isinstance(
        query,
        str
    ):

        raise TypeError(
            "Destination search query must be a string."
        )

    query = query.strip()

    if not query:

        raise ValueError(
            "Destination search query cannot be empty."
        )

    return query


# ==========================================================
# BUILD SEARCH REQUEST
# ==========================================================

def build_search_request(
    query
):
    """
    Create the internal search request.

    No external services are called here.
    """

    query = normalize_query(
        query
    )

    return {

        "query":
            query
    }


# ==========================================================
# NORMALIZE DATABASE RESULT
# ==========================================================

def normalize_database_results(
    results
):
    """
    Normalize results returned by main.py from SQLite.
    """

    if not isinstance(
        results,
        list
    ):

        return []

    normalized = []

    for destination in results:

        if not isinstance(
            destination,
            dict
        ):

            continue

        if not destination.get(
            "name"
        ):

            continue

        item = dict(
            destination
        )

        item.setdefault(
            "source",
            "database"
        )

        normalized.append(
            item
        )

    return normalized


# ==========================================================
# NORMALIZE LIVE RESULT
# ==========================================================

def normalize_live_result(
    result
):
    """
    Normalize a MapTiler result supplied by main.py.
    """

    if not isinstance(
        result,
        dict
    ):

        return None

    if not result.get(
        "found",
        False
    ):

        return None

    normalized = dict(
        result
    )

    normalized[
        "source"
    ] = "maptiler"

    return normalized


# ==========================================================
# BUILD FINAL RESULT
# ==========================================================

def build_search_result(
    query,
    database_results=None,
    live_result=None,
    image=None
):
    """
    Combine the information that main.py obtained from
    the various backend services.

    The actual communication with those services happens
    in main.py.
    """

    query = normalize_query(
        query
    )

    database_results = (
        normalize_database_results(
            database_results
        )
    )

    # ------------------------------------------------------
    # DATABASE RESULT
    # ------------------------------------------------------

    if database_results:

        return {

            "query":
                query,

            "source":
                "database",

            "results":
                database_results,

            "destination":
                database_results[0]
        }

    # ------------------------------------------------------
    # LIVE MAP RESULT
    # ------------------------------------------------------

    live_result = normalize_live_result(
        live_result
    )

    if live_result:

        destination = dict(
            live_result
        )

        # --------------------------------------------------
        # Add Pexels image information if main.py supplied it.
        # --------------------------------------------------

        if isinstance(
            image,
            dict
        ):

            if image.get(
                "image_url"
            ):

                destination[
                    "image_url"
                ] = image.get(
                    "image_url"
                )

            if image.get(
                "pexels_url"
            ):

                destination[
                    "pexels_url"
                ] = image.get(
                    "pexels_url"
                )

            if image.get(
                "photographer"
            ):

                destination[
                    "photo_credit"
                ] = image.get(
                    "photographer"
                )

        return {

            "query":
                query,

            "source":
                "live",

            "results":
                [destination],

            "destination":
                destination
        }

    # ------------------------------------------------------
    # NOTHING FOUND
    # ------------------------------------------------------

    return {

        "query":
            query,

        "source":
            None,

        "results":
            [],

        "destination":
            None
    }


# ==========================================================
# PUBLIC SEARCH FUNCTION
# ==========================================================

def search_destinations(
    query,
    database_results=None,
    live_result=None,
    image=None
):
    """
    Process a destination search.

    main.py supplies all external-service results.

    This function never contacts those services directly.
    """

    return build_search_result(

        query=query,

        database_results=
            database_results,

        live_result=
            live_result,

        image=
            image
    )