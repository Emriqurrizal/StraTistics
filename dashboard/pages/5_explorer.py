import streamlit as st
import pandas as pd
from db import run_query
from components.filters import render_sidebar_filters
import plotly.express as px
from components.charts import CHART_LAYOUT

st.title("Activity Explorer")
st.markdown("---")

filters = render_sidebar_filters()
params = (filters['start_date'], filters['end_date'], filters['sport_types'], filters['workout_types'])

st.subheader("Activity List")
query_activities = """
    SELECT 
        strava_id,
        date_day as date,
        name,
        sport_type,
        COALESCE(workout_type, 'Regular') as workout_type,
        distance_km,
        moving_time_min,
        avg_pace_min_per_km as pace,
        elevation_m as elevation,
        average_heartrate as avg_hr,
        gear_name as gear
    FROM public_gold.fct_activities
    WHERE date_day BETWEEN %s AND %s
    AND sport_type = ANY(%s)
    AND COALESCE(workout_type, 'Regular') = ANY(%s)
    ORDER BY date_day DESC
"""
activities_df = run_query(query_activities, params)

if not activities_df.empty:
    
    # Format pace helper for display dataframe
    def format_pace_str(pace_float):
        if pd.isna(pace_float): return ""
        m = int(pace_float)
        s = int((pace_float - m) * 60)
        return f"{m}:{s:02d}"
        
    # We create a display copy
    display_df = activities_df.copy()
    display_df['pace'] = display_df['pace'].apply(format_pace_str)
    
    # Use streamlit dataframe with column config
    st.dataframe(
        display_df.drop('strava_id', axis=1), # hide ID
        use_container_width=True,
        hide_index=True,
        column_config={
            "date": st.column_config.DateColumn("Date"),
            "distance_km": st.column_config.NumberColumn("Dist (km)", format="%.2f"),
            "moving_time_min": st.column_config.NumberColumn("Time (min)", format="%.1f"),
            "elevation": st.column_config.NumberColumn("Elev (m)", format="%d"),
            "avg_hr": st.column_config.NumberColumn("Avg HR (bpm)", format="%d"),
        }
    )

    st.markdown("---")
    st.markdown("### Select Activity for Split Analysis")
    
    # Allow user to pick an activity by name + date
    activity_options = activities_df.apply(lambda x: f"{x['date']} - {x['name']} ({x['distance_km']:.1f}km)", axis=1).tolist()
    
    selected_option = st.selectbox("Choose an activity:", activity_options)
    
    if selected_option:
        # Extract selected index
        idx = activity_options.index(selected_option)
        selected_id = str(activities_df.iloc[idx]['strava_id'])
        
        # Query splits for this activity
        query_splits = """
            SELECT 
                lap_index as lap,
                lap_distance_km,
                moving_time,
                average_heartrate,
                pace_min_per_km
            FROM public_silver.stg_splits
            WHERE strava_id = %s
            ORDER BY lap_index
        """
        # stg_splits might have strava_id as bigint or text, psycopg2 handles it
        splits_df = run_query(query_splits, (selected_id,))
        
        if not splits_df.empty:
            # Round numeric columns to 1 decimal place
            splits_df = splits_df.round(1)
            # Filter out laps with 0 distance
            splits_df = splits_df[splits_df['lap_distance_km'] > 0]
            
        if not splits_df.empty:
            st.markdown(f"**Lap Pacing for {selected_option}**")
            
            splits_df['speed'] = splits_df['pace_min_per_km'].apply(lambda x: 1/x if x > 0 else 0)
            max_speed = splits_df['speed'].max()
            
            html_lines = [
                '<div style="display: flex; align-items: center; margin-bottom: 8px; font-weight: bold; font-size: 0.85em; opacity: 0.7;">\n'
                '<div style="width: 30px; text-align: right; margin-right: 12px;">Lap</div>\n'
                '<div style="width: 45px; text-align: right; margin-right: 12px;">Dist</div>\n'
                '<div style="width: 45px; text-align: right; margin-right: 12px;">Pace</div>\n'
                '<div style="flex-grow: 1;"></div>\n'
                '<div style="width: 40px; text-align: right; margin-left: 12px;">HR</div>\n'
                '</div>'
            ]
            
            for _, row in splits_df.iterrows():
                lap_num = int(row['lap'])
                
                dist_float = row['lap_distance_km']
                dist_str = f"{dist_float:.2f}"
                
                pace_float = row['pace_min_per_km']
                m = int(pace_float)
                s = int((pace_float - m) * 60)
                pace_str = f"{m}:{s:02d}"
                
                hr = row['average_heartrate']
                hr_str = f"{int(hr)}" if pd.notna(hr) else "-"
                
                width_pct = (row['speed'] / max_speed) * 100 if max_speed > 0 else 0
                
                html_lines.append(f'''<div style="display: flex; align-items: center; margin-bottom: 8px;">
<div style="width: 30px; text-align: right; margin-right: 12px; opacity: 0.9;">{lap_num}</div>
<div style="width: 45px; text-align: right; margin-right: 12px; opacity: 0.9;">{dist_str}</div>
<div style="width: 45px; text-align: right; margin-right: 12px; font-variant-numeric: tabular-nums;">{pace_str}</div>
<div style="flex-grow: 1; height: 20px;">
<div style="width: {width_pct}%; height: 100%; background-color: #FC4C02; border-radius: 2px;"></div>
</div>
<div style="width: 40px; text-align: right; margin-left: 12px; opacity: 0.9;">{hr_str}</div>
</div>''')
                
            st.markdown("".join(html_lines), unsafe_allow_html=True)
            
        else:
            st.info("No lap data available for this activity (might be manual entry or no splits recorded).")

else:
    st.info("No activities found for the selected filters.")
