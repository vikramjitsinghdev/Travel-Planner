from flask import (
    Flask,
    jsonify,
    request,
    render_template
)

import main


# ==========================================================
# FLASK APPLICATION
# ==========================================================

app = Flask(
    __name__,
    template_folder="templates",
    static_folder="static"
)


# ==========================================================
# SYSTEM INITIALIZATION
# ==========================================================

try:

    main.initialize_systems()

except AttributeError:

    # If main.py does not expose initialize_systems(),
    # the application can still start.
    #
    # This keeps app.py from directly initializing the
    # database or other backend services.
    pass

except Exception as error:

    print(
        "Warning: system initialization failed:"
    )

    print(
        error
    )


# ==========================================================
# RESPONSE HELPERS
# ==========================================================

def success_response(
    data
):
    """
    Standard successful API response.
    """

    return jsonify({

        "status":
            "success",

        "data":
            data

    })


def error_response(
    message,
    status_code=500
):
    """
    Standard error API response.
    """

    return jsonify({

        "status":
            "error",

        "message":
            str(message)

    }), status_code


def get_json_data():
    """
    Read and validate a JSON object from the request body.
    """

    data = request.get_json(
        silent=True
    )

    if not isinstance(
        data,
        dict
    ):

        raise ValueError(
            "Request body must contain a valid JSON object."
        )

    return data


# ==========================================================
# HOME PAGE
# ==========================================================

@app.route(
    "/",
    methods=["GET"]
)
def home():
    """
    Serve the Wanderlust frontend.
    """

    return render_template(
        "index.html"
    )


# ==========================================================
# HEALTH CHECK
# ==========================================================

@app.route(
    "/api/health",
    methods=["GET"]
)
def health():
    """
    Check whether the Flask backend is running.
    """

    return success_response({

        "message":
            "AI Travel Planner backend is running."

    })


# ==========================================================
# HOME DESTINATIONS
# ==========================================================

@app.route(
    "/api/destinations/home",
    methods=["GET"]
)
def home_destinations():
    """
    Get destinations for the Wanderlust homepage.

    IMPORTANT:

        app.py
            ↓
        main.py
            ↓
        database.py / Pexels / etc.

    app.py does NOT communicate directly with the database.
    """

    try:

        result = (
            main.get_home_destinations()
        )

        return success_response(
            result
        )

    except ValueError as error:

        return error_response(
            error,
            400
        )

    except Exception as error:

        return error_response(
            error
        )


# ==========================================================
# RANDOM DESTINATIONS
# ==========================================================

@app.route(
    "/api/destinations/random",
    methods=["GET"]
)
def random_destinations():
    """
    Return randomized destinations.

    Optional query parameters:

        ?limit=6
        ?scope=domestic
        ?country=Canada
        ?region=Alberta

    Example:

        /api/destinations/random?limit=6
    """

    try:

        # --------------------------------------------------
        # LIMIT
        # --------------------------------------------------

        limit = request.args.get(
            "limit",
            default=6,
            type=int
        )

        if limit < 1:

            limit = 1

        if limit > 20:

            limit = 20

        # --------------------------------------------------
        # OPTIONAL FILTERS
        # --------------------------------------------------

        scope = request.args.get(
            "scope"
        )

        country = request.args.get(
            "country"
        )

        region = request.args.get(
            "region"
        )

        # --------------------------------------------------
        # MAIN CONTROLLER
        # --------------------------------------------------

        result = (
            main.get_random_destinations_for_trip({

                "count":
                    limit,

                "scope":
                    scope,

                "country":
                    country,

                "region":
                    region

            })
        )

        return success_response(
            result
        )

    except ValueError as error:

        return error_response(
            error,
            400
        )

    except TypeError as error:

        return error_response(
            error,
            400
        )

    except Exception as error:

        return error_response(
            error
        )


# ==========================================================
# DESTINATION SEARCH
# ==========================================================

