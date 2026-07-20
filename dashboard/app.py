import streamlit as st
import pandas as pd
from styles.theme import apply_theme
from db import run_query

# Must be the first Streamlit command
st.set_page_config(
    page_title="StraTistics Dashboard",
    page_icon=None,
    layout="centered",
    initial_sidebar_state="expanded"
)

# Apply global styling
apply_theme()

st.sidebar.image("https://upload.wikimedia.org/wikipedia/commons/thumb/c/cb/Strava_Logo.svg/1024px-Strava_Logo.svg.png", width=150)
st.sidebar.title("StraTistics")
st.sidebar.markdown("End-to-end Strava running analytics pipeline.")

# ─── Data Fetching ───
@st.cache_data(ttl=300)
def get_lifetime_stats():
    query = """
        SELECT 
            COUNT(*) as total_runs,
            SUM(distance_km) as total_distance,
            SUM(moving_time_min) / 60.0 as total_hours
        FROM public_gold.fct_activities
        WHERE sport_type = 'Run'
    """
    return run_query(query)

@st.cache_data(ttl=300)
def get_latest_activity():
    query = """
        SELECT 
            name,
            date_day,
            distance_km,
            CASE 
                WHEN distance_km > 0 
                THEN (moving_time_min / distance_km)
                ELSE NULL 
            END as avg_pace
        FROM public_gold.fct_activities
        WHERE sport_type = 'Run'
        ORDER BY date_day DESC
        LIMIT 1
    """
    return run_query(query)

stats_df = get_lifetime_stats()
latest_df = get_latest_activity()

# ─── Hero Section ───
st.markdown("""
    <div class="hero-section">
        <div class="hero-title">StraTistics</div>
        <div class="hero-subtitle">Your personal, data-driven running command center</div>
    </div>
""", unsafe_allow_html=True)

# ─── Lifetime Stats ───
if not stats_df.empty:
    runs = int(stats_df['total_runs'][0] or 0)
    dist = int(stats_df['total_distance'][0] or 0)
    hours = int(stats_df['total_hours'][0] or 0)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Runs", f"{runs:,}")
    with col2:
        st.metric("Lifetime Distance", f"{dist:,} km")
    with col3:
        st.metric("Time on Feet", f"{hours:,} hrs")

st.markdown("<br>", unsafe_allow_html=True)

# ─── Latest Activity Highlight ───
if not latest_df.empty:
    latest = latest_df.iloc[0]
    name = latest['name']
    date = pd.to_datetime(latest['date_day']).strftime('%b %d, %Y')
    distance = latest['distance_km']
    pace_val = latest['avg_pace']
    
    pace_str = "N/A"
    if pace_val and not pd.isna(pace_val):
        m, s = int(pace_val), int((pace_val - int(pace_val)) * 60)
        pace_str = f"{m}:{s:02d} /km"

    with st.container(border=True):
        st.markdown(f"**Latest Activity:** {name} • {date} • <span class='stat-highlight'>{distance:.1f} km</span> @ <span class='stat-highlight'>{pace_str}</span>", unsafe_allow_html=True)

st.markdown("### Modules")

# ─── Navigation Grid ───
c1, c2 = st.columns(2)

with c1:
    with st.container(border=True):
        st.subheader("Overview")
        st.markdown("High-level KPIs, activity heatmap, and weekly trends.")
        st.page_link("pages/1_overview.py", label="Go to Overview")

    with st.container(border=True):
        st.subheader("Performance")
        st.markdown("Detailed pace and heart rate zone analytics over time.")
        st.page_link("pages/2_performance.py", label="Go to Performance")

with c2:
    with st.container(border=True):
        st.subheader("Training Load")
        st.markdown("Fitness (CTL), Fatigue (ATL), and Form (TSB) tracking.")
        st.page_link("pages/3_training_load.py", label="Go to Training Load")
        
    with st.container(border=True):
        st.subheader("Gear Tracker")
        st.markdown("Shoe mileage, active rotation, and lifecycle tracking.")
        st.page_link("pages/4_gear_tracker.py", label="Go to Gear Tracker")

with st.container(border=True):
    col_a, col_b = st.columns([1, 2])
    with col_a:
        st.subheader("Explorer")
        st.page_link("pages/5_explorer.py", label="Go to Explorer")
    with col_b:
        st.markdown("<div style='margin-top: 1rem;'>Interactive table of all your runs with advanced filtering and deep dives into lap pacing.</div>", unsafe_allow_html=True)
