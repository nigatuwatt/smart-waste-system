# Smart Waste Collection and Route Optimization System for Addis Ababa City

A beginner-friendly, modular Python + Streamlit prototype that demonstrates Hill Climbing for waste-collection route-order optimization.

## Important data disclaimer

This version uses **SIMULATED DATA**. It includes names of Addis Ababa sub-cities and well-known area labels to make the demo relatable. However:

- The generated distances are fictional and are not verified road distances.
- The sample labels do not claim that every named place is an official collection site.
- Mexico Square and 4 Kilo are labeled as areas/landmarks, not sub-cities.
- Fuel use and fuel price are configurable illustrative assumptions, not current verified fleet data.
- The app is a student prototype, not an official municipal system.

The official Addis Ababa administrative names can change over time. Check current city-administration sources before treating the sample list as an authoritative administrative reference.

## Features

- Streamlit dashboard
- Reproducible simulated distance matrix
- Route distance calculation, including return to depot
- Pair-swap neighbor generation
- Random-restart steepest-improvement Hill Climbing for minimizing route distance
- Step-by-step route-finding simulation with per-iteration route and distance
- Search trace showing improvements, local optima, random restarts, and the best route found
- Initial-versus-best route comparison
- Configurable fuel-use and fuel-price estimates
- SQLite database for sample locations, distances, truck, and route-run history
- Recent optimization history table in the dashboard
- Automated tests with pytest

## Project structure

```text
smart_waste_system/
├── app.py
├── config.py
├── requirements.txt
├── data/
│   └── sample_data.py
├── algorithms/
│   ├── hill_climbing.py
│   └── route_utils.py
├── database/
│   ├── db.py
│   └── schema.sql
├── services/
│   ├── route_service.py
│   └── cost_service.py
├── tests/
│   ├── test_routes.py
│   └── test_hill_climbing.py
└── README.md
```

## Requirements

- Python 3.10 or newer recommended
- Internet connection for the first-time installation of Python packages

## Setup on Windows

Open Command Prompt or PowerShell in the folder containing `app.py`.

1. Create a virtual environment:

   ```bash
   python -m venv .venv
   ```

2. Activate it:

   **Command Prompt**
   ```bash
   .venv\Scripts\activate
   ```

   **PowerShell**
   ```powershell
   .\.venv\Scripts\Activate.ps1
   ```

3. Install dependencies:

   ```bash
   python -m pip install --upgrade pip
   pip install -r requirements.txt
   ```

4. Run the tests:

   ```bash
   python -m pytest -q
   ```

5. Start the dashboard:

   ```bash
   streamlit run app.py
   ```

Streamlit will print a local URL, usually `http://localhost:8501`. Open it in your browser.

## Setup on macOS or Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
python -m pytest -q
streamlit run app.py
```

## How the algorithm works

1. The route starts at the demo depot.
2. The truck visits every selected stop once.
3. The route returns to the depot.
4. The algorithm generates neighbors by swapping two intermediate stops.
5. It evaluates the total distance for every neighbor.
6. It moves to the shortest neighbor only if that route is strictly shorter.
7. It stops at a local optimum or the configured iteration limit.

**Hill Climbing does not guarantee the globally shortest route.** It finds an improved route based on the current starting route and neighborhood definition.

## Database

The database file `smart_waste_system.db` is created in the current working directory on first launch. It contains:

- `collection_points`
- `distance_matrix`
- `trucks`
- `route_runs`

The initial sample records are inserted only if the collection-points table is empty. Do not delete the database unless you are happy to recreate the initial sample dataset.

## Limitations and future work

This prototype optimizes the order of visits using a supplied distance matrix. It does not currently:
- fetch real road-network distances,
- use live traffic,
- allocate many trucks across a city,
- enforce truck capacity during route construction,
- schedule collection time windows,
- track live GPS positions,
- or authenticate multiple user roles.

The project already includes an optional OpenStreetMap geocoding + OSRM road-distance mode and a route map. Use verified collection-point coordinates, review matched places, and respect provider attribution/rate limits before operational use. Real route distances should replace simulated values before making operational claims.

## Suggested academic evaluation

For a fair comparison:
1. Use the same simulated matrix for each algorithm.
2. Run multiple initial routes.
3. Record the initial distance, best distance, iterations, and execution time.
4. Compare Hill Climbing with a baseline such as Nearest Neighbor.
5. Explain that local-optimum results are not proof of a global optimum.


## Understanding the distance matrix

- In **simulated mode**, the matrix is symmetric by design: `distance[A][B] == distance[B][A]`. It is generated sample data only.
- In **OpenStreetMap/OSRM mode**, the matrix is directed. `A -> B` may differ from `B -> A` because of one-way streets, turn restrictions, and the driving road network. This is expected and should not be forced to symmetry when optimizing realistic driving routes.
- The app's matrix tab explains which mode is active. The route objective sums each directed leg in the order the truck drives it.

## OpenStreetMap + OSRM integration (new)

The dashboard supports two modes:

- **OpenStreetMap road distances**: after clicking `Load data and optimize`, selected place names are geocoded using Nominatim; OSRM provides a road-distance matrix and road geometry. The resolved place names and coordinates are displayed for review.
- **Simulated demo data**: synthetic distance matrix retained for offline demos and tests. It is always labelled simulated.

If any geocoding or OSRM request fails, the app displays an explicit error and uses the simulated dataset as a fallback. Check the visible data-mode notice before quoting results. The public Nominatim service is rate-limited (maximum one request per second), requires a meaningful User-Agent, and requires caching and attribution. This app makes requests only after a deliberate button click and caches geocoding responses in `data/geocode_cache.json`. Read the [Nominatim usage policy](https://operations.osmfoundation.org/policies/nominatim/) before using it. OSRM road distances use its table service; see [OSRM API documentation](https://project-osrm.org/docs/v5.24.0/api/).

### Windows setup (PowerShell)

1. Install Python 3.11 or 3.12 and select **Add Python to PATH** in the installer.
2. Extract the ZIP, open PowerShell, and change into the `smart_waste_system` folder.
3. Run:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
pytest -q
streamlit run app.py
```

If PowerShell blocks activation, use `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` in that same PowerShell window, then activate again. To run offline, choose **Simulated demo data**.

### Accuracy notes

Nominatim returns its best matching OSM feature for each area query. A sub-city or landmark match can be a centroid or an approximate point, not an exact waste-bin/curbside location. Inspect the returned `OSM matched place`, then replace area queries with exact, verified collection-point addresses or coordinates for a real pilot. OSRM distance means distance along the configured drivable road graph; it is not a promise of live traffic, truck restrictions, or municipal access. The public OSRM demo server has no production SLA.
