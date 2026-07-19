import streamlit as st
import pandas as pd
from db import run_query
from components.filters import render_sidebar_filters
from components.charts import create_time_series, create_scatter, create_bar, create_donut, WORKOUT_COLOR_MAP, HR_ZONE_COLOR_MAP

st.title("Performance Analytics")
st.markdown("---")

#Sidebar filters
filters = render_sidebar_filters()
params = (filters['start_date'], filters['end_date'], filters['sport_types'], filters['workout_types'])

# 1.  pace trends
st.subheader("Pace Trends")

if filters['window_days'] <= 7:
    query_pace_trend = """
        WITH date_series AS (
            SELECT generate_series(%s::date, %s::date, '1 day'::interval)::date AS date_day
        )
        SELECT 
            d.date_day as date,
            p.avg_pace_min_per_km as weekly_pace,
            p.rolling_4w_pace,
            p.rolling_8w_pace,
            p.rolling_12w_pace
        FROM date_series d
        LEFT JOIN public_metrics.pace_trend p 
        ON date_trunc('week', d.date_day)::date = p.week_start_date
        ORDER BY d.date_day
    """
    pace_df = run_query(query_pace_trend, (filters['start_date'], filters['end_date']))

    if not pace_df.empty:
        fig1 = create_time_series(
            pace_df, 'date', 
            ['weekly_pace', 'rolling_4w_pace', 'rolling_8w_pace', 'rolling_12w_pace'],
            "",
            y_title="Pace (min/km)",
            inverted_y=False
        )
        st.plotly_chart(fig1, use_container_width=True)
else:
    query_pace_trend = """
        SELECT 
            week_start_date as week,
            avg_pace_min_per_km as weekly_pace,
            rolling_4w_pace,
            rolling_8w_pace,
            rolling_12w_pace
        FROM public_metrics.pace_trend
        WHERE week_start_date BETWEEN %s AND %s
        ORDER BY week_start_date
    """
    pace_df = run_query(query_pace_trend, (filters['start_date'], filters['end_date']))

    if not pace_df.empty:
        fig1 = create_time_series(
            pace_df, 'week', 
            ['weekly_pace', 'rolling_4w_pace', 'rolling_8w_pace', 'rolling_12w_pace'],
            " ",
            y_title="Pace (min/km)",
            inverted_y=False
        )
        st.plotly_chart(fig1, use_container_width=True)
        
st.markdown("---")

# 2. Pace vs Heart Rate Scatter Plot
st.subheader("Pace vs Heart Rate Scatter Plot")

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
        " ",
        inverted_y=False,
        color_discrete_map=WORKOUT_COLOR_MAP
    )
    # Update X axis to be inverted for Pace
    st.plotly_chart(fig2, use_container_width=True)

st.markdown("---")

# 3. HR Zone Distribution
st.subheader("Heart Rate Zone Distribution")

query_hr_donut = """
    SELECT 
        zone,
        SUM(total_minutes_in_zone) as total_minutes
    FROM public_metrics.hr_zone_distribution
    WHERE date_day BETWEEN %s AND %s
    GROUP BY zone
    ORDER BY zone DESC
"""
donut_df = run_query(query_hr_donut, (filters['start_date'], filters['end_date']))

if not donut_df.empty:
    fig3 = create_donut(
        donut_df, 'zone', 'total_minutes', " ", 
        color_discrete_map=HR_ZONE_COLOR_MAP,
        category_orders={"zone": ["Z5", "Z4", "Z3", "Z2", "Z1"]},
        sort=False
    )
    st.plotly_chart(fig3, use_container_width=True)

st.markdown("---")

# 5. Average Cadence per Workout Type
query_cadence = """
    SELECT 
        COALESCE(workout_type, 'Regular') as workout_type,
        AVG(average_cadence) as avg_cadence
    FROM public_gold.fct_activities
    WHERE date_day BETWEEN %s AND %s
    AND sport_type = ANY(%s)
    AND COALESCE(workout_type, 'Regular') = ANY(%s)
    AND average_cadence IS NOT NULL
    GROUP BY 1
    ORDER BY avg_cadence DESC
"""
cadence_df = run_query(query_cadence, params)

if not cadence_df.empty:
    fig5 = create_bar(
        cadence_df, 
        x='workout_type', 
        y='avg_cadence', 
        color='workout_type',
        title="Average Cadence per Workout Type",
        color_discrete_map=WORKOUT_COLOR_MAP
    )
    st.plotly_chart(fig5, use_container_width=True)
