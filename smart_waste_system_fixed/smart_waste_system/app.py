from __future__ import annotations
from datetime import datetime
import pandas as pd
import plotly.express as px
import pydeck as pdk
import streamlit as st
from algorithms.route_utils import calculate_route_distance
from config import APP_TITLE, DEFAULT_FUEL_CONSUMPTION_L_PER_KM, DEFAULT_FUEL_PRICE_ETB_PER_L
from data.sample_data import get_sample_dataset, LOCATION_DEFINITIONS
from database.db import get_recent_route_runs, initialize_database, save_route_run
from services.cost_service import estimate_fuel_cost
from services.route_service import optimize_route
from services.osm_routing import (OSMRoutingError, build_real_dataset, get_osrm_route_geometry)

st.set_page_config(page_title=APP_TITLE, page_icon="♻️", layout="wide")
st.markdown("""<style>.block-container{padding-top:1.5rem;padding-bottom:2rem}[data-testid=stMetric]{background:rgba(120,120,120,.07);padding:13px;border-radius:12px}</style>""", unsafe_allow_html=True)
initialize_database()

@st.cache_data(show_spinner=False)
def load_simulated_dataset():
    return get_sample_dataset()

@st.cache_data(ttl=86400, show_spinner=False)
def load_real_dataset(selected_names_tuple):
    return build_real_dataset(list(selected_names_tuple), LOCATION_DEFINITIONS)

simulated_dataset=load_simulated_dataset()
simulated_points=simulated_dataset["points"]
simulated_names=[p["name"] for p in simulated_points if not p["is_depot"]]

st.title("♻️ Smart Waste Collection")
st.subheader("Route Optimization System for Addis Ababa City")
st.caption("Student prototype · Streamlit · OpenStreetMap · OSRM · Hill Climbing")

with st.sidebar:
    st.header("Route settings")
    requested_mode=st.radio("Distance data source", ["OpenStreetMap road distances", "Simulated demo data"], index=0,
                            help="OSM mode geocodes the selected locations and requests road distances from OSRM. If it fails, the app explicitly falls back to simulated data.")
    st.caption("The public OSM services are community resources, not a guaranteed production API.")
    selected_stops=st.multiselect("Collection points to visit", options=simulated_names, default=simulated_names[:5],
                                  help="These are area labels. Review the OSM geocoded result names before treating them as exact collection entrances.")
    start_order=st.selectbox("Initial route order", ["Sample order", "Reverse sample order", "Alphabetical order"])
    max_iterations=st.slider("Maximum iterations", 1, 500, 100)
    fuel_consumption=st.number_input("Fuel use (liters per km)", 0.0, 10.0, float(DEFAULT_FUEL_CONSUMPTION_L_PER_KM), .05, format="%.2f")
    fuel_price=st.number_input("Fuel price (ETB per liter)", 0.0, 10000.0, float(DEFAULT_FUEL_PRICE_ETB_PER_L), 1.0, format="%.2f")
    run_button=st.button("Load data and optimize", type="primary", use_container_width=True)
    simulation_button=st.button("▶ Show route-finding simulation", use_container_width=True,
                                 help="Show the route and distance after every hill-climbing search round.")
    if simulation_button:
        st.session_state["show_route_simulation"] = True

st.markdown("### Data source status")
if requested_mode == "Simulated demo data":
    dataset=simulated_dataset
    st.warning("SIMULATED MODE: coordinates and distances are synthetic. The map is a schematic plot of the demo points, not verified geography.")
else:
    if len(selected_stops) < 2:
        st.info("Choose at least two collection points. OSM data will be requested after you click the button.")
        st.stop()
    cache_key=(requested_mode, tuple(selected_stops))
    if run_button or ("active_dataset_key" in st.session_state and st.session_state.get("active_dataset_key")==cache_key):
        try:
            with st.spinner("Resolving selected places with OpenStreetMap and requesting OSRM road distances…"):
                dataset=load_real_dataset(tuple(selected_stops))
            st.session_state["active_dataset_key"]=cache_key
            st.session_state["active_real_dataset"]=dataset
        except (OSMRoutingError, ValueError, KeyError) as exc:
            dataset=simulated_dataset
            st.error(f"REAL OSM DATA FAILED — using SIMULATED fallback instead. No road distances are being claimed as real. Reason: {exc}")
            st.session_state.pop("active_dataset_key", None)
            st.session_state.pop("active_real_dataset", None)
    elif "active_real_dataset" in st.session_state and st.session_state.get("active_dataset_key")==cache_key:
        dataset=st.session_state["active_real_dataset"]
    else:
        st.info("Click **Load data and optimize** to make the external OSM/OSRM requests. Nothing is fetched automatically.")
        st.stop()

