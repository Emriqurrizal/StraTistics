import os
import psycopg2
import pandas as pd
import streamlit as st
from dotenv import load_dotenv

# Load local .env if it exists (useful for local development)
# In production on Streamlit Cloud, it will use st.secrets
load_dotenv()

@st.cache_resource
def get_connection():
    # Try getting from st.secrets first (for Streamlit Cloud), then os.environ (local)
    try:
        user = st.secrets.get("POSTGRES_USER")
        password = st.secrets.get("POSTGRES_PASSWORD")
        host = st.secrets.get("POSTGRES_HOST")
        dbname = st.secrets.get("POSTGRES_DB")
    except Exception:
        user = None
        password = None
        host = None
        dbname = None

    if not all([user, password, host, dbname]):
        user = os.environ.get("POSTGRES_USER")
        password = os.environ.get("POSTGRES_PASSWORD")
        host = os.environ.get("POSTGRES_HOST")
        dbname = os.environ.get("POSTGRES_DB")

    if not all([user, password, host, dbname]):
        st.error("Database credentials not found. Please set POSTGRES_* environment variables or Streamlit secrets.")
        st.stop()

    conn = psycopg2.connect(
        user=user,
        password=password,
        host=host,
        dbname=dbname,
        port="5432"
    )
    # Set autocommit for read-only analytical queries to prevent aborted transaction blocks
    conn.autocommit = True
    return conn

@st.cache_data(ttl=300)
def run_query(query: str, params: tuple = None) -> pd.DataFrame:
    """Run a read-only query and return a pandas DataFrame."""
    conn = get_connection()
    with conn.cursor() as cur:
        try:
            cur.execute(query, params)
            if cur.description:
                columns = [desc[0] for desc in cur.description]
                data = cur.fetchall()
                return pd.DataFrame(data, columns=columns)
            else:
                return pd.DataFrame()
        except Exception as e:
            conn.rollback()
            st.error(f"Error executing query: {e}")
            return pd.DataFrame()
