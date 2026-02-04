import sqlite3
from pathlib import Path


DB_NAME = "game_stats.db"


def _get_db_path() -> str:
    return str(Path(__file__).with_name(DB_NAME))

def get_next_run_number() -> int:
    conn = sqlite3.connect(_get_db_path())
    try:
        cur = conn.cursor()
        cur.execute("SELECT COALESCE(MAX(num_run), 0) FROM runs")
        (max_num_run,) = cur.fetchone()
        return int(max_num_run) + 1
    finally:
        conn.close()


def add_run(num_run: int, death: int) -> None:
    # Добавляет запись о прохождении игры.
    conn = sqlite3.connect(_get_db_path())
    try:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO runs (num_run, death) VALUES (?, ?)",
            (int(num_run), int(death)),
        )
        conn.commit()
    finally:
        conn.close()

