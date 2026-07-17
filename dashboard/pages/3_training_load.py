import streamlit as st
import pandas as pd
from db import run_query
from components.filters import render_sidebar_filters
import plotly.graph_objects as go
from components.charts import CHART_LAYOUT

st.title("3. Training Load (PMC)")

filters = render_sidebar_filters()

query_pmc = """
    SELECT 
        date_day,
        daily_distance,
        ctl,
        atl,
        tsb
    FROM metrics.training_load
    WHERE date_day BETWEEN %s AND %s
    ORDER BY date_day
"""
pmc_df = run_query(query_pmc, (filters['start_date'], filters['end_date']))

if not pmc_df.empty:
    # Latest TSB Status Indicator
    latest_tsb = pmc_df['tsb'].iloc[-1]
    
    if pd.isna(latest_tsb):
        status_text = "No TSB data available"
        status_color = "grey"
    elif latest_tsb > 25:
        status_text = f"Current TSB: {latest_tsb:.1f} → 📉 DETRAINING — Loss of fitness"
        status_color = "orange"
    elif latest_tsb > 5:
        status_text = f"Current TSB: {latest_tsb:.1f} → 🟢 FRESH — Ready to race or hard workout"
        status_color = "green"
    elif latest_tsb >= -10:
        status_text = f"Current TSB: {latest_tsb:.1f} → 🟡 OPTIMAL — Productive training zone"
        status_color = "yellow"
    elif latest_tsb >= -30:
        status_text = f"Current TSB: {latest_tsb:.1f} → 🟠 HEAVY — Accumulated fatigue, consider recovery"
        status_color = "orange"
    else:
        status_text = f"Current TSB: {latest_tsb:.1f} → 🔴 OVERREACHING — High risk of injury/illness"
        status_color = "red"
        
    st.markdown(f"### {status_text}")

    # Plot PMC
    fig = go.Figure()
    
    # Background TSB zones
    fig.add_hrect(y0=25, y1=50, fillcolor="orange", opacity=0.1, line_width=0, layer="below")
    fig.add_hrect(y0=5, y1=25, fillcolor="green", opacity=0.1, line_width=0, layer="below")
    fig.add_hrect(y0=-10, y1=5, fillcolor="yellow", opacity=0.1, line_width=0, layer="below")
    fig.add_hrect(y0=-30, y1=-10, fillcolor="orange", opacity=0.1, line_width=0, layer="below")
    fig.add_hrect(y0=-50, y1=-30, fillcolor="red", opacity=0.1, line_width=0, layer="below")

    # TSB (Area)
    fig.add_trace(go.Scatter(
        x=pmc_df['date_day'], y=pmc_df['tsb'],
        mode='lines',
        name='TSB (Form)',
        line=dict(color='rgba(255, 255, 255, 0)'), # hide line
        fill='tozeroy',
        fillcolor='rgba(255, 200, 0, 0.3)'
    ))
    
    # CTL (Fitness)
    fig.add_trace(go.Scatter(
        x=pmc_df['date_day'], y=pmc_df['ctl'],
        mode='lines',
        name='CTL (Fitness)',
        line=dict(color='#2196F3', width=2)
    ))
    
    # ATL (Fatigue)
    fig.add_trace(go.Scatter(
        x=pmc_df['date_day'], y=pmc_df['atl'],
        mode='lines',
        name='ATL (Fatigue)',
        line=dict(color='#E91E63', width=2)
    ))
    
    # Daily distance bars on secondary axis
    fig.add_trace(go.Bar(
        x=pmc_df['date_day'], y=pmc_df['daily_distance'],
        name='Daily Distance',
        marker_color='rgba(200, 200, 200, 0.2)',
        yaxis='y2'
    ))

    fig.update_layout(
        title="Performance Management Chart (PMC)",
        yaxis=dict(title="CTL / ATL / TSB"),
        yaxis2=dict(
            title="Distance (km)",
            overlaying='y',
            side='right',
            showgrid=False,
            range=[0, pmc_df['daily_distance'].max() * 3] # Keep bars small at the bottom
        ),
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        **CHART_LAYOUT
    )
    
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("No training load data available for this period.")
