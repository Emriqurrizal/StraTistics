import os
import sys
import logging
import pandas as pd

# Suppress pandas warning
import warnings
warnings.filterwarnings('ignore')

# Add the parent directory to sys.path so we can import from ingestion when run via Airflow
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ingestion.strava_auth import StravaAuth
from ingestion.strava_api_client import StravaAPIClient
from ingestion.load_to_postgres import get_db_connection, upsert_activities, upsert_streams, upsert_gear, create_schema_if_not_exists

logging.basicConfig(level=logging.INFO, format='%(message)s')

def run_daily_sync():
    print("Authenticating with Strava API...")
    auth = StravaAuth()
    client = StravaAPIClient(auth)
    
    print("Connecting to PostgreSQL...")
    conn = get_db_connection()
    create_schema_if_not_exists(conn)

    print("Fetching your 30 most recent activities from Strava for daily sync...")
    # Fetch 30 most recent activities to ensure we don't miss any recent runs
    data = client._request("GET", "athlete/activities", params={'page': 1, 'per_page': 30})
    
    if not data:
        print("No activities found on Strava!")
        return
        
    print(f"Fetching details for {len(data)} activities...")
    detailed_activities = []
    seen_gear = set()
    
    for act in data:
        act_id = act['id']
        name = act.get('name', 'Unknown')
        print(f"Fetching detail for activity: {name} ({act_id})...")
        
        try:
            detailed_act = client.get_activity_detail(act_id)
            detailed_activities.append(detailed_act)
            
            gear_id = detailed_act.get('gear_id')
            if gear_id and gear_id not in seen_gear:
                print(f"Fetching gear details for gear_id: {gear_id}...")
                gear_data = client.get_gear(gear_id)
                upsert_gear(conn, gear_data)
                seen_gear.add(gear_id)
                
            print(f"Fetching streams (GPS/HR data) for activity: {name} ({act_id})...")
            streams_dict = client.get_activity_streams(act_id)
            
            if streams_dict:
                # Convert strava dict format into columnar dict for pandas
                df_dict = {k: v['data'] for k, v in streams_dict.items()}
                try:
                    df = pd.DataFrame(df_dict)
                    upsert_streams(conn, act_id, df)
                except Exception as e:
                    print(f"Skipping streams for {act_id} due to parsing error: {e}")
            else:
                print(f"No streams available for {act_id}")
                
        except Exception as e:
            print(f"Error processing activity {act_id}: {e}")
            conn.rollback()
            
    print(f"Upserting {len(detailed_activities)} detailed activities into bronze.raw_activities...")
    upsert_activities(conn, detailed_activities)
                
    conn.close()
    print("\nSUCCESS: Daily data ingested into the Bronze schema!")

if __name__ == '__main__':
    run_daily_sync()
