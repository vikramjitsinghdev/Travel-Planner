"""
Wanderlust SQLite database.

Stores:
- preloaded destination inspiration
- trip sessions
- full trip payloads (including budget state)

Pexels image population is optional. If PEXELS_API_KEY is present,
missing destination images are fetched once and stored locally in SQLite.
"""

import json
import os
import random
import sqlite3
from datetime import datetime, timezone
from urllib.parse import quote
from urllib.request import Request, urlopen

from dotenv import load_dotenv

load_dotenv()

DATABASE = "travel.db"

DESTINATIONS = [
    ("Kyoto", "Japan", "Kansai", "Temples, bamboo forests, gardens and traditional Japanese culture.", "culture,nature"),
    ("Banff", "Canada", "Alberta", "Rocky Mountain scenery, turquoise lakes and wilderness.", "mountains,nature"),
    ("Vancouver Island", "Canada", "British Columbia", "Coastal forests, quiet beaches and mountain landscapes.", "nature,coast"),
    ("Cape Breton Highlands", "Canada", "Nova Scotia", "Atlantic coastline, highlands and scenic drives.", "nature,coast,mountains"),
    ("Swiss Alps", "Switzerland", "Alps", "Alpine lakes, dramatic peaks and peaceful mountain villages.", "mountains,nature"),
    ("Santorini", "Greece", "Cyclades", "Aegean views, sunsets, whitewashed villages and coastlines.", "coast,relaxation"),
    ("Amalfi Coast", "Italy", "Campania", "Cliffside coastal scenery, villages and Mediterranean views.", "coast,relaxation"),
    ("Iceland", "Iceland", "South Iceland", "Waterfalls, volcanic landscapes, glaciers and open wilderness.", "nature,adventure"),
    ("Queenstown", "New Zealand", "Otago", "Lakes, mountains and spectacular South Island scenery.", "mountains,nature"),
    ("Maldives", "Maldives", "Indian Ocean", "Tropical lagoons, beaches and quiet island resorts.", "beach,relaxation"),
    ("Bali", "Indonesia", "Bali", "Rice terraces, forests, beaches and cultural landscapes.", "nature,beach"),
    ("Patagonia", "Argentina/Chile", "Patagonia", "Remote mountains, glaciers, lakes and expansive wilderness.", "mountains,nature"),
    ("Dolomites", "Italy", "South Tyrol", "Dramatic limestone peaks, alpine valleys and scenic villages.", "mountains,nature"),
    ("Norwegian Fjords", "Norway", "Western Norway", "Fjords, waterfalls, mountains and peaceful coastal scenery.", "nature,coast,mountains"),
    ("Madeira", "Portugal", "Madeira", "Volcanic mountains, forests, cliffs and Atlantic scenery.", "nature,coast"),
    ("Azores", "Portugal", "Azores", "Volcanic lakes, green countryside and quiet Atlantic islands.", "nature,coast"),
    ("Costa Rica", "Costa Rica", "Central America", "Rainforests, beaches, volcanoes and wildlife.", "nature,beach"),
    ("Scottish Highlands", "United Kingdom", "Scotland", "Lochs, mountains, glens and remote countryside.", "nature,mountains"),
    ("Grand Manan", "Canada", "New Brunswick", "Quiet island scenery, coastal cliffs and marine wildlife.", "nature,coast"),
    ("Gaspé Peninsula", "Canada", "Quebec", "Rugged coast, forests, mountains and national parks.", "nature,coast,mountains"),
]


def get_connection():
    connection = sqlite3.connect(DATABASE)
    connection.row_factory = sqlite3.Row
    return connection


def init_db():
    connection = get_connection()

    connection.executescript("""
        CREATE TABLE IF NOT EXISTS destinations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            country TEXT NOT NULL,
            region TEXT,
            description TEXT,
            category TEXT,
            image_url TEXT,
            image_credit TEXT,
            pexels_url TEXT
        );

        CREATE TABLE IF NOT EXISTS trips (
            trip_id TEXT PRIMARY KEY,
            departure_location TEXT,
            trip_scope TEXT,
            country TEXT,
            region TEXT,
            travelers INTEGER,
            duration_days INTEGER,
            travel_dates TEXT,
            maximum_total_travel_time TEXT,
            maximum_distance TEXT,
            transportation_preference TEXT,
            accommodation_preference TEXT,
            safety_requirement TEXT,
            other_requirements TEXT,
            user_preferences TEXT,
            total_budget REAL,
            spent REAL DEFAULT 0,
            remaining REAL DEFAULT 0,
            status TEXT,
            selected_destination TEXT,
            payload TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );

        CREATE INDEX IF NOT EXISTS idx_trips_status
        ON trips(status);
    """)

    count = connection.execute(
        "SELECT COUNT(*) AS count FROM destinations"
    ).fetchone()["count"]

    if count == 0:
        connection.executemany("""
            INSERT INTO destinations
            (name, country, region, description, category)
            VALUES (?, ?, ?, ?, ?)
        """, DESTINATIONS)

    connection.commit()
    connection.close()

    populate_pexels_images()


