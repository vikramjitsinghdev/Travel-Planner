from flask import (
    Flask,
    jsonify,
    request,
    render_template
)

import main


# ============================================================
# WANDERLUST FLASK APPLICATION
# ============================================================

app = Flask(
    __name__,
    template_folder="templates",
    static_folder="static"
)


# ============================================================
# INITIALIZE BACKEND
# ============================================================

try:

    main.initialize_systems()

    print(
        "Wanderlust backend initialized successfully."
    )

except Exception as error:

    print(
        "\nWARNING: Backend initialization failed."
    )

    print(
        f"Error: {error}"
    )

    print(
        "The Flask application will still start, "
        "but AI/database functionality may be unavailable.\n"
    )


# ============================================================
# RESPONSE HELPERS
# ============================================================

def success_response(data):
    """
    Standard successful API response.

    script.js already understands this format:

        {
            "status": "success",
            "data": ...
        }
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
    Standard error response.

    script.js already handles:

        {
            "status": "error",
            "message": "..."
        }
    """

    return jsonify({
        "status": "error",
        "message": str(message)
    }), status_code


def get_json_data():
    """
    Safely read a JSON object from the request body.
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


# ============================================================
# HOME PAGE
# ============================================================

@app.route(
    "/",
    methods=["GET"]
)
def home():

    return render_template(
        "index.html"
    )


# ============================================================
# HEALTH CHECK
# ============================================================

@app.route(
    "/api/health",
    methods=["GET"]
)
def health():

    return success_response({

        "message":
            "AI Travel Planner backend is running."

    })


# ============================================================
# HOME DESTINATIONS
# ============================================================

@app.route(
    "/api/destinations/home",
    methods=["GET"]
)
def home_destinations():

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

    except TypeError as error:

        return error_response(
            error,
            400
        )

    except Exception as error:

        print(
            f"HOME DESTINATIONS ERROR: {error}"
        )

        return error_response(
            "Unable to load home destinations."
        )


# ============================================================
# RANDOM DESTINATIONS
# ============================================================

@app.route(
    "/api/destinations/random",
    methods=["GET"]
)
def random_destinations():

    try:

        # ------------------------------------------------------
        # LIMIT
        # ------------------------------------------------------

        limit = request.args.get(
            "limit",
            default=6,
            type=int
        )

        if limit is None:
            limit = 6

        limit = max(
            1,
            min(
                limit,
                20
            )
        )

        # ------------------------------------------------------
        # OPTIONAL FILTERS
        # ------------------------------------------------------

        scope = request.args.get(
            "scope"
        )

        country = request.args.get(
            "country"
        )

        region = request.args.get(
            "region"
        )

        # ------------------------------------------------------
        # MAIN.PY
        # ------------------------------------------------------

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

        print(
            f"RANDOM DESTINATIONS ERROR: {error}"
        )

        return error_response(
            "Unable to load random destinations."
        )


# ============================================================
# DESTINATION SEARCH
# ============================================================

@app.route(
    "/api/destinations/search",
    methods=["POST"]
)
def search_destination():

    try:

        data = get_json_data()

        query = data.get(
            "query"
        )

        # ------------------------------------------------------
        # VALIDATE QUERY
        # ------------------------------------------------------

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

        # ------------------------------------------------------
        # MAIN.PY
        # ------------------------------------------------------

        result = (
            main.search_destination(
                query
            )
        )

        if not result:

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

        print(
            f"DESTINATION SEARCH ERROR: {error}"
        )

        return error_response(
            "Unable to search for the destination."
        )


# ============================================================
# DESTINATION DETAILS
# ============================================================

@app.route(
    "/api/destinations/<int:destination_id>",
    methods=["GET"]
)
def destination_details(
    destination_id
):

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

    except TypeError as error:

        return error_response(
            error,
            400
        )

    except Exception as error:

        print(
            f"DESTINATION DETAILS ERROR: {error}"
        )

        return error_response(
            "Unable to load destination details."
        )


# ============================================================
# SAVE BASIC TRIP INFORMATION
# ============================================================

@app.route(
    "/api/trip/basic-info",
    methods=["POST"]
)
def save_basic_information():

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

        # ------------------------------------------------------
        # MAIN.PY
        # ------------------------------------------------------

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

        print(
            f"SAVE BASIC TRIP ERROR: {error}"
        )

        return error_response(
            "Unable to save basic trip information."
        )


# ============================================================
# GET SAVED BASIC TRIP
# ============================================================

@app.route(
    "/api/trip/basic/<int:trip_id>",
    methods=["GET"]
)
def get_basic_trip(
    trip_id
):

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

    except TypeError as error:

        return error_response(
            error,
            400
        )

    except Exception as error:

        print(
            f"GET TRIP ERROR: {error}"
        )

        return error_response(
            "Unable to retrieve the trip."
        )


# ============================================================
# START AI TRIP PLANNING
# ============================================================

@app.route(
    "/api/trip/start",
    methods=["POST"]
)
def start_trip():

    try:

        data = get_json_data()

        # ------------------------------------------------------
        # VALIDATE TRIP ID
        # ------------------------------------------------------

        trip_id = data.get(
            "trip_id"
        )

        if trip_id is None:

            return error_response(
                "Missing required field: trip_id",
                400
            )

        try:

            trip_id = int(
                trip_id
            )

        except (
            TypeError,
            ValueError
        ):

            return error_response(
                "trip_id must be a valid integer.",
                400
            )

        if trip_id <= 0:

            return error_response(
                "trip_id must be greater than zero.",
                400
            )

        # ------------------------------------------------------
        # VALIDATE USER INPUT
        # ------------------------------------------------------

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

        # ------------------------------------------------------
        # MAIN.PY OWNS THE ENTIRE AI PIPELINE
        # ------------------------------------------------------
        #
        # app.py does NOT call:
        #
        #   MoodAgent
        #   TravelAgent
        #   ResearchAgent
        #   Ollama
        #   Gemini
        #
        # It simply passes the request to main.py.
        #
        # main.py:
        #
        #   User request
        #       ↓
        #   MoodAgent
        #       ↓
        #   Main Gemini
        #       ↓
        #   5 candidates
        #       ↓
        #   Research plan
        #       ↓
        #   ResearchAgent
        #       ↓
        #   3 Ollama workers
        #       ↓
        #   Evaluator
        #       ↓
        #   Main Gemini
        #       ↓
        #   3 final trips
        #
        # ------------------------------------------------------

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

        print(
            "\nSTART TRIP ERROR:"
        )

        print(
            error
        )

        return error_response(
            "Unable to complete travel planning. "
            "Please check the backend logs."
        )


# ============================================================
# UPDATE TRIP THROUGH CHAT
# ============================================================

@app.route(
    "/api/trip/update",
    methods=["POST"]
)
def update_trip():

    try:

        data = get_json_data()

        # ------------------------------------------------------
        # TRIP ID
        # ------------------------------------------------------

        trip_id = data.get(
            "trip_id"
        )

        if trip_id is None:

            return error_response(
                "trip_id is required.",
                400
            )

        try:

            trip_id = int(
                trip_id
            )

        except (
            TypeError,
            ValueError
        ):

            return error_response(
                "trip_id must be a valid integer.",
                400
            )

        # ------------------------------------------------------
        # CHANGE REQUEST
        # ------------------------------------------------------

        change_request = data.get(
            "change_request"
        )

        if not isinstance(
            change_request,
            str
        ):

            return error_response(
                "change_request must be a string.",
                400
            )

        change_request = (
            change_request.strip()
        )

        if not change_request:

            return error_response(
                "change_request is required.",
                400
            )

        # ------------------------------------------------------
        # MAIN.PY
        # ------------------------------------------------------

        result = (
            main.update_trip({

                "trip_id":
                    trip_id,

                "change_request":
                    change_request

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

        print(
            "\nUPDATE TRIP ERROR:"
        )

        print(
            error
        )

        return error_response(
            "Unable to update the trip. "
            "Please check the backend logs."
        )


# ============================================================
# SELECT TRIP
# ============================================================

@app.route(
    "/api/trip/select",
    methods=["POST"]
)
def select_trip():

    try:

        data = get_json_data()

        trip_id = data.get(
            "trip_id"
        )

        if trip_id is None:

            return error_response(
                "trip_id is required.",
                400
            )

        try:

            trip_id = int(
                trip_id
            )

        except (
            TypeError,
            ValueError
        ):

            return error_response(
                "trip_id must be a valid integer.",
                400
            )

        selected_index = data.get(
            "selected_index"
        )

        if selected_index is None:

            return error_response(
                "selected_index is required.",
                400
            )

        try:

            selected_index = int(
                selected_index
            )

        except (
            TypeError,
            ValueError
        ):

            return error_response(
                "selected_index must be a valid integer.",
                400
            )

        # ------------------------------------------------------
        # MAIN.PY
        # ------------------------------------------------------

        result = (
            main.select_trip({

                "trip_id":
                    trip_id,

                "selected_index":
                    selected_index

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

        print(
            "\nSELECT TRIP ERROR:"
        )

        print(
            error
        )

        return error_response(
            "Unable to select the trip."
        )


# ============================================================
# TRIP STATUS
# ============================================================

@app.route(
    "/api/trip/status",
    methods=["POST"]
)
def trip_status():

    try:

        data = get_json_data()

        trip_id = data.get(
            "trip_id"
        )

        if trip_id is None:

            return error_response(
                "trip_id is required.",
                400
            )

        try:

            trip_id = int(
                trip_id
            )

        except (
            TypeError,
            ValueError
        ):

            return error_response(
                "trip_id must be a valid integer.",
                400
            )

        result = (
            main.get_trip_status({

                "trip_id":
                    trip_id

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

        print(
            f"TRIP STATUS ERROR: {error}"
        )

        return error_response(
            "Unable to retrieve trip status."
        )


# ============================================================
# CONFIRM TRIP
# ============================================================

@app.route(
    "/api/trip/confirm",
    methods=["POST"]
)
def confirm_trip():

    try:

        data = get_json_data()

        trip_id = data.get(
            "trip_id"
        )

        if trip_id is None:

            return error_response(
                "trip_id is required.",
                400
            )

        try:

            trip_id = int(
                trip_id
            )

        except (
            TypeError,
            ValueError
        ):

            return error_response(
                "trip_id must be a valid integer.",
                400
            )

        result = (
            main.confirm_trip({

                "trip_id":
                    trip_id

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

        print(
            f"CONFIRM TRIP ERROR: {error}"
        )

        return error_response(
            "Unable to confirm the trip."
        )


# ============================================================
# CANCEL TRIP
# ============================================================

@app.route(
    "/api/trip/cancel",
    methods=["POST"]
)
def cancel_trip():

    try:

        data = get_json_data()

        trip_id = data.get(
            "trip_id"
        )

        if trip_id is None:

            return error_response(
                "trip_id is required.",
                400
            )

        try:

            trip_id = int(
                trip_id
            )

        except (
            TypeError,
            ValueError
        ):

            return error_response(
                "trip_id must be a valid integer.",
                400
            )

        result = (
            main.cancel_trip({

                "trip_id":
                    trip_id

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

        print(
            f"CANCEL TRIP ERROR: {error}"
        )

        return error_response(
            "Unable to cancel the trip."
        )


# ============================================================
# DELETE TRIP
# ============================================================

@app.route(
    "/api/trip/delete",
    methods=["POST"]
)
def delete_trip():

    try:

        data = get_json_data()

        trip_id = data.get(
            "trip_id"
        )

        if trip_id is None:

            return error_response(
                "trip_id is required.",
                400
            )

        try:

            trip_id = int(
                trip_id
            )

        except (
            TypeError,
            ValueError
        ):

            return error_response(
                "trip_id must be a valid integer.",
                400
            )

        result = (
            main.delete_trip({

                "trip_id":
                    trip_id

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

        print(
            f"DELETE TRIP ERROR: {error}"
        )

        return error_response(
            "Unable to delete the trip."
        )


# ============================================================
# 404 HANDLER
# ============================================================

@app.errorhandler(404)
def handle_not_found(error):

    # Keep normal frontend navigation working.
    if request.path.startswith("/api/"):

        return error_response(
            "API endpoint not found.",
            404
        )

    return render_template(
        "index.html"
    )


# ============================================================
# 405 HANDLER
# ============================================================

@app.errorhandler(405)
def handle_method_not_allowed(error):

    if request.path.startswith("/api/"):

        return error_response(
            "HTTP method is not allowed for this endpoint.",
            405
        )

    return error_response(
        "HTTP method is not allowed.",
        405
    )


# ============================================================
# GENERAL ERROR HANDLER
# ============================================================

@app.errorhandler(500)
def handle_internal_error(error):

    print(
        f"FLASK INTERNAL ERROR: {error}"
    )

    if request.path.startswith("/api/"):

        return error_response(
            "Internal server error.",
            500
        )

    return error_response(
        "Internal server error.",
        500
    )


# ============================================================
# RUN APPLICATION
# ============================================================

if __name__ == "__main__":

    app.run(
        host="127.0.0.1",
        port=5000,
        debug=True
    )