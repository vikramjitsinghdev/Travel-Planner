from flask import Flask, jsonify, request, render_template
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
# HELPERS
# ==========================================================

def json_body():
    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        raise ValueError("Request body must contain valid JSON.")

    return data


def backend_call(function, data):
    """
    Call main.py and persist the returned trip state in SQLite.
    main.py remains the owner of the travel-planning workflow.
    """
    result = function(trip_data=data)

    if isinstance(result, dict) and result.get("trip_id"):
        database.save_trip(result)

    return result


# ==========================================================
# STARTUP
# ==========================================================

database.init_db()


# ==========================================================
# HOME
# ==========================================================

@app.route("/")
def home():
    return render_template("index.html")


# ==========================================================
# HEALTH
# ==========================================================

@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({
        "status": "success",
        "message": "AI Travel Planner backend is running."
    })


# ==========================================================
# DESTINATION INSPIRATION
# ==========================================================

@app.route("/api/destinations/home", methods=["GET"])
def home_destinations():
    try:
        limit = request.args.get("limit", 4, type=int)
        return jsonify({
            "status": "success",
            "data": database.random_destinations(limit)
        })
    except Exception as error:
        return jsonify({
            "status": "error",
            "message": str(error)
        }), 500


@app.route("/api/destinations/random", methods=["GET"])
def random_destination():
    try:
        destination = database.random_destination()

        if destination is None:
            return jsonify({
                "status": "error",
                "message": "No preloaded destinations are available."
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
# START TRIP
# ==========================================================

@app.route("/api/trip/start", methods=["POST"])
def start_trip():
    try:
        data = json_body()

        # The frontend must send preference text separately
        # as a normal string.
        user_preferences = data.get("user_preferences")

        if not isinstance(user_preferences, str):
            return jsonify({
                "status": "error",
                "message": "user_preferences must be a string."
            }), 400

        if not user_preferences.strip():
            return jsonify({
                "status": "error",
                "message": "user_preferences cannot be empty."
            }), 400

        result = backend_call(main.start_trip, data)

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

@app.route("/api/trip/update", methods=["POST"])
def update_trip():
    try:
        data = json_body()
        result = backend_call(main.update_trip, data)

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

@app.route("/api/trip/select", methods=["POST"])
def select_trip():
    try:
        data = json_body()
        result = backend_call(main.select_trip, data)

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

@app.route("/api/trip/confirm", methods=["POST"])
def confirm_trip():
    try:
        data = json_body()
        result = backend_call(main.confirm_trip, data)

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

@app.route("/api/trip/cancel", methods=["POST"])
def cancel_trip():
    try:
        data = json_body()
        result = backend_call(main.cancel_trip, data)

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

@app.route("/api/trip/status", methods=["POST"])
def trip_status():
    try:
        data = json_body()
        result = backend_call(main.get_trip_status, data)

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
# DELETE TRIP
# ==========================================================

@app.route("/api/trip/delete", methods=["POST"])
def delete_trip():
    try:
        data = json_body()
        trip_id = data.get("trip_id")

        if not trip_id:
            raise ValueError("trip_id is required.")

        # Delete from main.py first.
        result = main.delete_trip(trip_data=data)

        # Then remove the persisted database record.
        database.delete_trip(trip_id)

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
