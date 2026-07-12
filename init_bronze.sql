CREATE SCHEMA IF NOT EXISTS bronze;

CREATE TABLE IF NOT EXISTS bronze.raw_activities (
    strava_id BIGINT PRIMARY KEY,
    name TEXT,
    sport_type TEXT,
    start_date TIMESTAMPTZ,
    distance FLOAT,
    moving_time INT,
    elapsed_time INT,
    total_elevation_gain FLOAT,
    average_speed FLOAT,
    max_speed FLOAT,
    average_heartrate FLOAT,
    max_heartrate FLOAT,
    average_cadence FLOAT,
    calories FLOAT,
    gear_id TEXT,
    start_latlng JSONB,
    map_polyline TEXT,
    source TEXT,
    ingested_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS bronze.raw_streams (
    strava_id BIGINT,
    time_offset INT,
    heartrate FLOAT,
    cadence FLOAT,
    latitude FLOAT,
    longitude FLOAT,
    altitude FLOAT,
    velocity FLOAT,
    distance FLOAT,
    source TEXT,
    ingested_at TIMESTAMPTZ DEFAULT NOW(),
    PRIMARY KEY (strava_id, time_offset)
);

CREATE TABLE IF NOT EXISTS bronze.raw_laps (
    strava_id BIGINT,
    lap_index INT,
    distance FLOAT,
    elapsed_time INT,
    moving_time INT,
    average_speed FLOAT,
    average_heartrate FLOAT,
    max_heartrate FLOAT,
    average_cadence FLOAT,
    PRIMARY KEY (strava_id, lap_index)
);

CREATE TABLE IF NOT EXISTS bronze.raw_gear (
    gear_id TEXT PRIMARY KEY,
    name TEXT,
    distance FLOAT,
    brand_name TEXT,
    model_name TEXT,
    retired BOOLEAN
);
