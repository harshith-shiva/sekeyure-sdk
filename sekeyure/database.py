import sqlite3
import json
import time
import numpy as np

DB_PATH = "keydna.db"

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # lets you access columns by name
    return conn

def init_db():
    """
    Run once when the SDK starts.
    Creates tables if they do not exist yet.
    """
    conn = get_connection()

    conn.execute("""
        CREATE TABLE IF NOT EXISTS profiles (
            user_id         TEXT PRIMARY KEY,
            password_length INTEGER,
            status          TEXT DEFAULT 'enrolling',
            enrolled_at     REAL,
            last_login      REAL
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS samples (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id     TEXT NOT NULL,
            vector      TEXT NOT NULL,
            timestamp   REAL NOT NULL,
            FOREIGN KEY (user_id) REFERENCES profiles(user_id)
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS models (
            user_id       TEXT PRIMARY KEY,
            model_blob    BLOB NOT NULL,
            model_type    TEXT NOT NULL,
            sample_count  INTEGER NOT NULL,
            trained_at    REAL NOT NULL,
            FOREIGN KEY (user_id) REFERENCES profiles(user_id)
        )
    """)

    conn.commit()
    conn.close()

def store_sample(user_id: str, vector, password_length: int):
    """
    Stores one feature vector for a user.
    Also creates or updates the user's profile row.
    """
    conn = get_connection()
    now  = time.time()

    # Check if this user has a profile yet
    existing = conn.execute(
        "SELECT user_id, password_length FROM profiles WHERE user_id = ?",
        (user_id,)
    ).fetchone()

    if existing is None:
        # First time we have ever seen this user
        # Create their profile row
        conn.execute(
            """INSERT INTO profiles
                (user_id, password_length, status, enrolled_at, last_login)
                VALUES (?, ?, 'enrolling', ?, ?)""",
            (user_id, password_length, now, now)
        )

    elif existing["password_length"] != password_length:
        # Password length changed — means user changed their password
        # Wipe all old samples and models, start fresh
        conn.execute("DELETE FROM samples WHERE user_id = ?", (user_id,))
        conn.execute("DELETE FROM models  WHERE user_id = ?", (user_id,))
        conn.execute(
            """UPDATE profiles
                SET password_length = ?,
                    status          = 'enrolling',
                    enrolled_at     = ?,
                    last_login      = ?
                WHERE user_id = ?""",
            (password_length, now, now, user_id)
        )

    else:
        # Existing user, same password length — just update last login
        conn.execute(
            "UPDATE profiles SET last_login = ? WHERE user_id = ?",
            (now, user_id)
        )

    # Store the vector — serialise numpy array to JSON list
    conn.execute(
        "INSERT INTO samples (user_id, vector, timestamp) VALUES (?, ?, ?)",
        (user_id, json.dumps(vector.tolist()), now)
    )

    conn.commit()
    conn.close()

def get_sample_count(user_id: str) -> int:
    conn = get_connection()
    row  = conn.execute(
        "SELECT COUNT(*) as count FROM samples WHERE user_id = ?",
        (user_id,)
    ).fetchone()
    conn.close()
    return row["count"] if row else 0


def load_all_vectors(user_id: str):
    """
    Loads all stored vectors for a user as a numpy array.
    Shape will be (sample_count, vector_length).
    Used when training models.
    """
   

    conn = get_connection()
    rows = conn.execute(
        "SELECT vector FROM samples WHERE user_id = ? ORDER BY timestamp ASC",
        (user_id,)
    ).fetchall()
    conn.close()

    if not rows:
        return None

    return np.array([json.loads(row["vector"]) for row in rows])

# These thresholds control when each phase activates
ENROLL_MIN   = 5    # minimum samples before any scoring
IFOREST_MIN  = 30   # samples needed before switching to Isolation Forest

def get_phase(sample_count: int) -> str:
    if sample_count < ENROLL_MIN:
        return "enrolling"
    elif sample_count < IFOREST_MIN:
        return "gaussian"
    else:
        return "iforest"
    
