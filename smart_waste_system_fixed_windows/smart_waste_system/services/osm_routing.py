"""OpenStreetMap geocoding and OSRM road-distance helpers.

Public Nominatim is deliberately called only when the user explicitly requests
OSM data. Geocoding results are cached locally in a JSON file. Keep requests
at or below one per second and use an identifying User-Agent.
"""
from __future__ import annotations
import json
import math
import time
from pathlib import Path
from typing import Any, Mapping, Sequence
from urllib.parse import quote
import requests

NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
OSRM_BASE_URL = "https://router.project-osrm.org"
CACHE_PATH = Path(__file__).resolve().parents[1] / "data" / "geocode_cache.json"
USER_AGENT = "SmartWasteCollectionStudentPrototype/1.0 (educational project; contact: set-your-email-in-config)"

class OSMRoutingError(RuntimeError):
    """Raised when geocoding or road routing cannot provide reliable results."""

def _read_cache(path: Path = CACHE_PATH) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}

def _write_cache(cache: Mapping[str, Any], path: Path = CACHE_PATH) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(cache, ensure_ascii=False, indent=2), encoding="utf-8")

def geocode_place(query: str, *, session: Any = requests, cache_path: Path = CACHE_PATH,
                  sleep_fn=time.sleep) -> dict[str, Any]:
    """Resolve one place using Nominatim and cache coordinates/display name.

    Returned coordinates are OSM geocoding results, not a guarantee that the
    point is the exact curbside collection entrance. Review the display name.
    """
    if not query or not query.strip():
        raise ValueError("Geocoding query cannot be empty.")
    key = query.strip().casefold()
    cache = _read_cache(cache_path)
    if key in cache:
        return dict(cache[key])
    headers = {"User-Agent": USER_AGENT, "Accept": "application/json"}
    try:
        response = session.get(NOMINATIM_URL, params={"q": query, "format": "jsonv2", "limit": 1,
                                                       "countrycodes": "et"},
                              headers=headers, timeout=20)
        response.raise_for_status()
        results = response.json()
    except (requests.RequestException, ValueError, TypeError) as exc:
        raise OSMRoutingError(f"OpenStreetMap geocoding failed for {query!r}: {exc}") from exc
    if not results:
        raise OSMRoutingError(f"OpenStreetMap could not find a result for {query!r}.")
    item = results[0]
    try:
        result = {"latitude": float(item["lat"]), "longitude": float(item["lon"]),
                  "display_name": str(item["display_name"]), "osm_type": item.get("osm_type"),
                  "osm_id": item.get("osm_id"), "data_source": "OPENSTREETMAP_NOMINATIM"}
    except (KeyError, TypeError, ValueError) as exc:
        raise OSMRoutingError(f"Invalid geocoding response for {query!r}.") from exc
    if not (-90 <= result["latitude"] <= 90 and -180 <= result["longitude"] <= 180):
        raise OSMRoutingError(f"Coordinates returned for {query!r} are outside valid ranges.")
    cache[key] = result
    _write_cache(cache, cache_path)
    # Only wait after a new request; public Nominatim has a strict usage policy.
    sleep_fn(1.05)
    return result

