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
# HOME PAGE
# ==========================================================

@app.route("/")
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
    Check whether Flask and the backend are running.
    """

    return jsonify({
        "status": "success",
        "message": (
            "AI Travel Planner backend is running."
        )
    })


# ==========================================================
# START TRIP
# ==========================================================

@app.route(
    "/api/trip/start",
    methods=["POST"]
)
def start_trip():
    """
    Start a new travel planning session.

    Frontend
        ↓
    app.py
        ↓
    main.start_trip()
        ↓
    AI / Map / Budget systems
    """

    try:

        data = request.get_json(
            silent=True
        )

        if not isinstance(
            data,
            dict
        ):

            return jsonify({
                "status": "error",
                "message": (
                    "Request body must contain "
                    "valid JSON."
                )
            }), 400

        result = main.start_trip(
            trip_data=data
        )

        return jsonify({
            "status": "success",
            "data": result
        })

    except Exception as error:

        return jsonify({
            "status": "error",
            "message": str(error)
        }), 500


# ==========================================================
# UPDATE TRIP
# ==========================================================

@app.route(
    "/api/trip/update",
    methods=["POST"]
)
def update_trip():
    """
    Change the requirements of an existing trip.
    """

    try:

        data = request.get_json(
            silent=True
        )

        if not isinstance(
            data,
            dict
        ):

            return jsonify({
                "status": "error",
                "message": (
                    "Request body must contain "
                    "valid JSON."
                )
            }), 400

        result = main.update_trip(
            trip_data=data
        )

        return jsonify({
            "status": "success",
            "data": result
        })

    except Exception as error:

        return jsonify({
            "status": "error",
            "message": str(error)
        }), 500


# ==========================================================
# SELECT TRIP
# ==========================================================

@app.route(
    "/api/trip/select",
    methods=["POST"]
)
def select_trip():
    """
    Select one of the candidate destinations.

    This creates a temporary detailed cost estimate.

    It does NOT commit the budget.
    """

    try:

        data = request.get_json(
            silent=True
        )

        if not isinstance(
            data,
            dict
        ):

            return jsonify({
                "status": "error",
                "message": (
                    "Request body must contain "
                    "valid JSON."
                )
            }), 400

        result = main.select_trip(
            trip_data=data
        )

        return jsonify({
            "status": "success",
            "data": result
        })

    except Exception as error:

        return jsonify({
            "status": "error",
            "message": str(error)
        }), 500


# ==========================================================
# CONFIRM TRIP
# ==========================================================

@app.route(
    "/api/trip/confirm",
    methods=["POST"]
)
def confirm_trip():
    """
    Confirm the selected trip.

    This is the point where temporary budget estimates
    become committed budget expenses.
    """

    try:

        data = request.get_json(
            silent=True
        )

        if not isinstance(
            data,
            dict
        ):

            return jsonify({
                "status": "error",
                "message": (
                    "Request body must contain "
                    "valid JSON."
                )
            }), 400

        result = main.confirm_trip(
            trip_data=data
        )

        return jsonify({
            "status": "success",
            "data": result
        })

    except Exception as error:

        return jsonify({
            "status": "error",
            "message": str(error)
        }), 500


# ==========================================================
# CANCEL TRIP
# ==========================================================

@app.route(
    "/api/trip/cancel",
    methods=["POST"]
)
def cancel_trip():
    """
    Cancel the current planning session.

    Temporary estimates are discarded.
    """

    try:

        data = request.get_json(
            silent=True
        )

        if not isinstance(
            data,
            dict
        ):

            return jsonify({
                "status": "error",
                "message": (
                    "Request body must contain "
                    "valid JSON."
                )
            }), 400

        result = main.cancel_trip(
            trip_data=data
        )

        return jsonify({
            "status": "success",
            "data": result
        })

    except Exception as error:

        return jsonify({
            "status": "error",
            "message": str(error)
        }), 500


# ==========================================================
# TRIP STATUS
# ==========================================================

@app.route(
    "/api/trip/status",
    methods=["POST"]
)
def trip_status():
    """
    Get the current state of a trip.
    """

    try:

        data = request.get_json(
            silent=True
        )

        if not isinstance(
            data,
            dict
        ):

            return jsonify({
                "status": "error",
                "message": (
                    "Request body must contain "
                    "valid JSON."
                )
            }), 400

        result = main.get_trip_status(
            trip_data=data
        )

        return jsonify({
            "status": "success",
            "data": result
        })

    except Exception as error:

        return jsonify({
            "status": "error",
            "message": str(error)
        }), 500


# ==========================================================
# DELETE TRIP SESSION
# ==========================================================

@app.route(
    "/api/trip/delete",
    methods=["POST"]
)
def delete_trip():
    """
    Delete a temporary trip planning session.
    """

    try:

        data = request.get_json(
            silent=True
        )

        if not isinstance(
            data,
            dict
        ):

            return jsonify({
                "status": "error",
                "message": (
                    "Request body must contain "
                    "valid JSON."
                )
            }), 400

        result = main.delete_trip(
            trip_data=data
        )

        return jsonify({
            "status": "success",
            "data": result
        })

    except Exception as error:

        return jsonify({
            "status": "error",
            "message": str(error)
        }), 500


# ==========================================================
# RUN APPLICATION
# ==========================================================

if __name__ == "__main__":

    app.run(
        host="127.0.0.1",
        port=5000,
        debug=True
    )