@app.route(
    "/api/destinations/search",
    methods=["POST"]
)
def search_destination():
    """
    Search for a destination.

    Request:

        {
            "query": "Niagara Falls, Canada"
        }

    Architecture:

        app.py
            ↓
        main.py
            ↓
        search_destination.py
            ↓
        main.py
            ↓
        database.py
            ↓
        if necessary:
            MapTiler
            Pexels
            ↓
        main.py
            ↓
        app.py
    """

    try:

        data = get_json_data()

        # --------------------------------------------------
        # QUERY
        # --------------------------------------------------

        query = data.get(
            "query"
        )

        if not isinstance(
            query,
            str
        ):

            return error_response(
                "query must be a string.",
                400
            )

        query = query.strip()

        if not query:

            return error_response(
                "Please enter a destination.",
                400
            )

        # --------------------------------------------------
        # MAIN CONTROLLER
        # --------------------------------------------------

        result = (
            main.search_destination(
                query
            )
        )

        # --------------------------------------------------
        # NOTHING FOUND
        # --------------------------------------------------

        if not result:

            return error_response(
                "Destination not found.",
                404
            )

        destination = result.get(
            "destination"
        )

        if destination is None:

            return error_response(
                "Destination not found.",
                404
            )

        return success_response(
            result
        )

    except ValueError as error:

        return error_response(
            error,
            400
        )

    except TypeError as error:

        return error_response(
            error,
            400
        )

    except Exception as error:

        return error_response(
            error
        )


# ==========================================================
# DESTINATION DETAILS
# ==========================================================

@app.route(
    "/api/destinations/<int:destination_id>",
    methods=["GET"]
)
def destination_details(
    destination_id
):
    """
    Get complete information about a destination.

    app.py delegates the operation to main.py.
    """

    try:

        result = (
            main.get_destination(
                destination_id
            )
        )

        if result is None:

            return error_response(
                "Destination not found.",
                404
            )

        return success_response(
            result
        )

    except ValueError as error:

        return error_response(
            error,
            400
        )

    except Exception as error:

        return error_response(
            error
        )


# ==========================================================
# SAVE BASIC TRIP INFORMATION
# ==========================================================

@app.route(
    "/api/trip/basic-info",
    methods=["POST"]
)
def save_basic_information():
    """
    Save the user's basic trip information.

    Request:

        {
            "basic_information": {
                ...
            }
        }

    app.py sends the information to main.py.

    main.py decides how the database should be used.
    """

    try:

        data = get_json_data()

        basic_information = data.get(
            "basic_information"
        )

        if not isinstance(
            basic_information,
            dict
        ):

            return error_response(
                "basic_information must be a JSON object.",
                400
            )

        result = (
            main.create_trip(
                basic_information
            )
        )

        if result is None:

            raise RuntimeError(
                "main.py did not return a trip."
            )

        return success_response(
            result
        )

    except ValueError as error:

        return error_response(
            error,
            400
        )

    except TypeError as error:

        return error_response(
            error,
            400
        )

    except Exception as error:

        return error_response(
            error
        )


# ==========================================================
# GET BASIC TRIP INFORMATION
# ==========================================================

@app.route(
    "/api/trip/basic/<int:trip_id>",
    methods=["GET"]
)
def get_basic_trip(
    trip_id
):
    """
    Retrieve a saved trip.

    app.py → main.py → database.py
    """

    try:

        result = (
            main.get_trip(
                trip_id
            )
        )

        if result is None:

            return error_response(
                "Trip not found.",
                404
            )

        return success_response(
            result
        )

    except ValueError as error:

        return error_response(
            error,
            400
        )

    except Exception as error:

        return error_response(
            error
        )


# ==========================================================
# START AI TRIP
# ==========================================================

@app.route(
    "/api/trip/start",
    methods=["POST"]
)
def start_trip():
    """
    Start the AI travel-planning workflow.

    Expected request:

        {
            "trip_id": 1,
            "user_input":
                "I want a natural and peaceful trip."
        }

    app.py does NOT communicate with TravelAgent directly.

    Flow:

        Frontend
            ↓
        app.py
            ↓
        main.py
            ↓
        database
            ↓
        MoodAgent
            ↓
        TravelAgent
            ↓
        Research
            ↓
        MapService
            ↓
        Budget
    """

    try:

        data = get_json_data()

        # --------------------------------------------------
        # TRIP ID
        # --------------------------------------------------

        trip_id = data.get(
            "trip_id"
        )

        if trip_id is None:

            return error_response(
                "Missing required field: trip_id",
                400
            )

        # --------------------------------------------------
        # USER INPUT
        # --------------------------------------------------

        user_input = data.get(
            "user_input"
        )

        if not isinstance(
            user_input,
            str
        ):

            return error_response(
                "user_input must be a string.",
                400
            )

        user_input = user_input.strip()

        if not user_input:

            return error_response(
                "Please describe what you want from your trip.",
                400
            )

        # --------------------------------------------------
        # MAIN CONTROLLER
        # --------------------------------------------------

        result = (
            main.start_trip({

                "trip_id":
                    trip_id,

                "user_input":
                    user_input

            })
        )

        return success_response(
            result
        )

    except ValueError as error:

        return error_response(
            error,
            400
        )

    except TypeError as error:

        return error_response(
            error,
            400
        )

    except Exception as error:

        return error_response(
            error
        )


