"""Application service that coordinates route validation and optimization."""
from __future__ import annotations

from typing import Any, Mapping, Sequence

from algorithms.hill_climbing import hill_climb
from algorithms.route_utils import calculate_route_distance, validate_route


def optimize_route(
    initial_route: Sequence[str],
    distance_matrix: Mapping[str, Mapping[str, float]],
    depot: str,
    max_iterations: int = 100,
) -> dict[str, Any]:
    """Validate the request and return a structured optimization result."""
    validate_route(initial_route, distance_matrix, depot)
    initial_distance = calculate_route_distance(initial_route, distance_matrix)
    result = hill_climb(
        initial_route=initial_route,
        distance_matrix=distance_matrix,
        depot=depot,
        max_iterations=max_iterations,
    )
    # Result safety invariant: never report a worse route than the initial route.
    if result["final_distance_km"] > initial_distance:
        raise RuntimeError("Algorithm invariant failed: optimized route is worse than initial route.")
    return result
