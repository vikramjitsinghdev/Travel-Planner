"""Flask HTTP boundary for Wanderlust."""
from flask import Flask, jsonify, request, render_template
from flask_cors import CORS
import main

app = Flask(__name__)
CORS(app)


def success_response(data, status_code=200):
    return jsonify({"success": True, "data": data}), status_code


def error_response(message, status_code=500):
    return jsonify({"success": False, "error": str(message)}), status_code


@app.get("/")
def home():
    return render_template("index.html")


@app.get("/api/health")
def health():
    return success_response({"status": "ok"})


@app.post("/api/trip/start")
@app.post("/api/trip/plan")
def start_trip():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return error_response("Request body must be a JSON object.", 400)
    user_input = data.get("user_input")
    if not isinstance(user_input, str) or not user_input.strip():
        return error_response("Please describe what you want from your trip.", 400)
    trip_information = data.get("trip_information") or {}
    if not isinstance(trip_information, dict):
        return error_response("trip_information must be a JSON object.", 400)
    try:
        result = main.run_travel_planner(user_input.strip(), trip_information)
        if not isinstance(result, dict):
            raise RuntimeError("main.py did not return a JSON object.")
        return success_response(result)
    except (ValueError, TypeError) as exc:
        return error_response(exc, 400)
    except Exception as exc:
        app.logger.exception("Trip-planning request failed")
        # Do not expose API credentials or provider response bodies to clients.
        return error_response(f"Trip planning failed: {type(exc).__name__}. Check the Flask server logs.", 500)


@app.errorhandler(404)
def not_found(_error):
    return error_response("Endpoint not found.", 404)


@app.errorhandler(405)
def method_not_allowed(_error):
    return error_response("HTTP method not allowed.", 405)


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=False)
