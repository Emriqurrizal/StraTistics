import streamlit as st
import pandas as pd
from db import run_query
from components.filters import render_sidebar_filters
import plotly.express as px
from components.charts import CHART_LAYOUT

st.title("5. Activity Explorer")

filters = render_sidebar_filters()
params = (filters['start_date'], filters['end_date'], filters['sport_types'], filters['workout_types'])

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
            "avg_hr": st.column_config.NumberColumn("HR (bpm)", format="%d"),
        }
    )
    
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
                split_number as lap,
                distance_km,
                moving_time_min,
                average_speed_m_s,
                average_heartrate,
                elevation_difference_m,
                pace_min_per_km
            FROM public_silver.stg_splits
            WHERE strava_id = %s
            ORDER BY split_number
        """
        # stg_splits might have strava_id as bigint or text, psycopg2 handles it
        splits_df = run_query(query_splits, (selected_id,))
        
        if not splits_df.empty:
            st.markdown(f"**Lap Pacing for {selected_option}**")
            
            fig = px.bar(
                splits_df,
                x='lap',
                y='pace_min_per_km',
                color='average_heartrate',
                color_continuous_scale='Inferno',
                labels={'lap': 'Lap Number', 'pace_min_per_km': 'Pace (min/km)'},
                hover_data=['distance_km', 'elevation_difference_m']
            )
            
            # Invert y-axis so faster pace (lower number) is visually higher
            fig.update_yaxes(autorange="reversed")
            fig.update_layout(**CHART_LAYOUT)
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Show raw splits table
            st.dataframe(splits_df, use_container_width=True, hide_index=True)
        else:
            st.info("No lap data available for this activity (might be manual entry or no splits recorded).")

else:
    st.info("No activities found for the selected filters.")
