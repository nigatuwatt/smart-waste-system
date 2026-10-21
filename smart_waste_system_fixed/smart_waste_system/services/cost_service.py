"""Transparent fuel-use and fuel-cost estimates."""
from __future__ import annotations


def estimate_fuel_cost(
    distance_km: float,
    fuel_consumption_l_per_km: float,
    fuel_price_etb_per_l: float,
) -> dict[str, float]:
    """Estimate fuel use and cost using user-configurable assumptions.

    This is a simple estimate. It excludes idling, traffic, terrain, load changes,
    maintenance, labor, and other operating expenses.
    """
    values = {
        "distance_km": distance_km,
        "fuel_consumption_l_per_km": fuel_consumption_l_per_km,
        "fuel_price_etb_per_l": fuel_price_etb_per_l,
    }
    for name, value in values.items():
        if not isinstance(value, (int, float)) or value < 0:
            raise ValueError(f"{name} must be a non-negative number.")

    fuel_liters = float(distance_km) * float(fuel_consumption_l_per_km)
    cost = fuel_liters * float(fuel_price_etb_per_l)
    return {
        "distance_km": round(float(distance_km), 3),
        "estimated_fuel_liters": round(fuel_liters, 3),
        "estimated_cost_etb": round(cost, 2),
    }
