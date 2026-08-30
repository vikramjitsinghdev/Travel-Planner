import sqlite3
import json
import os
from datetime import datetime


# ==========================================================
# DATABASE LOCATION
# ==========================================================

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
    """
    Create a connection to the Wanderlust SQLite database.
    """

    connection = sqlite3.connect(
        DATABASE_PATH
    )

    connection.row_factory = sqlite3.Row

    # Enable foreign-key support.
    connection.execute(
        "PRAGMA foreign_keys = ON"
    )

    return connection


# ==========================================================
# JSON HELPERS
# ==========================================================

def serialize_json(value):
    """
    Convert Python lists/dictionaries into JSON strings
    so SQLite can store them safely.

    Examples:

        ["none"]
            ↓
        '["none"]'

        {"nature": 1.0}
            ↓
        '{"nature": 1.0}'
    """

    if value is None:
        return None

    if isinstance(
        value,
        (list, dict)
    ):
        return json.dumps(
            value,
            ensure_ascii=False
        )

    return str(value)


def deserialize_json(value, default=None):
    """
    Convert a JSON string stored in SQLite back into
    a Python list/dictionary.

    If conversion fails, return the supplied default.
    """

    if value is None:
        return (
            [] if default is None
            else default
        )

    if isinstance(
        value,
        (list, dict)
    ):
        return value

    try:

        return json.loads(
            value
        )

    except (
        TypeError,
        json.JSONDecodeError
    ):

        return (
            [] if default is None
            else default
        )


# ==========================================================
# DATABASE INITIALIZATION
# ==========================================================

def initialize_database():
    """
    Create all Wanderlust database tables if they do not
    already exist.
    """

    connection = get_connection()

    cursor = connection.cursor()

    # ======================================================
    # TRIPS
    # ======================================================

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS trips (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

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

            budget REAL,

            other_requirements TEXT,

            user_preferences TEXT,

            status TEXT DEFAULT 'basic',

            created_at TEXT,

            updated_at TEXT
        )
    """)

    # ======================================================
    # DESTINATIONS
    # ======================================================

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

    # ======================================================
    # EXPENSES
    # ======================================================

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
                ON DELETE CASCADE
        )
    """)

    connection.commit()

    connection.close()

    # Seed initial destinations.
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


# ==========================================================
# SEED DESTINATIONS
# ==========================================================

def seed_destinations():
    """
    Insert the initial destination database.

    Existing destinations are not duplicated.
    """

    connection = get_connection()

    cursor = connection.cursor()

    for destination in PRELOADED_DESTINATIONS:

        cursor.execute(
            """
            SELECT id
            FROM destinations
            WHERE name = ?
              AND country = ?
            """,
            (
                destination["name"],
                destination["country"]
            )
        )

        existing = cursor.fetchone()

        if existing:
            continue

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
# CREATE TRIP
# ==========================================================

