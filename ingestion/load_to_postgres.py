"""
load_to_postgres.py
Handles loading of Bronze data into PostgreSQL with idempotent upserts.
"""

import os
import pandas as pd
import json
import psycopg2
from psycopg2.extras import execute_values
import logging

logger = logging.getLogger(__name__)

def get_db_connection():
    return psycopg2.connect(
        host=os.getenv("POSTGRES_HOST"),
        port=os.getenv("POSTGRES_PORT", "5432"),
        dbname=os.getenv("POSTGRES_DB", "neondb"),
        user=os.getenv("POSTGRES_USER"),
        password=os.getenv("POSTGRES_PASSWORD"),
        sslmode=os.getenv("POSTGRES_SSLMODE", "require")
    )

def create_schema_if_not_exists(conn):
    with conn.cursor() as cur:
        cur.execute("CREATE SCHEMA IF NOT EXISTS bronze;")
        
        cur.execute("""
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
        """)
        
        cur.execute("""
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
        """)
        
        cur.execute("""
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
        """)
        
        cur.execute("""
            CREATE TABLE IF NOT EXISTS bronze.raw_gear (
                gear_id TEXT PRIMARY KEY,
                name TEXT,
                distance FLOAT,
                brand_name TEXT,
                model_name TEXT,
                retired BOOLEAN
            );
        """)
    conn.commit()

def upsert_activities(conn, activities_data: list):
    """Upserts a list of dictionaries into bronze.raw_activities."""
    if not activities_data:
        return

    # Assuming input is from API or slightly pre-processed dict
    # Extract keys present in raw_activities schema
    valid_cols = [
        'name', 'sport_type', 'start_date', 'distance', 'moving_time', 
        'elapsed_time', 'total_elevation_gain', 'average_speed', 'max_speed',
        'average_heartrate', 'max_heartrate', 'average_cadence', 'calories', 
        'gear_id', 'start_latlng', 'map_polyline', 'source'
    ]
    
    values = []
    actual_cols = set()
    
    for act in activities_data:
        strava_id = act.get('id', act.get('strava_id'))
        if not strava_id:
            continue
            
        row = {'strava_id': strava_id}
        for col in valid_cols:
            if col in act:
                val = act[col]
                if isinstance(val, (dict, list)):
                    val = json.dumps(val)
                row[col] = val
                actual_cols.add(col)
                
        # Also map type to sport_type if present
        if 'type' in act and 'sport_type' not in act:
            row['sport_type'] = act['type']
            actual_cols.add('sport_type')
            
        # map_polyline from map.summary_polyline
        if 'map' in act and isinstance(act['map'], dict) and 'summary_polyline' in act['map']:
            row['map_polyline'] = act['map']['summary_polyline']
            actual_cols.add('map_polyline')
            
        # Hardcode source as api if not provided
        if 'source' not in act:
            row['source'] = 'api'
            actual_cols.add('source')
            
        values.append(row)
        
    if not values:
        return
        
    db_columns = ['strava_id'] + list(actual_cols)
    
    tuples = []
    for row in values:
        tuples.append(tuple(row.get(col) for col in db_columns))
        
    query = f"""
        INSERT INTO bronze.raw_activities ({','.join(db_columns)})
        VALUES %s
        ON CONFLICT (strava_id) DO UPDATE SET
        {','.join([f"{col} = EXCLUDED.{col}" for col in db_columns if col != 'strava_id'])},
        ingested_at = NOW();
    """
    
    with conn.cursor() as cur:
        execute_values(cur, query, tuples)
    conn.commit()
    logger.info(f"Upserted {len(tuples)} activities.")

