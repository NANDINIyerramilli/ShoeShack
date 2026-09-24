import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent / "orders_complaints.db"


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def get_orders(user_id: str):
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM orders WHERE user_id = ?",
        (user_id,),
    ).fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_complaints(user_id: str):
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM tickets WHERE user_id = ?",
        (user_id,),
    ).fetchall()
    conn.close()
    return [dict(row) for row in rows]
