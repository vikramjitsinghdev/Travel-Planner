from flask import (
    Flask,
    jsonify,
    request,
    render_template
)

import main
import database


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

    Browser
        ↓
    /
        ↓
    templates/index.html

    JavaScript inside index.html then communicates
    with the Flask API endpoints.
    """

    return render_template(
        "index.html"
    )


# ==========================================================
# HOME DESTINATIONS API
# ==========================================================

@app.route(
    "/api/destinations/home",
    methods=["GET"]
)
def home_destinations():
    """
    Return preloaded destinations for the homepage.

    This does NOT render HTML.

    It provides destination data to script.js.
    """

    try:

        destinations = (
            database.get_home_destinations(5)
        )

        return jsonify({
            "status": "success",
            "data": destinations
        })

    except Exception as error:

        return jsonify({
            "status": "error",
            "message": str(error)
        }), 500


# ==========================================================
# HEALTH
# ==========================================================

@app.route(
    "/api/health",
    methods=["GET"]
)
def health():

    return jsonify({
        "status": "success",
        "message": (
            "AI Travel Planner backend is running."
        )
    })

# ==========================================================
# RANDOM DESTINATIONS
# ==========================================================

@app.route(
    "/api/destinations/random",
    methods=["GET"]
)
def random_destinations():

    try:

        destinations = (
            database.get_random_destinations(6)
        )

        return jsonify({
            "status": "success",
            "data": destinations
        })

    except Exception as error:

        return jsonify({
            "status": "error",
            "message": str(error)
        }), 500
    
# ==========================================================
# SEARCH DESTINATION
# ==========================================================

# ==========================================================
# SEARCH DESTINATIONS
# ==========================================================

@app.route(
    "/api/destinations/search",
    methods=["GET"]
)
def search_destinations():

    query = request.args.get(
        "q",
        ""
    ).strip()


    if not query:

        return jsonify({
            "status": "success",
            "data": []
        })


    try:

        destinations = (
            database.search_destinations(
                query
            )
        )

        return jsonify({
            "status": "success",
            "data": destinations
        })

    except Exception as error:

        return jsonify({
            "status": "error",
            "message": str(error)
        }), 500

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

            return jsonify({
                "status": "error",
                "message": "Destination not found."
            }), 404


        return jsonify({
            "status": "success",
            "data": destination
        })


    except Exception as error:

        return jsonify({
            "status": "error",
            "message": str(error)
        }), 500

# ==========================================================
# SAVE BASIC TRIP INFORMATION
# ==========================================================

@app.route(
    "/api/trip/basic",
    methods=["POST"]
)
def save_basic_trip():

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
                "message":
                    "Invalid JSON data."
            }), 400


        required_fields = [
            "departure_location",
            "travelers",
            "duration_days",
            "travel_dates",
            "budget"
        ]


        for field in required_fields:

            if not str(
                data.get(field, "")
            ).strip():

                return jsonify({
                    "status": "error",
                    "message":
                        f"Missing required field: {field}"
                }), 400


        trip_id = database.create_trip(
            data
        )


        return jsonify({

            "status":
                "success",

            "data": {

                "trip_id":
                    trip_id,

                "trip":
                    database.get_trip(
                        trip_id
                    )

            }

        })


    except Exception as error:

        return jsonify({

            "status":
                "error",

            "message":
                str(error)

        }), 500

# ==========================================================
# START TRIP
# ==========================================================

@app.route(
    "/api/trip/start",
    methods=["POST"]
)
def start_trip():

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
                "message": "Invalid JSON."
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
# UPDATE
# ==========================================================

@app.route(
    "/api/trip/update",
    methods=["POST"]
)
def update_trip():

    try:

        data = request.get_json(
            silent=True
        ) or {}

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

@app.route(
    "/api/trip/basic/<int:trip_id>",
    methods=["GET"]
)
def get_basic_trip(
    trip_id
):

    trip = database.get_trip(
        trip_id
    )


    if trip is None:

        return jsonify({
            "status": "error",
            "message": "Trip not found."
        }), 404


    return jsonify({

        "status":
            "success",

        "data":
            trip

    })


# ==========================================================
# SELECT
# ==========================================================

@app.route(
    "/api/trip/select",
    methods=["POST"]
)
def select_trip():

    try:

        data = request.get_json(
            silent=True
        ) or {}

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
# CONFIRM
# ==========================================================

@app.route(
    "/api/trip/confirm",
    methods=["POST"]
)
def confirm_trip():

    try:

        data = request.get_json(
            silent=True
        ) or {}

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
# CANCEL
# ==========================================================

@app.route(
    "/api/trip/cancel",
    methods=["POST"]
)
def cancel_trip():

    try:

        data = request.get_json(
            silent=True
        ) or {}

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
# STATUS
# ==========================================================

@app.route(
    "/api/trip/status",
    methods=["POST"]
)
def trip_status():

    try:

        data = request.get_json(
            silent=True
        ) or {}

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
# DELETE
# ==========================================================

@app.route(
    "/api/trip/delete",
    methods=["POST"]
)
def delete_trip():

    try:

        data = request.get_json(
            silent=True
        ) or {}

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
# RUN
# ==========================================================

if __name__ == "__main__":

    app.run(
        host="127.0.0.1",
        port=5000,
        debug=True
    )