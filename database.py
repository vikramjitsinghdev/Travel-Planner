import sqlite3
import os
import random
from datetime import datetime


BASE_DIR = os.path.dirname(
    os.path.abspath(__file__)
)

DATABASE_PATH = os.path.join(
    BASE_DIR,
    "wanderlust.db"
)


# ==========================================================
# CONNECTION
# ==========================================================

def get_connection():

    connection = sqlite3.connect(
        DATABASE_PATH
    )

    connection.row_factory = sqlite3.Row

    return connection


# ==========================================================
# DATABASE INITIALIZATION
# ==========================================================

def initialize_database():

    connection = get_connection()

    cursor = connection.cursor()

    # ------------------------------------------------------
    # USER / TRIP INFORMATION
    # ------------------------------------------------------

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS trips (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            departure_location TEXT,

            trip_scope TEXT,

            country TEXT,

            travelers INTEGER,

            duration_days INTEGER,

            travel_dates TEXT,

            maximum_total_travel_time TEXT,

            maximum_distance TEXT,

            transportation_preference TEXT,

            accommodation_preference TEXT,

            safety_requirement TEXT,

            budget REAL,

            other_requirements TEXT,

            user_preferences TEXT,

            status TEXT DEFAULT 'basic',

            created_at TEXT,

            updated_at TEXT
        )
    """)


    # ------------------------------------------------------
    # DESTINATIONS
    # ------------------------------------------------------

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS destinations (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            name TEXT NOT NULL,

            country TEXT,

            region TEXT,

            description TEXT,

            image_url TEXT,

            pexels_url TEXT,

            photo_credit TEXT,

            latitude REAL,

            longitude REAL,

            source TEXT DEFAULT 'preloaded',

            created_at TEXT
        )
    """)


    # ------------------------------------------------------
    # EXPENSES
    # ------------------------------------------------------

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS expenses (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            trip_id INTEGER NOT NULL,

            category TEXT,

            description TEXT,

            amount REAL DEFAULT 0,

            status TEXT DEFAULT 'estimated',

            created_at TEXT,

            FOREIGN KEY (trip_id)
                REFERENCES trips(id)
        )
    """)


    connection.commit()

    connection.close()

    seed_destinations()


# ==========================================================
# PRELOADED DESTINATIONS
# ==========================================================

PRELOADED_DESTINATIONS = [

    {
        "name": "Banff",
        "country": "Canada",
        "region": "Alberta",
        "description":
            "Mountain scenery, lakes, hiking and peaceful natural landscapes.",
        "latitude": 51.1784,
        "longitude": -115.5708
    },

    {
        "name": "Vancouver",
        "country": "Canada",
        "region": "British Columbia",
        "description":
            "Coastal city surrounded by mountains, forests and ocean.",
        "latitude": 49.2827,
        "longitude": -123.1207
    },

    {
        "name": "Quebec City",
        "country": "Canada",
        "region": "Quebec",
        "description":
            "Historic architecture, culture and European-style streets.",
        "latitude": 46.8139,
        "longitude": -71.2080
    },

    {
        "name": "Jasper",
        "country": "Canada",
        "region": "Alberta",
        "description":
            "Quiet mountain environment with lakes, wildlife and hiking.",
        "latitude": 52.8737,
        "longitude": -118.0814
    },

    {
        "name": "Tofino",
        "country": "Canada",
        "region": "British Columbia",
        "description":
            "Pacific coastline, beaches, forests and relaxed atmosphere.",
        "latitude": 49.1530,
        "longitude": -125.9066
    },

    {
        "name": "Whistler",
        "country": "Canada",
        "region": "British Columbia",
        "description":
            "Mountain resort destination with outdoor activities.",
        "latitude": 50.1163,
        "longitude": -122.9574
    },

    {
        "name": "Montreal",
        "country": "Canada",
        "region": "Quebec",
        "description":
            "Food, nightlife, culture, festivals and historic neighbourhoods.",
        "latitude": 45.5017,
        "longitude": -73.5673
    },

    {
        "name": "Halifax",
        "country": "Canada",
        "region": "Nova Scotia",
        "description":
            "Atlantic coastline, waterfront areas and maritime culture.",
        "latitude": 44.6488,
        "longitude": -63.5752
    },

    {
        "name": "Tokyo",
        "country": "Japan",
        "region": "Kanto",
        "description":
            "Massive modern city combining technology, culture and tradition.",
        "latitude": 35.6762,
        "longitude": 139.6503
    },

    {
        "name": "Kyoto",
        "country": "Japan",
        "region": "Kansai",
        "description":
            "Temples, gardens, traditional streets and Japanese culture.",
        "latitude": 35.0116,
        "longitude": 135.7681
    },

    {
        "name": "Osaka",
        "country": "Japan",
        "region": "Kansai",
        "description":
            "Food, nightlife, entertainment and urban Japanese culture.",
        "latitude": 34.6937,
        "longitude": 135.5023
    },

    {
        "name": "Hokkaido",
        "country": "Japan",
        "region": "Northern Japan",
        "description":
            "Mountains, forests, lakes and wide open natural landscapes.",
        "latitude": 43.2203,
        "longitude": 142.8635
    },

    {
        "name": "Shizuoka",
        "country": "Japan",
        "region": "Chubu",
        "description":
            "Mount Fuji views, coastal landscapes, tea fields and nature.",
        "latitude": 34.9756,
        "longitude": 138.3828
    },

    {
        "name": "Lucerne",
        "country": "Switzerland",
        "region": "Central Switzerland",
        "description":
            "Lake scenery, mountains and picturesque historic surroundings.",
        "latitude": 47.0502,
        "longitude": 8.3093
    },

    {
        "name": "Interlaken",
        "country": "Switzerland",
        "region": "Bernese Oberland",
        "description":
            "Alpine scenery, lakes and outdoor adventure.",
        "latitude": 46.6863,
        "longitude": 7.8632
    },

    {
        "name": "Zermatt",
        "country": "Switzerland",
        "region": "Valais",
        "description":
            "Alpine village with dramatic mountain and Matterhorn scenery.",
        "latitude": 46.0207,
        "longitude": 7.7491
    },

    {
        "name": "Reykjavik",
        "country": "Iceland",
        "region": "Capital Region",
        "description":
            "Gateway to Icelandic landscapes, geothermal areas and northern lights.",
        "latitude": 64.1466,
        "longitude": -21.9426
    },

    {
        "name": "Queenstown",
        "country": "New Zealand",
        "region": "Otago",
        "description":
            "Mountains, lakes and adventure activities.",
        "latitude": -45.0312,
        "longitude": 168.6626
    },

    {
        "name": "Vancouver Island",
        "country": "Canada",
        "region": "British Columbia",
        "description":
            "Forests, beaches, mountains and coastal wilderness.",
        "latitude": 49.6500,
        "longitude": -125.4490
    },

    {
        "name": "Cape Breton",
        "country": "Canada",
        "region": "Nova Scotia",
        "description":
            "Coastal drives, mountains, forests and Atlantic scenery.",
        "latitude": 46.1368,
        "longitude": -60.1942
    }

]


def seed_destinations():

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute(
        "SELECT COUNT(*) FROM destinations"
    )

    count = cursor.fetchone()[0]

    if count >= 20:

        connection.close()

        return


    for destination in PRELOADED_DESTINATIONS:

        cursor.execute("""
            INSERT INTO destinations (
                name,
                country,
                region,
                description,
                latitude,
                longitude,
                source,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (

            destination["name"],
            destination["country"],
            destination["region"],
            destination["description"],
            destination["latitude"],
            destination["longitude"],
            "preloaded",
            datetime.utcnow().isoformat()

        ))


    connection.commit()

    connection.close()


