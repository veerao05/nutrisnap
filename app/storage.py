"""SQLite persistence for the daily goal and logged meals."""

import json
import sqlite3
from datetime import date, datetime
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "nutrisnap.db"

DEFAULT_GOAL = {"calories": 2000, "protein_pct": 30, "carbs_pct": 40, "fat_pct": 30}


def _conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init() -> None:
    with _conn() as c:
        c.execute("CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT)")
        c.execute("""CREATE TABLE IF NOT EXISTS meals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            day TEXT NOT NULL,
            logged_at TEXT NOT NULL,
            label TEXT NOT NULL,
            items TEXT NOT NULL,
            calories REAL, protein REAL, carbs REAL, fat REAL
        )""")


def get_goal() -> dict:
    with _conn() as c:
        row = c.execute("SELECT value FROM settings WHERE key='goal'").fetchone()
    return json.loads(row["value"]) if row else dict(DEFAULT_GOAL)


def set_goal(goal: dict) -> None:
    with _conn() as c:
        c.execute("INSERT OR REPLACE INTO settings (key, value) VALUES ('goal', ?)",
                  (json.dumps(goal),))


def add_meal(label: str, items: list[dict], totals: dict) -> int:
    now = datetime.now()
    with _conn() as c:
        cur = c.execute(
            "INSERT INTO meals (day, logged_at, label, items, calories, protein, carbs, fat)"
            " VALUES (?,?,?,?,?,?,?,?)",
            (now.date().isoformat(), now.isoformat(timespec="seconds"), label,
             json.dumps(items), totals["calories"], totals["protein"],
             totals["carbs"], totals["fat"]),
        )
        return cur.lastrowid


def meals_for(day: date) -> list[dict]:
    with _conn() as c:
        rows = c.execute("SELECT * FROM meals WHERE day=? ORDER BY logged_at",
                         (day.isoformat(),)).fetchall()
    return [{**dict(r), "items": json.loads(r["items"])} for r in rows]


def delete_meal(meal_id: int) -> bool:
    with _conn() as c:
        return c.execute("DELETE FROM meals WHERE id=?", (meal_id,)).rowcount > 0