def upsert_streams(conn, strava_id: int, streams_df: pd.DataFrame, source: str = 'api'):
    """Upserts stream data (from DataFrame) into bronze.raw_streams."""
    if streams_df.empty:
        return
        
    df = streams_df.copy()
    df['strava_id'] = strava_id
    df['source'] = source
    
    if 'time' in df.columns:
        df = df.rename(columns={'time': 'time_offset'})
        
    df = df.where(pd.notnull(df), None)
    
    db_columns = [col for col in df.columns if col in [
        'strava_id', 'time_offset', 'heartrate', 'cadence', 'latitude', 
        'longitude', 'altitude', 'velocity', 'distance', 'source'
    ]]
    
    if 'time_offset' not in db_columns:
        logger.warning(f"No time_offset in streams for {strava_id}, skipping.")
        return
        
    values = [tuple(x) for x in df[db_columns].to_numpy()]
    
    query = f"""
        INSERT INTO bronze.raw_streams ({','.join(db_columns)})
        VALUES %s
        ON CONFLICT (strava_id, time_offset) DO UPDATE SET
        {','.join([f"{col} = EXCLUDED.{col}" for col in db_columns if col not in ['strava_id', 'time_offset']])},
        ingested_at = NOW();
    """
    
    with conn.cursor() as cur:
        execute_values(cur, query, values)
    conn.commit()
    logger.info(f"Upserted {len(values)} stream points for activity {strava_id}.")

def upsert_laps(conn, strava_id: int, laps_data: list):
    """Upserts lap data into bronze.raw_laps."""
    if not laps_data:
        return
        
    valid_cols = [
        'distance', 'elapsed_time', 'moving_time',
        'average_speed', 'average_heartrate', 'max_heartrate', 'average_cadence'
    ]
    
    values = []
    actual_cols = set(['lap_index'])
    
    for lap in laps_data:
        row = {'strava_id': strava_id}
        
        # Strava uses 'split' in splits_metric, and 'lap_index' in laps
        if 'split' in lap:
            row['lap_index'] = lap['split']
        elif 'lap_index' in lap:
            row['lap_index'] = lap['lap_index']
        else:
            continue
            
        for col in valid_cols:
            if col in lap:
                row[col] = lap[col]
                actual_cols.add(col)
        values.append(row)
        
    if not values:
        return
        
    db_columns = ['strava_id'] + list(actual_cols)
    tuples = []
    for row in values:
        tuples.append(tuple(row.get(col) for col in db_columns))
        
    query = f"""
        INSERT INTO bronze.raw_laps ({','.join(db_columns)})
        VALUES %s
        ON CONFLICT (strava_id, lap_index) DO UPDATE SET
        {','.join([f"{col} = EXCLUDED.{col}" for col in db_columns if col not in ['strava_id', 'lap_index']])};
    """
    
    with conn.cursor() as cur:
        execute_values(cur, query, tuples)
    conn.commit()
    logger.info(f"Upserted {len(tuples)} laps for activity {strava_id}.")

def upsert_gear(conn, gear_data: dict):
    """Upserts gear details into bronze.raw_gear."""
    if not gear_data:
        return
        
    valid_cols = ['name', 'brand_name', 'model_name', 'distance', 'retired']
    gear_id = gear_data.get('id')
    if not gear_id:
        return
        
    row = {'gear_id': gear_id}
    actual_cols = set()
    
    for col in valid_cols:
        if col in gear_data:
            row[col] = gear_data[col]
            actual_cols.add(col)
            
    db_columns = ['gear_id'] + list(actual_cols)
    tuples = [tuple(row.get(col) for col in db_columns)]
    
    query = f"""
        INSERT INTO bronze.raw_gear ({','.join(db_columns)})
        VALUES %s
        ON CONFLICT (gear_id) DO UPDATE SET
        {','.join([f"{col} = EXCLUDED.{col}" for col in db_columns if col != 'gear_id'])};
    """
    
    with conn.cursor() as cur:
        execute_values(cur, query, tuples)
    conn.commit()
    logger.info(f"Upserted gear {gear_id} ({row.get('name', 'Unknown')}).")

