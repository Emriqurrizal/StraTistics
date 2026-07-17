import streamlit as st

def format_pace(pace_min_per_km: float) -> str:
    """Format pace (float minutes) to M:SS string."""
    if pace_min_per_km is None or pace_min_per_km != pace_min_per_km: # Handle None or NaN
        return "0:00"
    minutes = int(pace_min_per_km)
    seconds = int((pace_min_per_km - minutes) * 60)
    return f"{minutes}:{seconds:02d}"

def render_kpi_row(metrics: dict, previous_metrics: dict = None):
    """
    Render a row of KPI cards.
    metrics dict format: {'Total Distance': (value, 'km'), 'Avg Pace': (value, 'pace')}
    """
    cols = st.columns(len(metrics))
    
    for i, (key, (value, m_type)) in enumerate(metrics.items()):
        with cols[i]:
            delta = None
            if previous_metrics and key in previous_metrics:
                prev_val, _ = previous_metrics[key]
                if prev_val:
                    if m_type == 'pace':
                        # Pace: lower is better
                        diff = prev_val - value
                        # Need to be careful with formatting logic for delta string
                        if diff == 0:
                            delta = "0:00"
                            delta_color = "off"
                        else:
                            delta = f"{format_pace(abs(diff))} {'faster' if diff > 0 else 'slower'}"
                            delta_color = "normal" if diff > 0 else "inverse"
                    else:
                        diff = value - prev_val
                        pct = (diff / prev_val) * 100 if prev_val else 0
                        delta = f"{pct:.1f}%"
                        delta_color = "normal"
            else:
                delta_color = "off"
            
            # Format value
            if m_type == 'pace':
                formatted_val = format_pace(value)
            elif m_type == 'km':
                formatted_val = f"{value:.1f} km"
            elif m_type == 'm':
                formatted_val = f"{value:,.0f} m"
            elif m_type == 'int':
                formatted_val = f"{int(value):,}"
            else:
                formatted_val = str(value)
                
            st.metric(label=key, value=formatted_val, delta=delta, delta_color=delta_color)
