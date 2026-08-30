from flask import (
    Flask,
    jsonify,
    request,
    render_template
)

import database
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
# DATABASE INITIALIZATION
# ==========================================================

database.initialize_database()


# ==========================================================
# RESPONSE HELPERS
# ==========================================================

def success_response(data):
    """
    Standard successful API response.
    """

    return jsonify({
        "status": "success",
        "data": data
    })


def error_response(
    message,
    status_code=500
):
    """
    Standard error API response.
    """

    return jsonify({
        "status": "error",
        "message": str(message)
    }), status_code


def get_json_data():
    """
    Read a JSON object from the request body.
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
    Serve the actual Wanderlust HTML page.

    IMPORTANT:

        Flask
            ↓
        templates/index.html
    """

    return render_template(
        "index.html"
    )


# ==========================================================
# HEALTH
# ==========================================================

@app.route(
    "/api/health",
    methods=["GET"]
)
def health():

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

    try:

        destinations = (
            database.get_home_destinations(
                5
            )
        )

        return success_response(
            destinations
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

    try:

        limit = request.args.get(
            "limit",
            default=6,
            type=int
        )

        if limit < 1:
            limit = 1

        if limit > 20:
            limit = 20

        destinations = (
            database.get_random_destinations(
                limit
            )
        )

        return success_response(
            destinations
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

    try:

        data = get_json_data()

        query = str(
            data.get(
                "query",
                ""
            )
        ).strip()

        if not query:

            return error_response(
                "Please enter a destination.",
                400
            )

        # --------------------------------------------------
        # DATABASE FIRST
        # --------------------------------------------------

        existing = (
            database.find_destination(
                query
            )
        )

        if existing:

            return success_response({

                "source":
                    "database",

                "destination":
                    existing

            })

        # --------------------------------------------------
        # LIVE MAP SEARCH
        # --------------------------------------------------

        result = main.search_destination(
            query
        )

        return success_response({

            "source":
                "live",

            "destination":
                result

        })

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
# DESTINATION DETAILS
# ==========================================================

@app.route(
    "/api/destinations/<int:destination_id>",
    methods=["GET"]
)
def destination_details(
    destination_id
):

    try:

        destination = (
            database.get_destination(
                destination_id
            )
        )

        if destination is None:

            return error_response(
                "Destination not found.",
                404
            )

        return success_response(
            destination
        )

    except Exception as error:

        return error_response(
            error
        )


# ==========================================================
# SAVE BASIC INFORMATION
# ==========================================================

@app.route(
    "/api/trip/basic-info",
    methods=["POST"]
)
def save_basic_information():
    """
    Save the basic trip information into SQLite.

    This is the ONLY place where the frontend needs
    to send the complete basic trip information.

    The server returns:

        trip_id
    """

    try:

        data = get_json_data()

        basic_information = (
            data.get(
                "basic_information"
            )
        )

        if not isinstance(
            basic_information,
            dict
        ):

            return error_response(
                "basic_information must be a JSON object.",
                400
            )

        trip_id = (
            database.create_trip(
                basic_information
            )
        )

        if trip_id is None:

            raise RuntimeError(
                "Database did not return a trip ID."
            )

        return success_response({

            "trip_id":
                trip_id,

            "basic_information":
                basic_information

        })

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
# GET BASIC INFORMATION
# ==========================================================

@app.route(
    "/api/trip/basic/<int:trip_id>",
    methods=["GET"]
)
def get_basic_trip(
    trip_id
):

    try:

        trip = database.get_trip(
            trip_id
        )

        if trip is None:

            return error_response(
                "Trip not found.",
                404
            )

        return success_response(
            trip
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
    Start the AI workflow.

    Plan Trip only sends:

        {
            "trip_id": 1,
            "user_input": "I want a peaceful trip..."
        }

    main.py retrieves all basic information from SQLite.
    """

    try:

        data = get_json_data()

        trip_id = data.get(
            "trip_id"
        )

        user_input = data.get(
            "user_input"
        )

        if trip_id is None:

            return error_response(
                "Missing required field: trip_id",
                400
            )

        if not isinstance(
            user_input,
            str
        ):

            return error_response(
                "user_input must be a string.",
                400
            )

        if not user_input.strip():

            return error_response(
                "Please describe what you want from your trip.",
                400
            )

        result = main.start_trip(
            trip_data={

                "trip_id":
                    trip_id,

                "user_input":
                    user_input.strip()

            }
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

    try:

        data = get_json_data()

        result = main.update_trip(
            trip_data=data
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
# SELECT TRIP
# ==========================================================

@app.route(
    "/api/trip/select",
    methods=["POST"]
)
def select_trip():

    try:

        data = get_json_data()

        result = main.select_trip(
            trip_data=data
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
# CONFIRM TRIP
# ==========================================================

@app.route(
    "/api/trip/confirm",
    methods=["POST"]
)
def confirm_trip():

    try:

        data = get_json_data()

        result = main.confirm_trip(
            trip_data=data
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
# CANCEL TRIP
# ==========================================================

@app.route(
    "/api/trip/cancel",
    methods=["POST"]
)
def cancel_trip():

    try:

        data = get_json_data()

        result = main.cancel_trip(
            trip_data=data
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
# TRIP STATUS
# ==========================================================

@app.route(
    "/api/trip/status",
    methods=["POST"]
)
def trip_status():

    try:

        data = get_json_data()

        result = main.get_trip_status(
            trip_data=data
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
# DELETE TRIP
# ==========================================================

@app.route(
    "/api/trip/delete",
    methods=["POST"]
)
def delete_trip():

    try:

        data = get_json_data()

        result = main.delete_trip(
            trip_data=data
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
# RUN FLASK
# ==========================================================

if __name__ == "__main__":

    app.run(
        host="127.0.0.1",
        port=5000,
        debug=True
    )