"""Random-restart Hill Climbing for route-distance minimization.

Each iteration evaluates the best pair-swap neighbor. When a local optimum is
reached, the algorithm starts another climb from a reproducible shuffled route
until the iteration budget is used. The best route found across all climbs is kept.
"""
from __future__ import annotations

import random
from typing import Any, Mapping, Sequence

from algorithms.route_utils import calculate_route_distance, generate_neighbors, validate_route


def hill_climb(
    initial_route: Sequence[str],
    distance_matrix: Mapping[str, Mapping[str, float]],
    depot: str,
    max_iterations: int = 100,
    random_seed: int = 42,
) -> dict[str, Any]:
    """Run random-restart steepest-improvement hill climbing.

    ``max_iterations`` is the maximum number of search rounds, not a promise
    that every round improves the route. A local optimum triggers a new shuffled
    starting order when budget remains. ``trace`` contains one record per round
    for the UI's step-by-step simulation.
    """
    if not isinstance(max_iterations, int) or max_iterations < 1:
        raise ValueError("max_iterations must be a positive integer.")
    validate_route(initial_route, distance_matrix, depot)

    rng = random.Random(random_seed)
    initial = list(initial_route)
    current = initial[:]
    current_distance = calculate_route_distance(current, distance_matrix)
    best_route = current[:]
    best_distance = current_distance
    iterations = 0
    neighbors_evaluated = 0
    restarts = 0
    trace: list[dict[str, Any]] = [{
        "iteration": 0, "route": current[:], "distance_km": current_distance,
        "best_route": best_route[:], "best_distance_km": best_distance,
        "action": "initial", "neighbors_evaluated": 0,
    }]
    stop_reason = "maximum_iterations"

    while iterations < max_iterations:
        iterations += 1
        neighbors = generate_neighbors(current, depot)
        best_neighbor = None
        best_neighbor_distance = float("inf")
        round_evaluated = 0
        for neighbor in neighbors:
            neighbor_distance = calculate_route_distance(neighbor, distance_matrix)
            neighbors_evaluated += 1
            round_evaluated += 1
            if neighbor_distance < best_neighbor_distance:
                best_neighbor = neighbor
                best_neighbor_distance = neighbor_distance

        if best_neighbor is not None and best_neighbor_distance < current_distance - 1e-9:
            current = best_neighbor
            current_distance = best_neighbor_distance
            action = "improved"
            if current_distance < best_distance - 1e-9:
                best_route = current[:]
                best_distance = current_distance
        else:
            # A local optimum has been reached. Restart from a different order,
            # but preserve the best route found so far.
            if iterations >= max_iterations:
                action = "local optimum — search limit reached"
                trace.append({
                    "iteration": iterations, "route": current[:], "distance_km": current_distance,
                    "best_route": best_route[:], "best_distance_km": best_distance,
                    "action": action, "neighbors_evaluated": round_evaluated,
                })
                stop_reason = "local_optimum_at_limit"
                break
            stops = [name for name in initial[1:-1]]
            rng.shuffle(stops)
            current = [depot] + stops + [depot]
            current_distance = calculate_route_distance(current, distance_matrix)
            restarts += 1
            action = "local optimum → random restart"

        trace.append({
            "iteration": iterations, "route": current[:], "distance_km": current_distance,
            "best_route": best_route[:], "best_distance_km": best_distance,
            "action": action, "neighbors_evaluated": round_evaluated,
        })

    if iterations >= max_iterations and stop_reason != "local_optimum_at_limit":
        stop_reason = "maximum_iterations"

    return {
        "algorithm": "Random-Restart Hill Climbing (steepest improvement)",
        "initial_route": initial,
        "best_route": best_route,
        "initial_distance_km": calculate_route_distance(initial, distance_matrix),
        "final_distance_km": best_distance,
        "iterations": iterations,
        "neighbors_evaluated": neighbors_evaluated,
        "restarts": restarts,
        "stop_reason": stop_reason,
        "trace": trace,
    }