# ==========================================================
# TRIP CREATION
# ==========================================================

def create_trip(data):

    connection = get_connection()

    cursor = connection.cursor()

    now = datetime.utcnow().isoformat()

    cursor.execute("""
        INSERT INTO trips (

            departure_location,
            trip_scope,
            country,
            travelers,
            duration_days,
            travel_dates,
            maximum_total_travel_time,
            maximum_distance,
            transportation_preference,
            accommodation_preference,
            safety_requirement,
            budget,
            other_requirements,
            status,
            created_at,
            updated_at

        )

        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (

        data.get("departure_location"),
        data.get("trip_scope"),
        data.get("country"),
        data.get("travelers"),
        data.get("duration_days"),
        data.get("travel_dates"),
        data.get("maximum_total_travel_time"),
        data.get("maximum_distance"),
        data.get("transportation_preference"),
        data.get("accommodation_preference"),
        data.get("safety_requirement"),
        data.get("budget"),
        data.get("other"),
        "basic",
        now,
        now

    ))


    trip_id = cursor.lastrowid

    connection.commit()

    connection.close()

    return trip_id


# ==========================================================
# GET TRIP
# ==========================================================

def get_trip(trip_id):

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute("""
        SELECT *
        FROM trips
        WHERE id = ?
    """, (trip_id,))

    row = cursor.fetchone()

    connection.close()

    if row is None:
        return None

    return dict(row)


# ==========================================================
# UPDATE TRIP
# ==========================================================

def update_trip(trip_id, data):

    connection = get_connection()

    cursor = connection.cursor()

    allowed = [

        "departure_location",
        "trip_scope",
        "country",
        "travelers",
        "duration_days",
        "travel_dates",
        "maximum_total_travel_time",
        "maximum_distance",
        "transportation_preference",
        "accommodation_preference",
        "safety_requirement",
        "budget",
        "other_requirements",
        "user_preferences",
        "status"

    ]


    updates = []

    values = []


    for key in allowed:

        if key in data:

            updates.append(
                f"{key} = ?"
            )

            values.append(
                data[key]
            )


    if not updates:

        connection.close()

        return get_trip(trip_id)


    updates.append(
        "updated_at = ?"
    )

    values.append(
        datetime.utcnow().isoformat()
    )

    values.append(
        trip_id
    )


    cursor.execute(
        f"""
        UPDATE trips
        SET {", ".join(updates)}
        WHERE id = ?
        """,
        values
    )


    connection.commit()

    connection.close()

    return get_trip(trip_id)


# ==========================================================
# RANDOM DESTINATIONS
# ==========================================================

def get_random_destinations(limit=6):

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute("""
        SELECT *
        FROM destinations
        ORDER BY RANDOM()
        LIMIT ?
    """, (limit,))

    rows = cursor.fetchall()

    connection.close()

    return [
        dict(row)
        for row in rows
    ]


# ==========================================================
# HOME DESTINATIONS
# ==========================================================

def get_home_destinations(limit=5):

    return get_random_destinations(limit)


# ==========================================================
# SEARCH DESTINATIONS
# ==========================================================

def search_destinations(query):

    connection = get_connection()

    cursor = connection.cursor()

    pattern = f"%{query}%"

    cursor.execute("""
        SELECT *
        FROM destinations

        WHERE
            name LIKE ?
            OR country LIKE ?
            OR region LIKE ?
            OR description LIKE ?

        ORDER BY name

        LIMIT 20
    """, (
        pattern,
        pattern,
        pattern,
        pattern
    ))

    rows = cursor.fetchall()

    connection.close()

    return [
        dict(row)
        for row in rows
    ]


# ==========================================================
# DESTINATION BY ID
# ==========================================================

def get_destination(destination_id):

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute("""
        SELECT *
        FROM destinations
        WHERE id = ?
    """, (destination_id,))

    row = cursor.fetchone()

    connection.close()

    if row is None:
        return None

    return dict(row)