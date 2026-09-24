import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent / "db.sqlite"


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def execute_query(query: str):
    conn = get_connection()
    rows = conn.execute(query).fetchall()
    conn.close()
    return [dict(row) for row in rows]