def build_osrm_distance_matrix(points: Sequence[Mapping[str, Any]], *, session: Any = requests,
                               base_url: str = OSRM_BASE_URL) -> dict[str, dict[str, float]]:
    """Build a directed matrix in km from OSRM's fastest driving routes."""
    if len(points) < 2:
        raise ValueError("At least two points are required for an OSRM matrix.")
    coords=[]
    names=[]
    for point in points:
        try:
            lat, lon = float(point["latitude"]), float(point["longitude"])
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError(f"Point {point.get('name', '?')!r} has no valid coordinates.") from exc
        if not (-90 <= lat <= 90 and -180 <= lon <= 180):
            raise ValueError(f"Point {point.get('name', '?')!r} has invalid coordinates.")
        coords.append(f"{lon:.6f},{lat:.6f}")
        names.append(str(point["name"]))
    url=f"{base_url.rstrip('/')}/table/v1/driving/" + ";".join(coords)
    try:
        response=session.get(url, params={"annotations":"distance"}, headers={"User-Agent":USER_AGENT}, timeout=35)
        response.raise_for_status()
        payload=response.json()
    except (requests.RequestException, ValueError, TypeError) as exc:
        raise OSMRoutingError(f"OSRM road-distance request failed: {exc}") from exc
    if payload.get("code") != "Ok" or not isinstance(payload.get("distances"), list):
        raise OSMRoutingError(f"OSRM could not build a complete road matrix: {payload.get('message', payload.get('code'))}")
    raw=payload["distances"]
    if len(raw) != len(names) or any(not isinstance(row, list) or len(row) != len(names) for row in raw):
        raise OSMRoutingError("OSRM returned an incomplete distance matrix.")
    matrix={}
    for i, a in enumerate(names):
        matrix[a]={}
        for j, b in enumerate(names):
            meters=raw[i][j]
            if meters is None or not isinstance(meters, (int,float)) or not math.isfinite(meters) or meters < 0:
                raise OSMRoutingError(f"No drivable road distance was found from {a!r} to {b!r}.")
            matrix[a][b]=round(float(meters)/1000.0, 3)
    return matrix

def get_osrm_route_geometry(route_names: Sequence[str], points_by_name: Mapping[str, Mapping[str, Any]], *,
                            session: Any = requests, base_url: str = OSRM_BASE_URL) -> list[list[float]]:
    """Return [longitude, latitude] points along the OSRM road geometry."""
    coords=[]
    for name in route_names:
        point=points_by_name[name]
        coords.append(f"{float(point['longitude']):.6f},{float(point['latitude']):.6f}")
    url=f"{base_url.rstrip('/')}/route/v1/driving/" + ";".join(coords)
    try:
        response=session.get(url, params={"overview":"full", "geometries":"geojson", "steps":"false"},
                             headers={"User-Agent":USER_AGENT}, timeout=35)
        response.raise_for_status()
        payload=response.json()
    except (requests.RequestException, ValueError, TypeError) as exc:
        raise OSMRoutingError(f"OSRM road geometry request failed: {exc}") from exc
    routes=payload.get("routes") or []
    if payload.get("code") != "Ok" or not routes:
        raise OSMRoutingError(f"OSRM could not return route geometry: {payload.get('message', payload.get('code'))}")
    coordinates=routes[0].get("geometry", {}).get("coordinates")
    if not isinstance(coordinates, list) or len(coordinates) < 2:
        raise OSMRoutingError("OSRM returned empty road geometry.")
    return [[float(lon), float(lat)] for lon, lat in coordinates]

def build_real_dataset(selected_names: Sequence[str], definitions: Sequence[Mapping[str, Any]], *,
                       geocoder=geocode_place, matrix_builder=build_osrm_distance_matrix) -> dict[str, Any]:
    """Geocode the selected collection locations and request real OSM road distances."""
    lookup={str(item["name"]):item for item in definitions}
    depot_name="Addis Ababa City Hall (OSM geocoded depot)"
    depot_query="Addis Ababa City Hall, Addis Ababa, Ethiopia"
    queries=[(depot_name, depot_query, {"location_type":"Depot / landmark", "admin_area":"Addis Ababa"})]
    for name in selected_names:
        if name not in lookup:
            raise ValueError(f"Unknown collection point: {name}")
        definition=lookup[name]
        queries.append((name, definition.get("geocode_query", f"{name}, Addis Ababa, Ethiopia"), definition))
    points=[]
    for idx, (name, query, definition) in enumerate(queries):
        geo=geocoder(query)
        points.append({**definition, "name":name, "geocode_query":query,
                       "latitude":geo["latitude"], "longitude":geo["longitude"],
                       "geocoded_name":geo["display_name"], "osm_type":geo.get("osm_type"),
                       "osm_id":geo.get("osm_id"), "data_source":"OPENSTREETMAP_NOMINATIM",
                       "waste_volume_kg":0.0 if idx==0 else 500.0,
                       "priority":1 if idx==0 else 2, "is_depot":idx==0})
    matrix=matrix_builder(points)
    return {"depot":depot_name, "points":points, "distance_matrix":matrix,
            "data_mode":"OPENSTREETMAP_OSRM", "data_source_label":"OpenStreetMap geocoding + OSRM road distances"}
