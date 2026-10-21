import json

from database.db import get_connection, get_recent_route_runs, initialize_database, save_route_run
from data.sample_data import get_sample_dataset


def test_database_initializes_sample_data_once(tmp_path):
    db_path = tmp_path / "test.sqlite"
    initialize_database(db_path)
    initialize_database(db_path)

    with get_connection(db_path) as connection:
        points = connection.execute("SELECT COUNT(*) AS n FROM collection_points").fetchone()["n"]
        runs = connection.execute("SELECT COUNT(*) AS n FROM route_runs").fetchone()["n"]
    assert points == len(get_sample_dataset()["points"])
    assert runs == 0


def test_route_run_is_saved_and_read_back(tmp_path):
    db_path = tmp_path / "test.sqlite"
    initialize_database(db_path)
    dataset = get_sample_dataset()
    depot = dataset["depot"]
    stops = [p["name"] for p in dataset["points"] if not p["is_depot"]][:2]
    route = [depot] + stops + [depot]

    run_id = save_route_run(
        algorithm="Hill Climbing test",
        initial_route=route,
        final_route=route,
        initial_distance_km=10.0,
        final_distance_km=9.0,
        iterations=2,
        settings={"test": True},
        db_path=db_path,
    )
    recent = get_recent_route_runs(limit=5, db_path=db_path)
    assert recent[0]["id"] == run_id
    assert json.loads(recent[0]["initial_route_json"]) == route
    assert recent[0]["data_mode"] == "SIMULATED"