def create_trip(data):
    """
    Create and save a new trip.

    Important:
    Lists/dictionaries are converted to JSON before
    being inserted into SQLite.
    """

    if not isinstance(
        data,
        dict
    ):
        raise ValueError(
            "Trip data must be a dictionary."
        )

    connection = get_connection()

    cursor = connection.cursor()

    now = datetime.utcnow().isoformat()

    # ------------------------------------------------------
    # Support both names used by the application.
    #
    # Frontend/backend may send:
    #
    #     other
    #
    # or:
    #
    #     other_requirements
    # ------------------------------------------------------

    other_requirements = data.get(
        "other_requirements"
    )

    if other_requirements is None:

        other_requirements = data.get(
            "other",
            []
        )

    # ------------------------------------------------------
    # Convert lists/dictionaries into JSON.
    # This fixes:
    #
    # "Error binding parameter ... type 'list' is not supported"
    # ------------------------------------------------------

    other_requirements = serialize_json(
        other_requirements
    )

    user_preferences = serialize_json(
        data.get(
            "user_preferences"
        )
    )

    try:

        cursor.execute("""
            INSERT INTO trips (

                departure_location,
                trip_scope,
                country,
                region,
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
                user_preferences,
                status,
                created_at,
                updated_at

            )

            VALUES (
                ?, ?, ?, ?, ?, ?, ?, ?, ?,
                ?, ?, ?, ?, ?, ?, ?, ?, ?
            )
        """, (

            data.get(
                "departure_location"
            ),

            data.get(
                "trip_scope"
            ),

            data.get(
                "country"
            ),

            data.get(
                "region"
            ),

            data.get(
                "travelers"
            ),

            data.get(
                "duration_days"
            ),

            data.get(
                "travel_dates"
            ),

            data.get(
                "maximum_total_travel_time"
            ),

            data.get(
                "maximum_distance"
            ),

            data.get(
                "transportation_preference"
            ),

            data.get(
                "accommodation_preference"
            ),

            data.get(
                "safety_requirement"
            ),

            data.get(
                "budget"
            ),

            other_requirements,

            user_preferences,

            data.get(
                "status",
                "basic"
            ),

            now,

            now
        ))

        trip_id = cursor.lastrowid

        connection.commit()

        return trip_id

    except Exception:

        connection.rollback()

        raise

    finally:

        connection.close()


# ==========================================================
# GET TRIP
# ==========================================================

def get_trip(trip_id):
    """
    Retrieve a trip from SQLite.

    JSON fields are converted back into Python objects.
    """

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute("""
        SELECT *
        FROM trips
        WHERE id = ?
    """, (
        trip_id,
    ))

    row = cursor.fetchone()

    connection.close()

    if row is None:
        return None

    trip = dict(row)

    # ------------------------------------------------------
    # Restore JSON fields.
    # ------------------------------------------------------

    trip["other_requirements"] = deserialize_json(
        trip.get(
            "other_requirements"
        ),
        []
    )

    trip["user_preferences"] = deserialize_json(
        trip.get(
            "user_preferences"
        ),
        {}
    )

    # Compatibility with the older application format.
    trip["other"] = trip["other_requirements"]

    return trip


# ==========================================================
# UPDATE TRIP
# ==========================================================

