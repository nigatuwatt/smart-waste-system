import pytest

from algorithms.route_utils import calculate_route_distance, generate_neighbors, validate_route
from data.sample_data import get_sample_dataset
from services.cost_service import estimate_fuel_cost


def test_distance_calculation_includes_return_to_depot():
    matrix = {
        "D": {"D": 0, "A": 2, "B": 5},
        "A": {"D": 2, "A": 0, "B": 3},
        "B": {"D": 5, "A": 3, "B": 0},
    }
    assert calculate_route_distance(["D", "A", "B", "D"], matrix) == 10.0


def test_invalid_route_missing_return_depot_is_rejected():
    matrix = {"D": {"D": 0, "A": 2}, "A": {"D": 2, "A": 0}}
    with pytest.raises(ValueError):
        validate_route(["D", "A"], matrix, "D")


def test_duplicate_stops_are_rejected():
    matrix = {
        "D": {"D": 0, "A": 1, "B": 2},
        "A": {"D": 1, "A": 0, "B": 1},
        "B": {"D": 2, "A": 1, "B": 0},
    }
    with pytest.raises(ValueError):
        validate_route(["D", "A", "A", "B", "D"], matrix, "D")


def test_neighbor_generation_keeps_depot_fixed():
    neighbors = generate_neighbors(["D", "A", "B", "C", "D"], "D")
    assert neighbors
    assert all(route[0] == "D" and route[-1] == "D" for route in neighbors)
    assert all(sorted(route[1:-1]) == ["A", "B", "C"] for route in neighbors)


def test_sample_data_is_reproducible_and_labeled_simulated():
    first = get_sample_dataset()
    second = get_sample_dataset()
    assert first["distance_matrix"] == second["distance_matrix"]
    assert first["data_mode"] == "SIMULATED"
    assert all(point["data_source"] == "SIMULATED" for point in first["points"])


def test_fuel_cost_estimate():
    result = estimate_fuel_cost(10, 0.25, 100)
    assert result["estimated_fuel_liters"] == 2.5
    assert result["estimated_cost_etb"] == 250.0


def test_negative_distance_is_rejected_by_cost_service():
    with pytest.raises(ValueError):
        estimate_fuel_cost(-1, 0.25, 100)
