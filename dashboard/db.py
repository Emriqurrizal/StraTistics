import os
import time
import psycopg2
import pandas as pd
import streamlit as st
from dotenv import load_dotenv

# Load local .env if it exists (useful for local development)
# In production on Streamlit Cloud, it will use st.secrets
load_dotenv()


def _is_connection_alive(conn) -> bool:
    """Validate database connection by running a lightweight ping query.
    This prevents stale/closed connection errors when Neon DB wakes up from auto-suspend.
    """
    if conn is None:
        return False
    try:
        if hasattr(conn, "closed") and conn.closed != 0:
            return False
        with conn.cursor() as cur:
            cur.execute("SELECT 1;")
        return True
    except Exception:
        return False


@st.cache_resource(validate=_is_connection_alive)
def get_connection():
    """Establishes and caches PostgreSQL database connection.
    Uses st.secrets first (Streamlit Cloud), then os.environ (local).
    Validates connection health before returning cached instance.
    """
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
        sslmode="require",
        connect_timeout=10
    )
    # Set autocommit for read-only analytical queries to prevent aborted transaction blocks
    conn.autocommit = True
    return conn


def _make_hashable(obj):
    """Recursively convert mutable structures (lists, dicts) into immutable hashable tuples
    so st.cache_data can generate reliable cache keys.
    """
    if isinstance(obj, list):
        return tuple(_make_hashable(e) for e in obj)
    if isinstance(obj, dict):
        return tuple((k, _make_hashable(v)) for k, v in sorted(obj.items()))
    return obj


@st.cache_data(ttl=3600, show_spinner=False)
def _run_query_internal(query: str, params: tuple = None) -> pd.DataFrame:
    """Internal cached query execution.
    Results are cached in Streamlit for 1 hour (3600s) to minimize DB hits on Neon DB free tier.
    Includes auto-retry with exponential backoff to handle Neon DB cold starts.
    """
    max_retries = 3
    for attempt in range(max_retries):
        conn = None
        try:
            conn = get_connection()
            if conn is None:
                raise Exception("Failed to obtain database connection.")

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

            # If connection dropped or Neon DB is waking from sleep, clear connection cache & retry
            if attempt < max_retries - 1:
                get_connection.clear()
                time.sleep(1.5 * (attempt + 1))
                continue

            raise e


def run_query(query: str, params: tuple = None) -> pd.DataFrame:
    """Run a read-only query and return a pandas DataFrame.
    Automatically converts parameters to hashable formats for st.cache_data.
    """
    try:
        hashable_params = _make_hashable(params) if params is not None else None
        return _run_query_internal(query, hashable_params)
    except Exception as e:
        st.error(f"Error executing query: {e}")
        return pd.DataFrame()


def clear_db_cache():
    """Clear all cached queries and database connection resources."""
    get_connection.clear()
    _run_query_internal.clear()
    st.cache_data.clear()
