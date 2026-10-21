import json
from pathlib import Path
import pytest
from services.osm_routing import (OSMRoutingError, geocode_place, build_osrm_distance_matrix,
                                  get_osrm_route_geometry, build_real_dataset)

class FakeResponse:
    def __init__(self, payload, status_error=False): self.payload=payload; self.status_error=status_error
    def raise_for_status(self):
        if self.status_error: raise RuntimeError("HTTP failure")
    def json(self): return self.payload
class FakeSession:
    def __init__(self, payload): self.payload=payload; self.calls=[]
    def get(self, url, **kwargs): self.calls.append((url,kwargs)); return FakeResponse(self.payload)

def test_geocode_caches_result_and_uses_osm_source(tmp_path):
    cache=tmp_path/"cache.json"
    session=FakeSession([{"lat":"9.03","lon":"38.74","display_name":"Test, Addis Ababa","osm_type":"node","osm_id":123}])
    first=geocode_place("Test, Ethiopia",session=session,cache_path=cache,sleep_fn=lambda _:None)
    second=geocode_place("Test, Ethiopia",session=FakeSession([]),cache_path=cache,sleep_fn=lambda _:None)
    assert first==second
    assert first["latitude"]==9.03 and first["longitude"]==38.74
    assert first["data_source"]=="OPENSTREETMAP_NOMINATIM"
    assert len(session.calls)==1

def test_geocode_raises_when_no_result(tmp_path):
    with pytest.raises(OSMRoutingError):
        geocode_place("missing place",session=FakeSession([]),cache_path=tmp_path/"cache.json",sleep_fn=lambda _:None)

def test_osrm_matrix_converts_meters_to_km():
    points=[{"name":"A","latitude":9.0,"longitude":38.7},{"name":"B","latitude":9.1,"longitude":38.8}]
    session=FakeSession({"code":"Ok","distances":[[0,1250],[1700,0]]})
    matrix=build_osrm_distance_matrix(points,session=session)
    assert matrix["A"]["B"]==1.25
    assert matrix["B"]["A"]==1.7

def test_osrm_matrix_rejects_unreachable_pair():
    points=[{"name":"A","latitude":9.0,"longitude":38.7},{"name":"B","latitude":9.1,"longitude":38.8}]
    with pytest.raises(OSMRoutingError):
        build_osrm_distance_matrix(points,session=FakeSession({"code":"Ok","distances":[[0,None],[1,0]]}))

def test_route_geometry_returns_lon_lat_pairs():
    points={"A":{"latitude":9,"longitude":38.7},"B":{"latitude":9.1,"longitude":38.8}}
    session=FakeSession({"code":"Ok","routes":[{"geometry":{"coordinates":[[38.7,9.0],[38.75,9.05],[38.8,9.1]]}}]})
    assert get_osrm_route_geometry(["A","B"],points,session=session)==[[38.7,9.0],[38.75,9.05],[38.8,9.1]]

def test_build_real_dataset_marks_source():
    definitions=[{"name":"Stop A","geocode_query":"Stop A, Addis Ababa","location_type":"Area","admin_area":"Demo"}]
    def geo(q): return {"latitude":9.0,"longitude":38.7,"display_name":q,"data_source":"OPENSTREETMAP_NOMINATIM"}
    def matrix(points): return {p["name"]:{q["name"]:(0 if p["name"]==q["name"] else 2.5) for q in points} for p in points}
    dataset=build_real_dataset(["Stop A"],definitions,geocoder=geo,matrix_builder=matrix)
    assert dataset["data_mode"]=="OPENSTREETMAP_OSRM"
    assert all(p["data_source"]=="OPENSTREETMAP_NOMINATIM" for p in dataset["points"])
    assert dataset["distance_matrix"][dataset["depot"]]["Stop A"]==2.5
