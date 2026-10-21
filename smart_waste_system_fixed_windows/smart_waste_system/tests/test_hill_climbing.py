import pytest

from algorithms.hill_climbing import hill_climb
from algorithms.route_utils import calculate_route_distance
from data.sample_data import get_sample_dataset
from services.route_service import optimize_route


def test_hill_climbing_never_returns_worse_route_than_initial():
    dataset = get_sample_dataset()
    depot = dataset["depot"]
    stops = [p["name"] for p in dataset["points"] if not p["is_depot"]][:5]
    initial_route = [depot] + stops + [depot]
    result = hill_climb(initial_route, dataset["distance_matrix"], depot, max_iterations=100)
    assert result["final_distance_km"] <= result["initial_distance_km"]
    assert result["best_route"][0] == depot
    assert result["best_route"][-1] == depot
    assert sorted(result["best_route"][1:-1]) == sorted(stops)


def test_hill_climbing_rejects_zero_iteration_limit():
    dataset = get_sample_dataset()
    depot = dataset["depot"]
    stops = [p["name"] for p in dataset["points"] if not p["is_depot"]][:2]
    with pytest.raises(ValueError):
        hill_climb([depot] + stops + [depot], dataset["distance_matrix"], depot, max_iterations=0)


def test_route_service_returns_structured_result():
    dataset = get_sample_dataset()
    depot = dataset["depot"]
    stops = [p["name"] for p in dataset["points"] if not p["is_depot"]][:4]
    result = optimize_route(
        [depot] + stops + [depot],
        dataset["distance_matrix"],
        depot,
        max_iterations=50,
    )
    assert "best_route" in result
    assert "stop_reason" in result
    assert result["final_distance_km"] <= result["initial_distance_km"]


def test_symmetric_matrix_has_same_reverse_distance():
    matrix = get_sample_dataset()["distance_matrix"]
    names = list(matrix)
    for a in names:
        for b in names:
            assert matrix[a][b] == matrix[b][a]


def test_hill_climbing_trace_exposes_each_search_round_and_respects_limit():
    dataset = get_sample_dataset()
    depot = dataset["depot"]
    stops = [p["name"] for p in dataset["points"] if not p["is_depot"]][:5]
    result = hill_climb([depot] + stops + [depot], dataset["distance_matrix"], depot, max_iterations=8)
    assert result["iterations"] == 8
    assert len(result["trace"]) == result["iterations"] + 1
    assert result["trace"][0]["action"] == "initial"
    assert result["final_distance_km"] <= result["initial_distance_km"]
    assert result["restarts"] >= 0
