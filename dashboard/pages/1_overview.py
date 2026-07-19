import streamlit as st
import pandas as pd
from db import run_query
from components.filters import render_sidebar_filters
from components.kpi_cards import render_kpi_row
from components.charts import (
    create_stacked_bar, create_time_series, create_calendar_heatmap,
    create_github_heatmap, create_donut, WORKOUT_COLOR_MAP
)
import plotly.express as px
from datetime import timedelta
import plotly.graph_objects as go

st.title("Overview")

# Sidebar filters
filters = render_sidebar_filters()

# Query KPI data based on filters
query_kpi = """
    SELECT 
        SUM(distance_km) as total_distance,
        COUNT(*) as total_runs,
        AVG(avg_pace_min_per_km) as avg_pace,
        SUM(moving_time_min) / 60.0 as total_duration_hr,
        SUM(elevation_m) as total_elevation
    FROM public_gold.fct_activities
    WHERE date_day BETWEEN %s AND %s
    AND sport_type = ANY(%s)
    AND COALESCE(workout_type, 'Regular') = ANY(%s)
"""
params = (filters['start_date'], filters['end_date'], filters['sport_types'], filters['workout_types'])
kpi_df = run_query(query_kpi, params)

window_days = filters['window_days']
prev_end_date = filters['start_date'] - timedelta(days=1)
prev_start_date = prev_end_date - timedelta(days=window_days)
prev_params = (prev_start_date, prev_end_date, filters['sport_types'], filters['workout_types'])
prev_kpi_df = run_query(query_kpi, prev_params)

if not kpi_df.empty:
    metrics = {
        "Total Distance": (kpi_df['total_distance'][0] or 0, 'km'),
        "Total Runs": (kpi_df['total_runs'][0] or 0, 'int'),
        "Avg Pace": (kpi_df['avg_pace'][0], 'pace'),
        "Total Duration": (kpi_df['total_duration_hr'][0] or 0, 'hrs'),
        "Total Elevation": (kpi_df['total_elevation'][0] or 0, 'm')
    }
    prev_metrics = None
    if not prev_kpi_df.empty:
        prev_metrics = {
            "Total Distance": (prev_kpi_df['total_distance'][0] or 0, 'km'),
            "Total Runs": (prev_kpi_df['total_runs'][0] or 0, 'int'),
            "Avg Pace": (prev_kpi_df['avg_pace'][0], 'pace'),
            "Total Duration": (prev_kpi_df['total_duration_hr'][0] or 0, 'hrs'),
            "Total Elevation": (prev_kpi_df['total_elevation'][0] or 0, 'm')
        }
    render_kpi_row(metrics, previous_metrics=prev_metrics)
    st.caption(f"*(Deltas compare vs prior {window_days} days)*")
else:
    st.info("No data available for the selected filters.")

st.markdown("---")

# 1. Distance Trend (Line)
st.subheader("Distance Trend")

if window_days <= 31:
    query_trend = """
        WITH daily AS (
            SELECT 
                date_day as date,
                total_distance_km as distance,
                AVG(total_distance_km) OVER (ORDER BY date_day ROWS BETWEEN 6 PRECEDING AND CURRENT ROW) as rolling_7d
            FROM public_gold.fct_daily_training_log
        )
        SELECT * FROM daily
        WHERE date BETWEEN %s AND %s
        ORDER BY date
    """
    trend_df = run_query(query_trend, (filters['start_date'], filters['end_date']))
    if not trend_df.empty:
        fig2 = create_time_series(trend_df, 'date', ['distance', 'rolling_7d'], "", "Distance (km)")
        st.plotly_chart(fig2, use_container_width=True)
else:
    query_trend = """
        WITH rolling AS (
            SELECT 
                week_start_date as date,
                total_distance_km as distance,
                AVG(total_distance_km) OVER (ORDER BY week_start_date ROWS BETWEEN 3 PRECEDING AND CURRENT ROW) as rolling_4w
            FROM public_gold.fct_weekly_summary
        )
        SELECT * FROM rolling
        WHERE date BETWEEN %s AND %s
        ORDER BY date
    """
    trend_df = run_query(query_trend, (filters['start_date'], filters['end_date']))
    if not trend_df.empty:
        fig2 = create_time_series(trend_df, 'date', ['distance', 'rolling_4w'], "", "Distance (km)")
        st.plotly_chart(fig2, use_container_width=True)

