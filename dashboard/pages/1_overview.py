import streamlit as st
import pandas as pd
from db import run_query
from components.filters import render_sidebar_filters
from components.kpi_cards import render_kpi_row
from components.charts import create_stacked_bar, create_time_series, create_heatmap
import plotly.express as px
import plotly.graph_objects as go

st.title("1. Overview")

# Sidebar filters
filters = render_sidebar_filters()

# Query KPI data based on filters
query_kpi = """
    SELECT 
        SUM(distance_km) as total_distance,
        COUNT(*) as total_runs,
        SUM(moving_time_min) / NULLIF(SUM(distance_km), 0) as avg_pace,
        SUM(elevation_m) as total_elevation,
        SUM(calories) as total_calories
    FROM public_gold.fct_activities
    WHERE date_day BETWEEN %s AND %s
    AND sport_type = ANY(%s)
    AND COALESCE(workout_type, 'Regular') = ANY(%s)
"""
params = (filters['start_date'], filters['end_date'], filters['sport_types'], filters['workout_types'])
kpi_df = run_query(query_kpi, params)

if not kpi_df.empty:
    metrics = {
        "Total Distance": (kpi_df['total_distance'][0] or 0, 'km'),
        "Total Runs": (kpi_df['total_runs'][0] or 0, 'int'),
        "Avg Pace": (kpi_df['avg_pace'][0], 'pace'),
        "Total Elevation": (kpi_df['total_elevation'][0] or 0, 'm'),
        "Total Calories": (kpi_df['total_calories'][0] or 0, 'int')
    }
    render_kpi_row(metrics)
else:
    st.info("No data available for the selected filters.")

st.markdown("---")

col1, col2 = st.columns(2)

with col1:
    # Monthly Volume (Stacked Bar)
    query_monthly = """
        SELECT 
            TO_CHAR(date_day, 'YYYY-MM') as month,
            COALESCE(workout_type, 'Regular') as workout,
            SUM(distance_km) as distance
        FROM public_gold.fct_activities
        WHERE date_day BETWEEN %s AND %s
        AND sport_type = ANY(%s)
        AND COALESCE(workout_type, 'Regular') = ANY(%s)
        GROUP BY 1, 2
        ORDER BY 1
    """
    monthly_df = run_query(query_monthly, params)
    if not monthly_df.empty:
        fig1 = create_stacked_bar(monthly_df, 'month', 'distance', 'workout', "Monthly Volume")
        st.plotly_chart(fig1, use_container_width=True)

with col2:
    # Weekly Distance Trend (Line)
    query_weekly = """
        SELECT 
            week_start_date as week,
            total_distance_km as distance,
            AVG(total_distance_km) OVER (ORDER BY week_start_date ROWS BETWEEN 3 PRECEDING AND CURRENT ROW) as rolling_4w
        FROM public_gold.fct_weekly_summary
        WHERE week_start_date BETWEEN %s AND %s
        ORDER BY week_start_date
    """
    weekly_df = run_query(query_weekly, (filters['start_date'], filters['end_date']))
    if not weekly_df.empty:
        fig2 = create_time_series(weekly_df, 'week', ['distance', 'rolling_4w'], "Weekly Distance Trend", "Distance (km)")
        st.plotly_chart(fig2, use_container_width=True)

st.markdown("---")

# Activity Calendar Heatmap
query_heatmap = """
    SELECT 
        date_day,
        total_distance_km
    FROM public_gold.fct_daily_training_log
    WHERE date_day BETWEEN %s AND %s
"""
heatmap_df = run_query(query_heatmap, (filters['start_date'], filters['end_date']))

if not heatmap_df.empty:
    heatmap_df['date_day'] = pd.to_datetime(heatmap_df['date_day'])
    heatmap_df['week'] = heatmap_df['date_day'].dt.isocalendar().week
    heatmap_df['year'] = heatmap_df['date_day'].dt.year
    heatmap_df['day_of_week'] = heatmap_df['date_day'].dt.dayofweek
    heatmap_df['day_name'] = heatmap_df['date_day'].dt.day_name()
    
    heatmap_df['week_idx'] = heatmap_df.groupby(['year', 'week']).ngroup()
    
    fig3 = px.scatter(
        heatmap_df, 
        x="week_idx", 
        y="day_name", 
        color="total_distance_km",
        size="total_distance_km",
        hover_data=["date_day"],
        color_continuous_scale="Oranges",
        title="Activity Calendar Heatmap"
    )
    fig3.update_yaxes(categoryorder='array', categoryarray=['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'])
    fig3.update_xaxes(showticklabels=False, title="")
    fig3.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color='#FAFAFA'))
    st.plotly_chart(fig3, use_container_width=True)
