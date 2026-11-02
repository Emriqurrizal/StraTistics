from typing import Any, Dict, Optional, Tuple
import pandas as pd
import streamlit as st


def _safe_float(val: Any) -> Optional[float]:
    """Safely cast metric value to float, normalizing None, NaN, and pd.NA.

    Why: Database queries (psycopg2) can return decimal.Decimal, None, or
    pandas can produce NaN/pd.NA when aggregations have zero matching rows.
    Explicit float conversion prevents cross-type TypeError during subtraction.
    """
    if val is None:
        return None
    try:
        if pd.isna(val):
            return None
    except (ValueError, TypeError):
        pass

    try:
        f = float(val)
        return None if (f != f) else f
    except (ValueError, TypeError):
        return None


def format_pace(pace_min_per_km: Any) -> str:
    """Format pace (float minutes per km) to M:SS string.

    Args:
        pace_min_per_km: Pace in minutes per kilometer.

    Returns:
        Formatted pace string (e.g. '5:30') or '0:00' if invalid or non-positive.
    """
    val = _safe_float(pace_min_per_km)
    if val is None or val <= 0:
        return "0:00"
    minutes = int(val)
    seconds = int(round((val - minutes) * 60))
    if seconds == 60:
        minutes += 1
        seconds = 0
    return f"{minutes}:{seconds:02d}"


def render_kpi_row(
    metrics: Dict[str, Tuple[Any, str]],
    previous_metrics: Optional[Dict[str, Tuple[Any, str]]] = None,
) -> None:
    """Render a responsive row of Streamlit KPI metric cards with delta indicators.

    Args:
        metrics: Current period metrics dict: {'Total Distance': (value, 'km'), ...}
        previous_metrics: Optional prior period metrics dict for comparison deltas.
    """
    if len(metrics) == 5:
        # Give more width to Total Distance and Total Duration so they don't get cut off
        cols = st.columns([1.4, 0.9, 1.0, 1.3, 1.1])
    else:
        cols = st.columns(len(metrics))

    for i, (key, (value, m_type)) in enumerate(metrics.items()):
        with cols[i]:
            curr_val = _safe_float(value)
            delta = None
            delta_color = "off"

            if previous_metrics and key in previous_metrics:
                prev_raw, _ = previous_metrics[key]
                prev_val = _safe_float(prev_raw)

                # Both values must be valid and positive to compute a meaningful delta
                if prev_val is not None and curr_val is not None:
                    if m_type == "pace":
                        if prev_val > 0 and curr_val > 0:
                            # Pace: lower is better; positive diff indicates improved speed
                            diff = prev_val - curr_val
                            if abs(diff) < 1e-4:
                                delta = "0:00"
                                delta_color = "off"
                            else:
                                direction = "faster" if diff > 0 else "slower"
                                delta = f"{format_pace(abs(diff))} {direction}"
                                delta_color = "normal" if diff > 0 else "inverse"
                    else:
                        if prev_val > 0:
                            diff = curr_val - prev_val
                            pct = (diff / prev_val) * 100.0

                            if round(pct, 1) == 0.0:
                                delta = "0.0%"
                                delta_color = "off"
                            else:
                                delta = f"{pct:.1f}%"
                                delta_color = "normal"

            # Format primary display value with null-safe defaults
            if m_type == "pace":
                formatted_val = format_pace(curr_val)
            elif curr_val is None:
                if m_type == "km":
                    formatted_val = "0.0 km"
                elif m_type == "m":
                    formatted_val = "0 m"
                elif m_type == "int":
                    formatted_val = "0"
                elif m_type == "hrs":
                    formatted_val = "0.0 hrs"
                else:
                    formatted_val = "-"
            else:
                if m_type == "km":
                    formatted_val = f"{curr_val:.1f} km"
                elif m_type == "m":
                    formatted_val = f"{curr_val:,.0f} m"
                elif m_type == "int":
                    formatted_val = f"{int(curr_val):,}"
                elif m_type == "hrs":
                    formatted_val = f"{curr_val:.1f} hrs"
                else:
                    formatted_val = str(value)

            st.metric(label=key, value=formatted_val, delta=delta, delta_color=delta_color)
