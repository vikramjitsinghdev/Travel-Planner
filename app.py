from flask import Flask, jsonify, request
from flask_cors import CORS

import main


# ==============================================================
# FLASK APPLICATION
# ==============================================================

app = Flask(__name__)

# Allow the frontend to communicate with Flask.
CORS(app)


# ==============================================================
# RESPONSE HELPERS
# ==============================================================

def success_response(data, status_code=200):
    """
    Return a successful JSON response.
    """

    return jsonify({
        "success": True,
        "data": data
    }), status_code


def error_response(
    message,
    status_code=500
):
    """
    Return a standardized JSON error response.
    """

    return jsonify({
        "success": False,
        "error": str(message)
    }), status_code


def get_json_data():
    """
    Safely retrieve JSON data from the request.
    """

    data = request.get_json(
        silent=True
    )

    if data is None:
        raise ValueError(
            "Request body must contain valid JSON."
        )

    if not isinstance(
        data,
        dict
    ):
        raise ValueError(
            "Request JSON must be an object."
        )

    return data


# ==============================================================
# HEALTH CHECK
# ==============================================================

@app.route(
    "/",
    methods=["GET"]
)
def home():
    """
    Basic server health check.
    """

    return success_response({
        "application": "Wanderlust",
        "status": "running"
    })


@app.route(
    "/api/health",
    methods=["GET"]
)
def health():
    """
    API health check.
    """

    return success_response({
        "status": "ok"
    })


# ==============================================================
# START AI TRAVEL PLANNER
# ==============================================================

@app.route(
    "/api/trip/start",
    methods=["POST"]
)
def start_trip():
    """
    Start the complete AI travel-planning workflow.

    Request:

        {
            "user_input":
                "I want a peaceful mountain vacation..."
        }

    app.py does NOT communicate with any AI agent directly.

    It simply sends the user's request to main.py.

    Flow:

        Frontend
            ↓
        app.py
            ↓
        main.py
            ↓
        MoodAgent
            ↓
        ResearchAgent
            ↓
        Worker 1 → Recheck
        Worker 2 → Recheck
        Worker 3 → Recheck
            ↓
        TravelAgent
            ↓
        StructureAgent
            ↓
        Final structured backend
            ↓
        app.py
            ↓
        Frontend
    """

    try:

        # ------------------------------------------------------
        # READ REQUEST
        # ------------------------------------------------------

        data = get_json_data()

        # ------------------------------------------------------
        # USER INPUT
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
        # MAIN WORKFLOW
        # ------------------------------------------------------

        result = main.run_travel_planner(
            user_input
        )

        # ------------------------------------------------------
        # VALIDATE MAIN RESULT
        # ------------------------------------------------------

        if not isinstance(
            result,
            dict
        ):
            raise RuntimeError(
                "main.py did not return a valid JSON object."
            )

        # ------------------------------------------------------
        # RETURN FINAL STRUCTURED BACKEND
        # ------------------------------------------------------

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
            error,
            500
        )


# ==============================================================
# OPTIONAL: DIRECT AI WORKFLOW ENDPOINT
# ==============================================================

@app.route(
    "/api/trip/plan",
    methods=["POST"]
)
def plan_trip():
    """
    Alias for /api/trip/start.

    This can be useful if the frontend eventually uses
    /api/trip/plan instead of /api/trip/start.
    """

    return start_trip()


# ==============================================================
# ERROR HANDLERS
# ==============================================================

@app.errorhandler(404)
def not_found(error):

    return error_response(
        "Endpoint not found.",
        404
    )


@app.errorhandler(405)
def method_not_allowed(error):

    return error_response(
        "HTTP method not allowed.",
        405
    )


@app.errorhandler(500)
def internal_server_error(error):

    return error_response(
        "Internal server error.",
        500
    )


# ==============================================================
# RUN SERVER
# ==============================================================

if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )