PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS collection_points (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    location_type TEXT NOT NULL,
    admin_area TEXT NOT NULL,
    latitude REAL,
    longitude REAL,
    waste_volume_kg REAL NOT NULL DEFAULT 0 CHECK (waste_volume_kg >= 0),
    priority INTEGER NOT NULL DEFAULT 2 CHECK (priority BETWEEN 1 AND 5),
    is_depot INTEGER NOT NULL DEFAULT 0 CHECK (is_depot IN (0, 1)),
    data_source TEXT NOT NULL DEFAULT 'SIMULATED',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS distance_matrix (
    from_point_id INTEGER NOT NULL,
    to_point_id INTEGER NOT NULL,
    distance_km REAL NOT NULL CHECK (distance_km >= 0),
    data_source TEXT NOT NULL DEFAULT 'SIMULATED',
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (from_point_id, to_point_id),
    FOREIGN KEY (from_point_id) REFERENCES collection_points(id),
    FOREIGN KEY (to_point_id) REFERENCES collection_points(id)
);

CREATE TABLE IF NOT EXISTS trucks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    capacity_kg REAL NOT NULL CHECK (capacity_kg > 0),
    fuel_l_per_km REAL NOT NULL CHECK (fuel_l_per_km >= 0),
    is_active INTEGER NOT NULL DEFAULT 1 CHECK (is_active IN (0, 1)),
    data_source TEXT NOT NULL DEFAULT 'SIMULATED'
);

CREATE TABLE IF NOT EXISTS route_runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    algorithm TEXT NOT NULL,
    initial_route_json TEXT NOT NULL,
    final_route_json TEXT NOT NULL,
    initial_distance_km REAL NOT NULL CHECK (initial_distance_km >= 0),
    final_distance_km REAL NOT NULL CHECK (final_distance_km >= 0),
    iterations INTEGER NOT NULL CHECK (iterations >= 0),
    data_mode TEXT NOT NULL DEFAULT 'SIMULATED',
    settings_json TEXT NOT NULL DEFAULT '{}'
);
