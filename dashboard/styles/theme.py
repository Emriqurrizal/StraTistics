import streamlit as st

def apply_theme():
    """Apply global CSS overrides that respect Streamlit's active theme."""
    st.markdown("""
        <style>
        /* Metric cards custom styling */
        div[data-testid="metric-container"] {
            background-color: var(--secondary-background-color);
            border: 1px solid rgba(128, 128, 128, 0.2);
            padding: 1rem 1.5rem;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            transition: transform 0.2s ease-in-out;
            text-align: center;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
        }
        
        div[data-testid="metric-container"]:hover {
            transform: translateY(-2px);
        }
        
        div[data-testid="stMetricLabel"] > div, div[data-testid="stMetricValue"] > div {
            justify-content: center;
        }
        
        /* Hero Section */
        .hero-section {
            padding: 2rem 0;
            text-align: center;
            animation: fadeIn 0.8s ease-out;
        }
        .hero-title {
            font-size: 3.5rem;
            font-weight: 900;
            background: linear-gradient(90deg, #FC4C02, #FF8C00);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 0.5rem;
            letter-spacing: -1px;
        }
        .hero-subtitle {
            font-size: 1.25rem;
            color: var(--text-color);
            opacity: 0.8;
            margin-bottom: 2rem;
            font-weight: 400;
        }
        
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
        }

        /* Stat Cards highlight */
        .stat-highlight {
            color: #FC4C02;
            font-weight: bold;
        }
        
        </style>
    """, unsafe_allow_html=True)
