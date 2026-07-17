import datetime
import streamlit as st
import pandas as pd
from db import run_query

def render_sidebar_filters():
    """Render the sidebar filters and return the selected values."""
    st.sidebar.header("Filters")
    
    # We query the max and min dates to set the default date range
    date_range_df = run_query("SELECT MIN(date_day) as min_date, MAX(date_day) as max_date FROM public_gold.fct_daily_training_log")
    
    if date_range_df.empty or pd.isna(date_range_df['min_date'].iloc[0]):
        default_start = datetime.date(2026, 4, 1)
        default_end = datetime.date.today()
    else:
        default_start = date_range_df['min_date'].iloc[0]
        default_end = date_range_df['max_date'].iloc[0]

    # Date Range
    date_range = st.sidebar.date_input(
        "Date Range",
        value=(default_start, default_end),
        min_value=datetime.date(2000, 1, 1),
        max_value=datetime.date.today() + datetime.timedelta(days=365)
    )
    
    if isinstance(date_range, tuple) and len(date_range) == 2:
        start_date, end_date = date_range
    else:
        start_date, end_date = default_start, default_end

    # Sport Type
    sport_types_df = run_query("SELECT DISTINCT sport_type FROM public_gold.fct_activities ORDER BY sport_type")
    available_sports = sport_types_df['sport_type'].tolist() if not sport_types_df.empty else ["Run"]
    
    default_sports = ["Run"] if "Run" in available_sports else available_sports
    selected_sports = st.sidebar.multiselect("Sport Type", options=available_sports, default=default_sports)
    
    # Workout Type
    workout_types_df = run_query("SELECT DISTINCT COALESCE(workout_type, 'Regular') as workout_type FROM public_gold.fct_activities ORDER BY workout_type")
    available_workouts = workout_types_df['workout_type'].tolist() if not workout_types_df.empty else ["Regular", "Race", "Long Run", "Workout"]
    
    selected_workouts = st.sidebar.multiselect("Workout Type", options=available_workouts, default=available_workouts)
    
    return {
        "start_date": start_date,
        "end_date": end_date,
        "sport_types": selected_sports if selected_sports else available_sports,
        "workout_types": selected_workouts if selected_workouts else available_workouts
    }