is_real=dataset["data_mode"]=="OPENSTREETMAP_OSRM"
if is_real:
    st.success("REAL ROAD-DISTANCE MODE: coordinates are returned by OpenStreetMap Nominatim and distances are returned by OSRM. Review the geocoded place labels below; an area centroid may not be the exact curbside collection entrance.")
    st.caption("Map/data attribution: © OpenStreetMap contributors · Routing: OSRM. OSM data may be incomplete or outdated.")
else:
    st.warning("SIMULATED DATA ACTIVE. Do not present these distances, coordinates, or savings as actual Addis Ababa road measurements.")

points=dataset["points"]
distance_matrix=dataset["distance_matrix"]
point_names=[p["name"] for p in points]
point_by_name={p["name"]:p for p in points}
depot_name=dataset["depot"]
collection_names=[n for n in point_names if n!=depot_name]
# Keep only selected stops that exist in the currently active dataset.
active_selected=[n for n in selected_stops if n in collection_names]
if len(active_selected)<2:
    st.info("Select at least two collection points that exist in the active data source.")
    st.stop()
if start_order=="Reverse sample order": initial_stops=list(reversed(active_selected))
elif start_order=="Alphabetical order": initial_stops=sorted(active_selected)
else: initial_stops=active_selected[:]
initial_route=[depot_name]+initial_stops+[depot_name]

# Re-optimize after button click, when settings/data selection change, or first visit.
settings_key=(tuple(initial_route), max_iterations, float(fuel_consumption), float(fuel_price), dataset["data_mode"])
if run_button or st.session_state.get("settings_key") != settings_key or "last_result" not in st.session_state:
    try:
        result=optimize_route(initial_route, distance_matrix, depot_name, max_iterations)
        st.session_state["last_result"]=result
        st.session_state["settings_key"]=settings_key
        st.session_state["last_data_mode"]=dataset["data_mode"]
        save_route_run(algorithm=result["algorithm"], initial_route=result["initial_route"], final_route=result["best_route"],
                       initial_distance_km=result["initial_distance_km"], final_distance_km=result["final_distance_km"],
                       iterations=result["iterations"], data_mode=dataset["data_mode"],
                       settings={"max_iterations":max_iterations,"fuel_consumption_l_per_km":fuel_consumption,
                                 "fuel_price_etb_per_l":fuel_price,"data_mode":dataset["data_mode"]})
    except (ValueError, KeyError) as exc:
        st.error(f"Could not optimize route: {exc}")
        st.stop()
result=st.session_state["last_result"]
# Ensure displayed result belongs to current mode/route. When switching modes, request a run first.
if st.session_state.get("last_data_mode") != dataset["data_mode"]:
    result=optimize_route(initial_route, distance_matrix, depot_name, max_iterations)
    st.session_state["last_result"]=result
    st.session_state["last_data_mode"]=dataset["data_mode"]
initial_distance=result["initial_distance_km"]
final_distance=result["final_distance_km"]
saved_km=max(0.0,initial_distance-final_distance)
reduction_pct=(saved_km/initial_distance*100) if initial_distance>0 else 0.0
initial_cost=estimate_fuel_cost(initial_distance,fuel_consumption,fuel_price)
final_cost=estimate_fuel_cost(final_distance,fuel_consumption,fuel_price)
estimated_saving=max(0.0,initial_cost["estimated_cost_etb"]-final_cost["estimated_cost_etb"])

st.markdown("### Performance overview")
a,b,c,d=st.columns(4)
a.metric("Initial distance",f"{initial_distance:.2f} km")
b.metric("Best distance found",f"{final_distance:.2f} km",delta=f"{-saved_km:.2f} km",delta_color="inverse")
c.metric("Distance reduction",f"{reduction_pct:.1f}%")
d.metric("Search iterations",str(result["iterations"]))
st.caption(f"Random restarts: {result.get('restarts', 0)} · Neighbors evaluated: {result['neighbors_evaluated']} · Stop reason: {result['stop_reason']}")
e,f,g=st.columns(3)
e.metric("Estimated initial fuel cost",f"{initial_cost['estimated_cost_etb']:,.2f} ETB")
f.metric("Estimated final fuel cost",f"{final_cost['estimated_cost_etb']:,.2f} ETB")
g.metric("Estimated cost difference",f"{estimated_saving:,.2f} ETB")
st.caption(f"Cost assumptions: {fuel_consumption:.2f} L/km and {fuel_price:,.2f} ETB/L. These are estimates, not actual fleet records.")