def update_trip(
    trip_id,
    data
):
    """
    Update an existing trip.

    JSON/list values are serialized before storage.
    """

    if not isinstance(
        data,
        dict
    ):
        raise ValueError(
            "Trip update data must be a dictionary."
        )

    connection = get_connection()

    cursor = connection.cursor()

    allowed = [

        "departure_location",
        "trip_scope",
        "country",
        "region",
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

        if key not in data:
            continue

        value = data[key]

        # --------------------------------------------------
        # Convert JSON-compatible fields.
        # --------------------------------------------------

        if key in (
            "other_requirements",
            "user_preferences"
        ):

            value = serialize_json(
                value
            )

        updates.append(
            f"{key} = ?"
        )

        values.append(
            value
        )

    if not updates:

        connection.close()

        return get_trip(
            trip_id
        )

    updates.append(
        "updated_at = ?"
    )

    values.append(
        datetime.utcnow().isoformat()
    )

    values.append(
        trip_id
    )

    try:

        cursor.execute(
            f"""
            UPDATE trips

            SET {", ".join(updates)}

            WHERE id = ?
            """,
            values
        )

        connection.commit()

    except Exception:

        connection.rollback()

        raise

    finally:

        connection.close()

    return get_trip(
        trip_id
    )


# ==========================================================
# RANDOM DESTINATIONS
# ==========================================================

def get_random_destinations(
    limit=6
):
    """
    Return random destinations from the database.

    SQLite performs the randomization using:

        ORDER BY RANDOM()
    """

    try:

        limit = int(
            limit
        )

    except (
        TypeError,
        ValueError
    ):

        limit = 6

    # Prevent unreasonable queries.
    limit = max(
        1,
        min(
            limit,
            20
        )
    )

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute("""
        SELECT *
        FROM destinations
        ORDER BY RANDOM()
        LIMIT ?
    """, (
        limit,
    ))

    rows = cursor.fetchall()

    connection.close()

    return [
        dict(row)
        for row in rows
    ]


# ==========================================================
# HOME DESTINATIONS
# ==========================================================

def get_home_destinations(
    limit=5
):
    """
    Get randomized destinations for the homepage.
    """

    return get_random_destinations(
        limit
    )


# ==========================================================
# SEARCH DESTINATIONS
# ==========================================================

def search_destinations(
    query
):
    """
    Search the local destination database.
    """

    if query is None:
        query = ""

    query = str(
        query
    ).strip()

    if not query:
        return []

    connection = get_connection()

    cursor = connection.cursor()

    pattern = (
        f"%{query}%"
    )

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

def get_destination(
    destination_id
):
    """
    Get a single destination by database ID.
    """

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute("""
        SELECT *
        FROM destinations
        WHERE id = ?
    """, (
        destination_id,
    ))

    row = cursor.fetchone()

    connection.close()

    if row is None:
        return None

    return dict(row)


# ==========================================================
# ADD DESTINATION
# ==========================================================

def add_destination(
    data
):
    """
    Add a new destination to the database.

    This will be useful later when Gemini discovers
    a new destination and Pexels/MapTiler information
    is retrieved for it.
    """

    if not isinstance(
        data,
        dict
    ):
        raise ValueError(
            "Destination data must be a dictionary."
        )

    name = str(
        data.get(
            "name",
            ""
        )
    ).strip()

    if not name:
        raise ValueError(
            "Destination name is required."
        )

    connection = get_connection()

    cursor = connection.cursor()

    try:

        cursor.execute("""
            INSERT INTO destinations (

                name,
                country,
                region,
                description,
                image_url,
                pexels_url,
                photo_credit,
                latitude,
                longitude,
                source,
                created_at

            )

            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (

            name,

            data.get(
                "country"
            ),

            data.get(
                "region"
            ),

            data.get(
                "description"
            ),

            data.get(
                "image_url"
            ),

            data.get(
                "pexels_url"
            ),

            data.get(
                "photo_credit"
            ),

            data.get(
                "latitude"
            ),

            data.get(
                "longitude"
            ),

            data.get(
                "source",
                "ai"
            ),

            datetime.utcnow().isoformat()

        ))

        destination_id = cursor.lastrowid

        connection.commit()

        return destination_id

    except Exception:

        connection.rollback()

        raise

    finally:

        connection.close()


# ==========================================================
# ADD EXPENSE
# ==========================================================

def add_expense(
    trip_id,
    category,
    description,
    amount,
    status="estimated"
):
    """
    Store a trip expense in SQLite.
    """

    try:

        amount = float(
            amount
        )

    except (
        TypeError,
        ValueError
    ):

        raise ValueError(
            "Expense amount must be a valid number."
        )

    if amount < 0:

        raise ValueError(
            "Expense amount cannot be negative."
        )

    connection = get_connection()

    cursor = connection.cursor()

    try:

        cursor.execute("""
            INSERT INTO expenses (

                trip_id,
                category,
                description,
                amount,
                status,
                created_at

            )

            VALUES (?, ?, ?, ?, ?, ?)
        """, (

            trip_id,
            str(category),
            str(description),
            amount,
            str(status),
            datetime.utcnow().isoformat()

        ))

        expense_id = cursor.lastrowid

        connection.commit()

        return expense_id

    except Exception:

        connection.rollback()

        raise

    finally:

        connection.close()


# ==========================================================
# GET TRIP EXPENSES
# ==========================================================

def get_trip_expenses(
    trip_id
):
    """
    Retrieve all expenses associated with a trip.
    """

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute("""
        SELECT *
        FROM expenses
        WHERE trip_id = ?
        ORDER BY id
    """, (
        trip_id,
    ))

    rows = cursor.fetchall()

    connection.close()

    return [
        dict(row)
        for row in rows
    ]


# ==========================================================
# INITIALIZE DATABASE WHEN MODULE IS USED
# ==========================================================

initialize_database()