def populate_pexels_images():
    api_key = os.getenv("PEXELS_API_KEY")

    if not api_key:
        return

    connection = get_connection()
    rows = connection.execute("""
        SELECT id, name, country
        FROM destinations
        WHERE image_url IS NULL OR image_url = ''
    """).fetchall()

    for row in rows:
        try:
            query = quote(f"{row['name']} {row['country']} travel")
            request = Request(
                f"https://api.pexels.com/v1/search?query={query}&per_page=1",
                headers={"Authorization": api_key}
            )

            with urlopen(request, timeout=10) as response:
                data = json.loads(response.read().decode("utf-8"))

            photos = data.get("photos") or []
            if not photos:
                continue

            photo = photos[0]
            image = photo.get("src", {}).get("large2x") or photo.get("src", {}).get("large")
            credit = photo.get("photographer")
            pexels_url = photo.get("url")

            if image:
                connection.execute("""
                    UPDATE destinations
                    SET image_url = ?, image_credit = ?, pexels_url = ?
                    WHERE id = ?
                """, (image, credit, pexels_url, row["id"]))

        except Exception:
            # Image population is optional. The application must still start
            # if Pexels is unavailable.
            continue

    connection.commit()
    connection.close()


def random_destinations(limit=4):
    limit = max(1, min(int(limit), 20))
    connection = get_connection()
    rows = connection.execute(
        "SELECT * FROM destinations ORDER BY RANDOM() LIMIT ?",
        (limit,)
    ).fetchall()
    connection.close()
    return [dict(row) for row in rows]


def random_destination():
    rows = random_destinations(1)
    return rows[0] if rows else None


def save_trip(payload):
    if not isinstance(payload, dict):
        raise TypeError("Trip payload must be a dictionary.")

    trip_id = payload.get("trip_id")
    if not trip_id:
        return

    info = payload.get("trip_information") or {}
    budget = payload.get("budget") or {}

    now = datetime.now(timezone.utc).isoformat()

    connection = get_connection()
    connection.execute("""
        INSERT INTO trips (
            trip_id, departure_location, trip_scope, country, region,
            travelers, duration_days, travel_dates,
            maximum_total_travel_time, maximum_distance,
            transportation_preference, accommodation_preference,
            safety_requirement, other_requirements, user_preferences,
            total_budget, spent, remaining, status,
            selected_destination, payload, created_at, updated_at
        )
        VALUES (
            ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
        )
        ON CONFLICT(trip_id) DO UPDATE SET
            departure_location=excluded.departure_location,
            trip_scope=excluded.trip_scope,
            country=excluded.country,
            region=excluded.region,
            travelers=excluded.travelers,
            duration_days=excluded.duration_days,
            travel_dates=excluded.travel_dates,
            maximum_total_travel_time=excluded.maximum_total_travel_time,
            maximum_distance=excluded.maximum_distance,
            transportation_preference=excluded.transportation_preference,
            accommodation_preference=excluded.accommodation_preference,
            safety_requirement=excluded.safety_requirement,
            other_requirements=excluded.other_requirements,
            user_preferences=excluded.user_preferences,
            total_budget=excluded.total_budget,
            spent=excluded.spent,
            remaining=excluded.remaining,
            status=excluded.status,
            selected_destination=excluded.selected_destination,
            payload=excluded.payload,
            updated_at=excluded.updated_at
    """, (
        trip_id,
        info.get("departure_location"),
        info.get("trip_scope"),
        info.get("country"),
        info.get("region"),
        info.get("travelers"),
        info.get("duration_days"),
        info.get("travel_dates"),
        info.get("maximum_total_travel_time"),
        info.get("maximum_distance"),
        info.get("transportation_preference"),
        info.get("accommodation_preference"),
        info.get("safety_requirement"),
        json.dumps(info.get("other", []), ensure_ascii=False),
        payload.get("original_user_input") or payload.get("user_preferences"),
        budget.get("total_budget"),
        budget.get("spent", 0),
        budget.get("remaining", 0),
        payload.get("status"),
        payload.get("selected_destination"),
        json.dumps(payload, ensure_ascii=False, default=str),
        now,
        now
    ))
    connection.commit()
    connection.close()


def get_trip(trip_id):
    connection = get_connection()
    row = connection.execute(
        "SELECT payload FROM trips WHERE trip_id = ?",
        (trip_id,)
    ).fetchone()
    connection.close()

    if not row:
        return None

    try:
        return json.loads(row["payload"])
    except json.JSONDecodeError:
        return None


def delete_trip(trip_id):
    connection = get_connection()
    cursor = connection.execute(
        "DELETE FROM trips WHERE trip_id = ?",
        (trip_id,)
    )
    connection.commit()
    deleted = cursor.rowcount > 0
    connection.close()
    return deleted


if __name__ == "__main__":
    init_db()
    print(f"SQLite database initialized: {DATABASE}")
