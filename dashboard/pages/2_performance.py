import streamlit as st
import pandas as pd
from db import run_query
from components.filters import render_sidebar_filters
from components.charts import create_time_series, create_scatter, create_histogram, create_donut
import plotly.express as px

st.title("2. Performance Analytics")

filters = render_sidebar_filters()
params = (filters['start_date'], filters['end_date'], filters['sport_types'], filters['workout_types'])

query_pace_trend = """
    SELECT 
        week_start_date as week,
        avg_pace_min_per_km as weekly_pace,
        rolling_4w_pace,
        rolling_8w_pace,
        rolling_12w_pace
    FROM metrics.pace_trend
    WHERE week_start_date BETWEEN %s AND %s
    ORDER BY week_start_date
"""
pace_df = run_query(query_pace_trend, (filters['start_date'], filters['end_date']))

if not pace_df.empty:
    fig1 = create_time_series(
        pace_df, 'week', 
        ['weekly_pace', 'rolling_4w_pace', 'rolling_8w_pace', 'rolling_12w_pace'],
        "Pace Trend (Weekly & Rolling Averages)",
        y_title="Pace (min/km)",
        inverted_y=True
    )
    st.plotly_chart(fig1, use_container_width=True)

col1, col2 = st.columns(2)

with col1:
    query_scatter = """
        SELECT 
            date_day, name, distance_km, avg_pace_min_per_km, average_heartrate,
            COALESCE(workout_type, 'Regular') as workout_type
        FROM public_gold.fct_activities
        WHERE date_day BETWEEN %s AND %s
        AND sport_type = ANY(%s)
        AND COALESCE(workout_type, 'Regular') = ANY(%s)
        AND avg_pace_min_per_km IS NOT NULL 
        AND average_heartrate IS NOT NULL
    """
    scatter_df = run_query(query_scatter, params)
    
    if not scatter_df.empty:
        fig2 = create_scatter(
            scatter_df, 'avg_pace_min_per_km', 'average_heartrate', 
            'workout_type', 'distance_km', ['name', 'date_day'],
            "Pace vs Heart Rate",
            inverted_y=True
        )
        # Update X axis to be inverted for Pace
        fig2.update_xaxes(autorange="reversed")
        st.plotly_chart(fig2, use_container_width=True)

with col2:
    query_hr_donut = """
        SELECT 
            zone,
            SUM(total_minutes_in_zone) as total_minutes
        FROM metrics.hr_zone_distribution
        WHERE date_day BETWEEN %s AND %s
        GROUP BY zone
        ORDER BY zone
    """
    donut_df = run_query(query_hr_donut, (filters['start_date'], filters['end_date']))
    
    if not donut_df.empty:
        fig3 = create_donut(donut_df, 'zone', 'total_minutes', "HR Zone Distribution (All Time)")
        st.plotly_chart(fig3, use_container_width=True)

col3, col4 = st.columns(2)

with col3:
    query_hr_area = """
        SELECT 
            date_day, zone, total_minutes_in_zone
        FROM metrics.hr_zone_distribution
        WHERE date_day BETWEEN %s AND %s
        ORDER BY date_day, zone
    """
    area_df = run_query(query_hr_area, (filters['start_date'], filters['end_date']))
    
    if not area_df.empty:
        fig4 = px.area(
            area_df, x="date_day", y="total_minutes_in_zone", color="zone",
            title="HR Zone Distribution Over Time (Normalized)",
            groupnorm="percent",
            color_discrete_sequence=px.colors.qualitative.Pastel
        )
        fig4.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color='#FAFAFA'))
        st.plotly_chart(fig4, use_container_width=True)

with col4:
    query_cadence = """
        SELECT average_cadence
        FROM public_gold.fct_activities
        WHERE date_day BETWEEN %s AND %s
        AND sport_type = ANY(%s)
        AND COALESCE(workout_type, 'Regular') = ANY(%s)
        AND average_cadence IS NOT NULL
    """
    cadence_df = run_query(query_cadence, params)
    
    if not cadence_df.empty:
        fig5 = create_histogram(cadence_df, 'average_cadence', "Cadence Distribution", ref_line=180.0)
        st.plotly_chart(fig5, use_container_width=True)
