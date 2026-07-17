import streamlit as st

def apply_theme():
    """Apply global CSS overrides for a glassmorphism aesthetic."""
    st.markdown("""
        <style>
        /* Main background */
        .stApp {
            background-color: #0E1117;
        }
        
        /* Metric cards glassmorphism */
        div[data-testid="metric-container"] {
            background-color: rgba(26, 29, 35, 0.7);
            border: 1px solid rgba(255, 255, 255, 0.1);
            padding: 1rem 1.5rem;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            backdrop-filter: blur(10px);
            -webkit-backdrop-filter: blur(10px);
            transition: transform 0.2s ease-in-out;
        }
        
        div[data-testid="metric-container"]:hover {
            transform: translateY(-2px);
        }
        
        /* Hide sidebar completely if closed, style if open */
        [data-testid="stSidebar"] {
            background-color: rgba(14, 17, 23, 0.95);
            border-right: 1px solid rgba(255, 255, 255, 0.05);
        }
        </style>
    """, unsafe_allow_html=True)
