import streamlit as st
from styles.theme import apply_theme

# Must be the first Streamlit command
st.set_page_config(
    page_title="StraTistics Dashboard",
    page_icon="🏃",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Apply global styling
apply_theme()

st.sidebar.image("https://upload.wikimedia.org/wikipedia/commons/thumb/c/cb/Strava_Logo.svg/1024px-Strava_Logo.svg.png", width=150)
st.sidebar.title("StraTistics")
st.sidebar.markdown("End-to-end Strava running analytics pipeline.")

st.title("Welcome to StraTistics")
st.markdown("""
Use the sidebar on the left to navigate through the dashboard pages:

- **1 Overview**: High-level KPIs and monthly/weekly trends
- **2 Performance**: Detailed pace and heart rate analytics
- **3 Training Load**: CTL/ATL/TSB Performance Management Chart
- **4 Gear Tracker**: Shoe mileage and rotation tracking
- **5 Explorer**: Interactive activity data table
""")
