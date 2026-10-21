"""SQLite database setup and persistence helpers."""
from __future__ import annotations

import json
import sqlite3
from contextlib import closing
from pathlib import Path
from typing import Any, Mapping, Sequence

from config import DATABASE_PATH
from data.sample_data import get_sample_dataset


def get_connection(db_path: str | Path | None = None) -> sqlite3.Connection:
    """Open a connection and enable foreign-key checks."""
    connection = sqlite3.connect(str(db_path or DATABASE_PATH))
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def initialize_database(db_path: str | Path | None = None) -> None:
    """Create tables and insert sample data once, without overwriting edits."""
    schema_path = Path(__file__).with_name("schema.sql")
    schema = schema_path.read_text(encoding="utf-8")
    dataset = get_sample_dataset()

    with closing(get_connection(db_path)) as connection:
        with connection:
            connection.executescript(schema)
            existing = connection.execute(
                "SELECT COUNT(*) AS count FROM collection_points"
            ).fetchone()["count"]

            if existing == 0:
                id_by_name: dict[str, int] = {}
                for point in dataset["points"]:
                    cursor = connection.execute(
                        """
                        INSERT INTO collection_points
                        (name, location_type, admin_area, latitude, longitude,
                         waste_volume_kg, priority, is_depot, data_source)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            point["name"], point["location_type"], point["admin_area"],
                            point["latitude"], point["longitude"], point["waste_volume_kg"],
                            point["priority"], int(point["is_depot"]), point["data_source"],
                        ),
                    )
                    id_by_name[point["name"]] = cursor.lastrowid

                for from_name, row in dataset["distance_matrix"].items():
                    for to_name, distance in row.items():
                        connection.execute(
                            """
                            INSERT INTO distance_matrix
                            (from_point_id, to_point_id, distance_km, data_source)
                            VALUES (?, ?, ?, 'SIMULATED')
                            """,
                            (id_by_name[from_name], id_by_name[to_name], distance),
                        )

                connection.execute(
                    """
                    INSERT OR IGNORE INTO trucks (name, capacity_kg, fuel_l_per_km, data_source)
                    VALUES (?, ?, ?, 'SIMULATED')
                    """,
                    ("Demo Truck 01", 5000.0, 0.25),
                )


def save_route_run(
    algorithm: str,
    initial_route: Sequence[str],
    final_route: Sequence[str],
    initial_distance_km: float,
    final_distance_km: float,
    iterations: int,
    data_mode: str = "SIMULATED",
    settings: Mapping[str, Any] | None = None,
    db_path: str | Path | None = None,
) -> int:
    """Persist one optimization run and return its database ID."""
    with closing(get_connection(db_path)) as connection:
        with connection:
            cursor = connection.execute(
                """
                INSERT INTO route_runs
                (algorithm, initial_route_json, final_route_json,
                 initial_distance_km, final_distance_km, iterations, data_mode, settings_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    algorithm,
                    json.dumps(list(initial_route), ensure_ascii=False),
                    json.dumps(list(final_route), ensure_ascii=False),
                    float(initial_distance_km),
                    float(final_distance_km),
                    int(iterations),
                    data_mode,
                    json.dumps(dict(settings or {}), ensure_ascii=False),
                ),
            )
            return int(cursor.lastrowid)


def get_recent_route_runs(limit: int = 20, db_path: str | Path | None = None) -> list[dict[str, Any]]:
    """Return the most recent route runs as ordinary dictionaries."""
    if limit < 1:
        raise ValueError("limit must be at least 1.")
    with closing(get_connection(db_path)) as connection:
        rows = connection.execute(
            "SELECT * FROM route_runs ORDER BY id DESC LIMIT ?", (int(limit),)
        ).fetchall()
    return [dict(row) for row in rows]
