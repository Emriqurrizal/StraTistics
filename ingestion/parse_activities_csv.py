"""
parse_activities_csv.py
Parses the activities.csv from the Strava bulk export into a standard format.
"""

import pandas as pd
import os
from typing import Optional

def parse_activities_csv(filepath: str) -> Optional[pd.DataFrame]:
    """Reads activities.csv from the bulk export into a DataFrame matching bronze.raw_activities schema as closely as possible."""
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"CSV file not found: {filepath}")
        
    try:
        df = pd.read_csv(filepath)
    except Exception as e:
        print(f"Error reading {filepath}: {e}")
        return None
        
    # Mapping based on typical Strava bulk export CSV
    rename_map = {
        'Activity ID': 'strava_id',
        'Activity Name': 'name',
        'Activity Type': 'sport_type',
        'Activity Date': 'start_date',
        'Distance': 'distance', 
        'Moving Time': 'moving_time', 
        'Elapsed Time': 'elapsed_time', 
        'Elevation Gain': 'total_elevation_gain', 
        'Average Speed': 'average_speed', 
        'Max Speed': 'max_speed',
        'Average Heart Rate': 'average_heartrate',
        'Max Heart Rate': 'max_heartrate',
        'Average Cadence': 'average_cadence',
        'Calories': 'calories',
        'Gear': 'gear_name' # Note: Bulk export has name, API has ID.
    }
    
    df.rename(columns=rename_map, inplace=True, errors='ignore')
    
    if 'strava_id' in df.columns:
        df['source'] = 'bulk_export'
        
    # Filter to only the columns we renamed/added, plus Filename if present
    columns_to_keep = list(rename_map.values()) + ['source', 'Filename']
    existing_cols = [col for col in columns_to_keep if col in df.columns]
    
    return df[existing_cols]

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        df = parse_activities_csv(sys.argv[1])
        if df is not None:
            print(df.head())
