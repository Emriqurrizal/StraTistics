import datetime
import streamlit as st
import pandas as pd
from db import run_query

def render_sidebar_filters():
    """Render the sidebar filters and return the selected values."""
    st.sidebar.header("Filters")
    
    # Date Range Dropdown
    date_options = ["7 days", "30 days", "3 months", "6 months", "YTD", "1 year"]
    selected_date_range = st.sidebar.selectbox("Date Range", options=date_options, index=0)
    
    today = datetime.date.today()
    end_date = today
    
    if selected_date_range == "7 days":
        start_date = today - datetime.timedelta(days=6)
    elif selected_date_range == "30 days":
        start_date = today - datetime.timedelta(days=29)
    elif selected_date_range == "3 months":
        start_date = today - datetime.timedelta(days=89)
    elif selected_date_range == "6 months":
        start_date = today - datetime.timedelta(days=179)
    elif selected_date_range == "YTD":
        start_date = datetime.date(today.year, 1, 1)
    elif selected_date_range == "1 year":
        start_date = today - datetime.timedelta(days=364)

    # Sport Type is hardcoded to "Run" since it's the only sport
    selected_sports = ["Run"]
    available_sports = ["Run"]
    
    # Workout Type
    workout_types_df = run_query("SELECT DISTINCT COALESCE(workout_type, 'Regular') as workout_type FROM public_gold.fct_activities ORDER BY workout_type")
    available_workouts = workout_types_df['workout_type'].tolist() if not workout_types_df.empty else ["Regular", "Race", "Long Run", "Workout"]
    
    selected_workouts = st.sidebar.multiselect("Workout Type", options=available_workouts, default=available_workouts)
    
    return {
        "start_date": start_date,
        "end_date": end_date,
        "sport_types": selected_sports if selected_sports else available_sports,
        "workout_types": selected_workouts if selected_workouts else available_workouts,
        "window_days": (end_date - start_date).days
    }
