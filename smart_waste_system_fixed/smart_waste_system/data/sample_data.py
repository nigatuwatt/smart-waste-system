"""Clearly labeled simulated sample data for local development and testing.

Place names are labels for demonstration only. Distances are generated synthetic
values, not measured road distances or verified routes in Addis Ababa.
"""
from __future__ import annotations

import random
from typing import Any

DEPOT_NAME = "Demo Depot (SIMULATED)"

# Administrative names are based on published Addis Ababa sub-city names.
# Mexico Square and 4 Kilo are represented as areas, not administrative sub-cities.
LOCATION_DEFINITIONS = [
    {
        "name": "Bole Sub-city",
        "location_type": "Administrative sub-city",
        "admin_area": "Bole",
        "geocode_query": "Bole, Addis Ababa, Ethiopia",
    },
    {
        "name": "Arada Sub-city",
        "location_type": "Administrative sub-city",
        "admin_area": "Arada",
        "geocode_query": "Arada, Addis Ababa, Ethiopia",
    },
    {
        "name": "Kirkos Sub-city",
        "location_type": "Administrative sub-city",
        "admin_area": "Kirkos",
        "geocode_query": "Kirkos, Addis Ababa, Ethiopia",
    },
    {
        "name": "Lideta Sub-city",
        "location_type": "Administrative sub-city",
        "admin_area": "Lideta",
        "geocode_query": "Lideta, Addis Ababa, Ethiopia",
    },
    {
        "name": "Addis Ketema Sub-city",
        "location_type": "Administrative sub-city",
        "admin_area": "Addis Ketema",
        "geocode_query": "Addis Ketema, Addis Ababa, Ethiopia",
    },
    {
        "name": "Yeka Sub-city",
        "location_type": "Administrative sub-city",
        "admin_area": "Yeka",
        "geocode_query": "Yeka, Addis Ababa, Ethiopia",
    },
    {
        "name": "Gullele Sub-city",
        "location_type": "Administrative sub-city",
        "admin_area": "Gullele",
        "geocode_query": "Gullele, Addis Ababa, Ethiopia",
    },
    {
        "name": "Kolfe Keranio Sub-city",
        "location_type": "Administrative sub-city",
        "admin_area": "Kolfe Keranio",
        "geocode_query": "Kolfe Keranio, Addis Ababa, Ethiopia",
    },
    {
        "name": "Nifas Silk-Lafto Sub-city",
        "location_type": "Administrative sub-city",
        "admin_area": "Nifas Silk-Lafto",
        "geocode_query": "Nifas Silk-Lafto, Addis Ababa, Ethiopia",
    },
    {
        "name": "Akaki Kality Sub-city",
        "location_type": "Administrative sub-city",
        "admin_area": "Akaki Kality",
        "geocode_query": "Akaki Kality, Addis Ababa, Ethiopia",
    },
    {
        "name": "Lemi Kura Sub-city",
        "location_type": "Administrative sub-city",
        "admin_area": "Lemi Kura",
        "geocode_query": "Lemi Kura, Addis Ababa, Ethiopia",
    },
    {
        "name": "Mexico Square",
        "location_type": "Area / landmark",
        "admin_area": "Not assigned in this demo",
        "geocode_query": "Mexico Square, Addis Ababa, Ethiopia",
    },
    {
        "name": "4 Kilo",
        "location_type": "Area / landmark",
        "admin_area": "Not assigned in this demo",
        "geocode_query": "4 Kilo, Addis Ababa, Ethiopia",
    },
]

def get_sample_dataset(seed: int = 42) -> dict[str, Any]:
    """Return reproducible fictional points and a symmetric distance matrix."""
    points = [
        {
            "name": DEPOT_NAME,
            "location_type": "Simulated depot",
            "admin_area": "Not applicable",
            "geocode_query": "Addis Ababa City Hall, Addis Ababa, Ethiopia",
            "data_source": "SIMULATED",
            "latitude": None,
            "longitude": None,
            "waste_volume_kg": 0.0,
            "priority": 1,
            "is_depot": True,
        }
    ]
    for definition in LOCATION_DEFINITIONS:
        points.append({
            **definition,
            "data_source": "SIMULATED",
            "latitude": None,
            "longitude": None,
            "waste_volume_kg": 500.0,
            "priority": 2,
            "is_depot": False,
        })

    names = [point["name"] for point in points]
    rng = random.Random(seed)
    matrix: dict[str, dict[str, float]] = {
        name: {other: 0.0 for other in names} for name in names
    }

    # Synthetic distances are generated once from a fixed seed so tests and demos
    # are reproducible. These values must not be interpreted as real geography.
    for i, a in enumerate(names):
        for b in names[i + 1:]:
            distance = round(rng.uniform(1.5, 18.0), 2)
            matrix[a][b] = distance
            matrix[b][a] = distance

    return {
        "depot": DEPOT_NAME,
        "points": points,
        "distance_matrix": matrix,
        "data_mode": "SIMULATED",
        "seed": seed,
    }