# ==========================================================
# UPDATE TRIP
# ==========================================================

@app.route(
    "/api/trip/update",
    methods=["POST"]
)
def update_trip():
    """
    Update an existing trip through main.py.
    """

    try:

        data = get_json_data()

        result = (
            main.update_trip(
                trip_data=data
            )
        )

        return success_response(
            result
        )

    except ValueError as error:

        return error_response(
            error,
            400
        )

    except TypeError as error:

        return error_response(
            error,
            400
        )

    except Exception as error:

        return error_response(
            error
        )


# ==========================================================
# SELECT TRIP
# ==========================================================

@app.route(
    "/api/trip/select",
    methods=["POST"]
)
def select_trip():
    """
    User selects one of the AI-generated destinations.
    """

    try:

        data = get_json_data()

        result = (
            main.select_trip(
                trip_data=data
            )
        )

        return success_response(
            result
        )

    except ValueError as error:

        return error_response(
            error,
            400
        )

    except TypeError as error:

        return error_response(
            error,
            400
        )

    except Exception as error:

        return error_response(
            error
        )


# ==========================================================
# CONFIRM TRIP
# ==========================================================

@app.route(
    "/api/trip/confirm",
    methods=["POST"]
)
def confirm_trip():
    """
    Confirm the currently selected trip.
    """

    try:

        data = get_json_data()

        result = (
            main.confirm_trip(
                trip_data=data
            )
        )

        return success_response(
            result
        )

    except ValueError as error:

        return error_response(
            error,
            400
        )

    except TypeError as error:

        return error_response(
            error,
            400
        )

    except Exception as error:

        return error_response(
            error
        )


# ==========================================================
# CANCEL TRIP
# ==========================================================

@app.route(
    "/api/trip/cancel",
    methods=["POST"]
)
def cancel_trip():
    """
    Cancel the current trip workflow.
    """

    try:

        data = get_json_data()

        result = (
            main.cancel_trip(
                trip_data=data
            )
        )

        return success_response(
            result
        )

    except ValueError as error:

        return error_response(
            error,
            400
        )

    except TypeError as error:

        return error_response(
            error,
            400
        )

    except Exception as error:

        return error_response(
            error
        )


# ==========================================================
# TRIP STATUS
# ==========================================================

@app.route(
    "/api/trip/status",
    methods=["POST"]
)
def trip_status():
    """
    Retrieve the current state of a trip.
    """

    try:

        data = get_json_data()

        result = (
            main.get_trip_status(
                trip_data=data
            )
        )

        return success_response(
            result
        )

    except ValueError as error:

        return error_response(
            error,
            400
        )

    except TypeError as error:

        return error_response(
            error,
            400
        )

    except Exception as error:

        return error_response(
            error
        )


# ==========================================================
# DELETE TRIP
# ==========================================================

@app.route(
    "/api/trip/delete",
    methods=["POST"]
)
def delete_trip():
    """
    Delete a trip through main.py.
    """

    try:

        data = get_json_data()

        result = (
            main.delete_trip(
                trip_data=data
            )
        )

        return success_response(
            result
        )

    except ValueError as error:

        return error_response(
            error,
            400
        )

    except TypeError as error:

        return error_response(
            error,
            400
        )

    except Exception as error:

        return error_response(
            error
        )


# ==========================================================
# RUN FLASK APPLICATION
# ==========================================================

if __name__ == "__main__":

    app.run(

        host="127.0.0.1",

        port=5000,

        debug=True

    )