st.markdown("---")

# ─── Activity Heatmap ───
st.subheader("Activity Heatmap")

metric_cfg = {"sql_col": "SUM(distance_km)", "alias": "metric_value", "z_label": "Distance (km)"}

query_heatmap = f"""
    SELECT 
        date_day,
        {metric_cfg['sql_col']} as metric_value,
        STRING_AGG(DISTINCT COALESCE(workout_type, 'Regular'), ', ') as workout_types,
        CASE 
            WHEN SUM(distance_km) > 0 
            THEN ROUND((SUM(moving_time_min) / SUM(distance_km))::numeric, 2)
            ELSE NULL 
        END as avg_pace
    FROM public_gold.fct_activities
    WHERE date_day BETWEEN %s AND %s
    AND sport_type = ANY(%s)
    AND COALESCE(workout_type, 'Regular') = ANY(%s)
    GROUP BY date_day
    ORDER BY date_day
"""
heatmap_df = run_query(query_heatmap, params)

# Ensure all days in the filter range are present
full_date_range = pd.date_range(start=filters['start_date'], end=filters['end_date'])
if heatmap_df.empty:
    heatmap_df = pd.DataFrame(columns=['date_day', 'metric_value', 'workout_types', 'avg_pace'])

heatmap_df['date_day'] = pd.to_datetime(heatmap_df['date_day'])
heatmap_df = heatmap_df.set_index('date_day').reindex(full_date_range).rename_axis('date_day').reset_index()
heatmap_df['metric_value'] = heatmap_df['metric_value'].fillna(0)
heatmap_df['workout_types'] = heatmap_df['workout_types'].fillna('None')

if not heatmap_df.empty:
    # Format pace for hover display
    def _fmt_pace(p):
        if p is None or pd.isna(p):
            return "N/A"
        m, s = int(p), int((p - int(p)) * 60)
        return f"{m}:{s:02d} /km"
    
    heatmap_df['pace_str'] = heatmap_df['avg_pace'].apply(_fmt_pace)
    
    hover_extra = {'workout_types': 'Workout', 'pace_str': 'Pace'}
    
    # ── Dual-layout: 1D strip for ≤7 days, 2D calendar grid for 30+ days ──
    if window_days <= 7:
        fig_heatmap = create_github_heatmap(
            heatmap_df,
            x_col='date_day',
            z_col='metric_value',
            title="",
            z_label=metric_cfg['z_label'],
            hover_extra_cols=hover_extra
        )
    else:
        fig_heatmap = create_calendar_heatmap(
            heatmap_df,
            date_col='date_day',
            z_col='metric_value',
            title="",
            z_label=metric_cfg['z_label'],
            hover_extra=hover_extra
        )
        
    st.plotly_chart(fig_heatmap, use_container_width=True, config={'responsive': True, 'scrollZoom': False, 'displayModeBar': False})
else:
    st.info("No activity data for the selected period.")

st.markdown("---")

# 3. Workout Type Distribution (Donut)
st.subheader("Workout Type Distribution")

query_donut = """
    SELECT 
        COALESCE(workout_type, 'Regular') as workout_type,
        COUNT(*) as count
    FROM public_gold.fct_activities
    WHERE date_day BETWEEN %s AND %s
    AND sport_type = ANY(%s)
    AND COALESCE(workout_type, 'Regular') = ANY(%s)
    GROUP BY 1
"""
donut_df = run_query(query_donut, params)
if not donut_df.empty:
    fig_donut = create_donut(donut_df, names='workout_type', values='count', title="", color_discrete_map=WORKOUT_COLOR_MAP)
    st.plotly_chart(fig_donut, use_container_width=True)