with st.expander("Review geocoded collection points / coordinate provenance", expanded=is_real):
    rows=[]
    for point in points:
        rows.append({"Location":point["name"],"Latitude":point.get("latitude"),"Longitude":point.get("longitude"),
                     "OSM matched place":point.get("geocoded_name","Not geocoded in simulated mode"),
                     "Data source":point["data_source"],"Query used":point.get("geocode_query","")})
    st.dataframe(pd.DataFrame(rows),use_container_width=True,hide_index=True)
    if is_real:
        st.caption("Coordinates are Nominatim's best match for each query. Confirm each matched place is suitable for a real collection stop before operational use.")

show_simulation = st.session_state.get("show_route_simulation", False)
simulation_trace = result.get("trace", [])
simulation_index = 0
if show_simulation and simulation_trace:
    st.markdown("### Route-finding simulation — step by step")
    st.caption("Each step shows the current candidate route. A restart means the current route reached a local optimum; the algorithm tries another shuffled order while retaining the best route found.")
    simulation_index = st.slider("Choose search iteration", min_value=0, max_value=len(simulation_trace)-1,
                                 value=min(st.session_state.get("simulation_index", 0), len(simulation_trace)-1),
                                 key="simulation_step_slider")
    step = simulation_trace[simulation_index]
    sim_a, sim_b, sim_c = st.columns(3)
    sim_a.metric("Step", f"{step['iteration']} / {result['iterations']}")
    sim_b.metric("Current route distance", f"{step['distance_km']:.2f} km")
    sim_c.metric("Best found so far", f"{step['best_distance_km']:.2f} km")
    st.info(f"Action: {step['action']}\n\nRoute: " + " → ".join(step["route"]))
    if st.button("Hide route-finding simulation"):
        st.session_state["show_route_simulation"] = False
        st.rerun()

# In simulation mode, the interactive map shows the selected step's route.
displayed_route = simulation_trace[simulation_index]["route"] if show_simulation and simulation_trace else result["best_route"]

