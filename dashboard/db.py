import os
import psycopg2
import pandas as pd
import streamlit as st
from dotenv import load_dotenv

# Load local .env if it exists (useful for local development)
# In production on Streamlit Cloud, it will use st.secrets
load_dotenv()

@st.cache_resource(validate=lambda conn: conn.closed == 0)
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
        port="5432",
        sslmode="require"
    )
    # Set autocommit for read-only analytical queries to prevent aborted transaction blocks
    conn.autocommit = True
    return conn

@st.cache_data(ttl=300)
def run_query(query: str, params: tuple = None) -> pd.DataFrame:
    """Run a read-only query and return a pandas DataFrame."""
    for attempt in range(2):
        conn = None
        try:
            conn = get_connection()
            if conn is None:
                st.error("Failed to obtain database connection.")
                return pd.DataFrame()
                
            with conn.cursor() as cur:
                cur.execute(query, params)
                if cur.description:
                    columns = [desc[0] for desc in cur.description]
                    data = cur.fetchall()
                    return pd.DataFrame(data, columns=columns)
                else:
                    return pd.DataFrame()
        except Exception as e:
            if conn is not None:
                try:
                    conn.rollback()
                except Exception:
                    pass
            
            # If the connection dropped, clear cache and retry once
            if attempt == 0 and ("SSL" in str(e) or "connection" in str(e).lower() or "closed" in str(e).lower()):
                get_connection.clear()
                continue
                
            st.error(f"Error executing query: {e}")
            return pd.DataFrame()
