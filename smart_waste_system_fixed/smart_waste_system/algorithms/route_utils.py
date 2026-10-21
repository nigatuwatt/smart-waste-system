"""Route validation, distance calculation, and neighborhood generation."""
from __future__ import annotations

from itertools import combinations
from typing import Dict, Iterable, List, Mapping, Sequence, Tuple

DistanceMatrix = Mapping[str, Mapping[str, float]]
Route = Sequence[str]


def validate_route(route: Route, distance_matrix: DistanceMatrix, depot: str) -> None:
    """Raise ValueError if a route is invalid or references missing distances."""
    if not route:
        raise ValueError("Route cannot be empty.")
    if len(route) < 4:
        raise ValueError("Route must contain a depot, at least two stops, and the return depot.")
    if route[0] != depot or route[-1] != depot:
        raise ValueError("Route must start and end at the configured depot.")
    stops = list(route[1:-1])
    if depot in stops:
        raise ValueError("The depot must not appear among the intermediate collection stops.")
    if len(stops) != len(set(stops)):
        raise ValueError("Each collection stop must appear exactly once.")
    for location in route:
        if location not in distance_matrix:
            raise ValueError(f"Location {location!r} is missing from the distance matrix.")
    for a, b in zip(route, route[1:]):
        if b not in distance_matrix[a]:
            raise ValueError(f"Distance from {a!r} to {b!r} is missing.")
        distance = distance_matrix[a][b]
        if not isinstance(distance, (int, float)) or distance < 0:
            raise ValueError(f"Distance from {a!r} to {b!r} must be a non-negative number.")


def calculate_route_distance(route: Route, distance_matrix: DistanceMatrix, depot: str | None = None) -> float:
    """Sum all route legs. The caller should supply a route ending at the depot."""
    if len(route) < 2:
        raise ValueError("Route must contain at least a start and an end location.")
    total = 0.0
    for a, b in zip(route, route[1:]):
        try:
            distance = distance_matrix[a][b]
        except KeyError as exc:
            raise ValueError(f"Missing distance for route leg {a!r} -> {b!r}.") from exc
        if not isinstance(distance, (int, float)) or distance < 0:
            raise ValueError(f"Invalid distance for route leg {a!r} -> {b!r}.")
        total += float(distance)
    return round(total, 6)


def generate_neighbors(route: Route, depot: str) -> List[List[str]]:
    """Generate every route formed by swapping two intermediate stops."""
    route_list = list(route)
    if len(route_list) < 4:
        return []
    if route_list[0] != depot or route_list[-1] != depot:
        raise ValueError("Route must start and end at the depot.")
    neighbors: List[List[str]] = []
    for i, j in combinations(range(1, len(route_list) - 1), 2):
        candidate = route_list[:]
        candidate[i], candidate[j] = candidate[j], candidate[i]
        neighbors.append(candidate)
    return neighbors