tab_map,tab_route,tab_compare,tab_matrix,tab_method=st.tabs(["Interactive map","Optimized route","Before vs after","Distance matrix","How the AI works"])
with tab_map:
    st.markdown("#### Collection points and optimized route")
    if is_real:
        try:
            geometry=get_osrm_route_geometry(displayed_route,point_by_name)
            path_data=pd.DataFrame([{"path":geometry}])
            path_layer=pdk.Layer("PathLayer",data=path_data,get_path="path",get_width=5,width_min_pixels=3,
                                 get_color=[20,130,220],pickable=True)
            center_lat=sum(float(p["latitude"]) for p in points)/len(points)
            center_lon=sum(float(p["longitude"]) for p in points)/len(points)
            stops_data=pd.DataFrame([{"name":p["name"],"latitude":p["latitude"],"longitude":p["longitude"],
                                      "type":"Depot" if p["is_depot"] else "Collection stop",
                                      "matched":p.get("geocoded_name",p["name"])} for p in points])
            scatter=pdk.Layer("ScatterplotLayer",data=stops_data,get_position="[longitude, latitude]",get_radius=100,
                              get_fill_color=[220,70,50],pickable=True,auto_highlight=True)
            labels=pdk.Layer("TextLayer",data=stops_data,get_position="[longitude, latitude]",get_text="name",
                             get_size=14,get_alignment_baseline="bottom",pickable=True)
            deck=pdk.Deck(layers=[path_layer,scatter,labels],initial_view_state=pdk.ViewState(latitude=center_lat,longitude=center_lon,zoom=11,pitch=0),
                           tooltip={"text":"{name}\n{type}\n{matched}"},map_style="https://basemaps.cartocdn.com/gl/positron-gl-style/style.json")
            st.pydeck_chart(deck,use_container_width=True)
            st.caption("The blue path is OSRM's returned road geometry for the optimized stop order. The basemap is a third-party style; routing distances come from OSRM.")
        except (OSMRoutingError, KeyError, ValueError) as exc:
            st.warning(f"Could not fetch road geometry. Showing point map only. {exc}")
            st.map(pd.DataFrame([{"latitude":p["latitude"],"longitude":p["longitude"]} for p in points]))
    else:
        # Explicitly label schematic map: simulated points have no coordinates.
        schematic=pd.DataFrame([{"stop":i+1,"name":name,"x":i%4,"y":i//4} for i,name in enumerate(displayed_route[:-1])])
        fig=px.scatter(schematic,x="x",y="y",text="name",hover_name="name",title="Schematic order only — not a geographic map")
        fig.update_traces(textposition="top center")
        fig.update_layout(xaxis_title="Demo layout (not longitude)",yaxis_title="Demo layout (not latitude)")
        st.plotly_chart(fig,use_container_width=True)
        st.info("Select OpenStreetMap road distances and click Load data and optimize to see geocoded points and road geometry.")
with tab_route:
    st.markdown("#### Route found by Hill Climbing")
    st.code(" → ".join(displayed_route),language="text")
    if show_simulation:
        st.caption("The route above follows the selected simulation step; the final best route is shown in the performance overview.")
    st.markdown("#### Initial route")
    st.code(" → ".join(result["initial_route"]),language="text")
    route_rows=[]
    for i,(a,b) in enumerate(zip(displayed_route,displayed_route[1:]),start=1):
        route_rows.append({"Leg":i,"From":a,"To":b,"Distance (km)":distance_matrix[a][b],"Data mode":dataset["data_mode"]})
    st.dataframe(pd.DataFrame(route_rows),use_container_width=True,hide_index=True)
with tab_compare:
    comparison=pd.DataFrame({"Route":["Initial route","Best route found"],"Distance (km)":[initial_distance,final_distance],
                            "Estimated fuel cost (ETB)":[initial_cost["estimated_cost_etb"],final_cost["estimated_cost_etb"]]})
    left,right=st.columns(2)
    with left: st.plotly_chart(px.bar(comparison,x="Route",y="Distance (km)",title="Route distance comparison",text_auto=".2f"),use_container_width=True)
    with right: st.plotly_chart(px.bar(comparison,x="Route",y="Estimated fuel cost (ETB)",title="Estimated fuel cost",text_auto=".2f"),use_container_width=True)
    if saved_km>0: st.success(f"The search reduced this {dataset['data_mode'].lower()} route by {saved_km:.2f} km ({reduction_pct:.1f}%).")
    else: st.warning("No shorter route was found from this starting order. Hill Climbing can stop at a local optimum.")
with tab_matrix:
    st.markdown("#### Distance matrix")
    chosen=[depot_name]+active_selected
    st.dataframe(pd.DataFrame([{ "From / To":a,**{b:distance_matrix[a][b] for b in chosen}} for a in chosen]).set_index("From / To"),use_container_width=True)
    if is_real:
        st.caption("OSRM road distances are directed: A → B can differ from B → A because of one-way streets, turn restrictions, and road-network routing. This is expected for real road distances; do not force symmetry if you want realistic driving routes.")
    else:
        st.caption("SIMULATED matrix is symmetric by design: A → B equals B → A. These generated values are demo values, not actual road distances.")
with tab_method:
    st.markdown("""1. Start with the selected visiting order.
2. Sum the distances for each leg, including the return to the depot.
3. Generate neighboring routes by swapping two collection stops.
4. Evaluate every neighbor and accept the best shorter neighbor.
5. If a local optimum is reached, start a new shuffled route (random restart) while keeping the best route found.
6. Stop when the iteration budget is used. The iteration limit is a maximum, not a guarantee that every step improves the route.""")
    st.warning("Hill Climbing does not guarantee a globally shortest route. OSM geocoding may return an area/landmark centroid rather than a collection entrance. Validate points and routes before any real-world use.")
    st.json({"algorithm":result["algorithm"],"stop_reason":result["stop_reason"],"iterations":result["iterations"],
             "neighbors_evaluated":result["neighbors_evaluated"],"random_restarts":result.get("restarts",0),"data_mode":dataset["data_mode"],
             "run_timestamp":datetime.now().isoformat(timespec="seconds")})

st.markdown("### Recent optimization history")
history=get_recent_route_runs(limit=10)
if history:
    st.dataframe(pd.DataFrame([{"Run ID":r["id"],"Created at":r["created_at"],"Algorithm":r["algorithm"],
                               "Initial km":r["initial_distance_km"],"Best km":r["final_distance_km"],
                               "Iterations":r["iterations"],"Data mode":r["data_mode"]} for r in history]),use_container_width=True,hide_index=True)
else: st.info("No saved route runs yet.")
st.divider()
st.caption("Student prototype — not an official Addis Ababa municipal system. OSM attribution: © OpenStreetMap contributors. Public geocoding/routing services may be unavailable or rate-limited.")
