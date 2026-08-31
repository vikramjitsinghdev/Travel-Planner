"""
Random Destination Service

IMPORTANT ARCHITECTURE RULE:

This module does NOT communicate directly with:

    - database.py
    - pexels.py
    - map.py
    - travel_agent.py
    - research_agent.py

main.py is the orchestration layer.

This module only prepares and normalizes random-destination
requests.
"""


# ==========================================================
# DEFAULTS
# ==========================================================

DEFAULT_RANDOM_COUNT = 6

MAX_RANDOM_COUNT = 20


# ==========================================================
# NORMALIZE COUNT
# ==========================================================

def normalize_count(
    count=DEFAULT_RANDOM_COUNT
):
    """
    Normalize the number of random destinations requested.
    """

    try:

        count = int(
            count
        )

    except (
        TypeError,
        ValueError
    ):

        count = DEFAULT_RANDOM_COUNT

    return max(
        1,
        min(
            count,
            MAX_RANDOM_COUNT
        )
    )


# ==========================================================
# BUILD RANDOM REQUEST
# ==========================================================

def build_random_request(
    count=DEFAULT_RANDOM_COUNT,
    scope=None,
    country=None,
    region=None
):
    """
    Build a clean random-destination request.

    This function does NOT access the database.

    main.py receives this request and decides which
    backend services should be called.
    """

    return {

        "count":
            normalize_count(
                count
            ),

        "scope":
            (
                str(scope).strip()
                if scope
                else None
            ),

        "country":
            (
                str(country).strip()
                if country
                else None
            ),

        "region":
            (
                str(region).strip()
                if region
                else None
            )
    }


# ==========================================================
# PREPARE RANDOM RESULTS
# ==========================================================

def prepare_random_results(
    destinations
):
    """
    Normalize destinations returned by main.py.

    The actual database operation is performed by main.py.

    This function simply makes sure the returned structure
    is consistent.
    """

    if not isinstance(
        destinations,
        list
    ):

        return []

    results = []

    for destination in destinations:

        if not isinstance(
            destination,
            dict
        ):

            continue

        name = destination.get(
            "name"
        )

        if not name:

            continue

        results.append(
            dict(destination)
        )

    return results


# ==========================================================
# PUBLIC FUNCTION
# ==========================================================

def get_random_destinations(
    count=DEFAULT_RANDOM_COUNT,
    scope=None,
    country=None,
    region=None,
    destinations=None
):
    """
    Prepare random destinations.

    IMPORTANT:

    `destinations` must be supplied by main.py.

    This function does NOT query SQLite.

    main.py is responsible for:

        database.py
            ↓
        random_destination.py
            ↓
        return result
    """

    request = build_random_request(

        count=count,

        scope=scope,

        country=country,

        region=region
    )

    if destinations is None:

        return {

            "request":
                request,

            "destinations":
                [],

            "message":
                "No destinations were supplied by main.py."
        }

    results = prepare_random_results(
        destinations
    )

    return {

        "request":
            request,

        "destinations":
            results
    }