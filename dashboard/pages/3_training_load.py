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
    FROM public_metrics.training_load
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
    elif latest_tsb > 10:
        status_text = f"Current TSB: {latest_tsb:.1f} → DETRAINING — Loss of fitness"
        status_color = "#ffa000"
    elif latest_tsb > 3:
        status_text = f"Current TSB: {latest_tsb:.1f} → FRESH — Ready to race or hard workout"
        status_color = "#06d6a0"
    elif latest_tsb >= -4:
        status_text = f"Current TSB: {latest_tsb:.1f} → OPTIMAL — Productive training zone"
        status_color = "#ffd166"
    elif latest_tsb >= -10:
        status_text = f"Current TSB: {latest_tsb:.1f} → HEAVY — Accumulated fatigue, consider recovery"
        status_color = "#ffa000"
    else:
        status_text = f"Current TSB: {latest_tsb:.1f} → OVERREACHING — High risk of injury/illness"
        status_color = "#ff4b4b"
        
    # Plot PMC
    fig = go.Figure()
    
    # Background TSB zones
    fig.add_hrect(y0=10, y1=15, fillcolor="orange", opacity=0.1, line_width=0, layer="below")
    fig.add_hrect(y0=3, y1=10, fillcolor="green", opacity=0.1, line_width=0, layer="below")
    fig.add_hrect(y0=-4, y1=3, fillcolor="yellow", opacity=0.1, line_width=0, layer="below")
    fig.add_hrect(y0=-10, y1=-4, fillcolor="orange", opacity=0.1, line_width=0, layer="below")
    fig.add_hrect(y0=-15, y1=-10, fillcolor="red", opacity=0.1, line_width=0, layer="below")

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

    # Calculate y-axis range based on data so shapes don't zoom out the chart
    min_y = pmc_df[['ctl', 'atl', 'tsb']].min().min()
    max_y = pmc_df[['ctl', 'atl', 'tsb']].max().max()

    fig.update_layout(
        title="Performance Management Chart (PMC)",
        yaxis=dict(title="CTL / ATL / TSB", range=[min_y - 3, max_y + 3]),
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
    
    # Gauge Chart for Latest TSB
    fig_gauge = go.Figure(go.Indicator(
        mode="gauge+number",
        value=latest_tsb,
        title={'text': "Current Form (TSB)", 'font': {'size': 20, 'color': "white"}},
        number={'font': {'color': "white"}},
        gauge={
            'axis': {'range': [-15, 15], 'tickwidth': 1, 'tickcolor': "white", 'tickfont': {'color': "white"}},
            'bar': {'color': "rgba(0,0,0,0)", 'thickness': 0}, # Hide the thick progress bar
            'bgcolor': "rgba(0,0,0,0)", # Transparent background
            'borderwidth': 0,
            'steps': [
                {'range': [-15, -10], 'color': "#ff4b4b"},  # Vibrant Red
                {'range': [-10, -4], 'color': "#ffa000"},   # Vibrant Orange
                {'range': [-4, 3], 'color': "#ffd166"},     # Vibrant Yellow
                {'range': [3, 10], 'color': "#06d6a0"},     # Vibrant Green
                {'range': [10, 15], 'color': "#ffa000"}     # Vibrant Orange
            ],
            'threshold': {
                'line': {'color': "white", 'width': 4},
                'thickness': 0.8,
                'value': latest_tsb
            }
        }
    ))
    
    gauge_layout = CHART_LAYOUT.copy()
    gauge_layout.update(
        height=300,
        margin=dict(l=20, r=20, t=50, b=20)
    )
    fig_gauge.update_layout(**gauge_layout)
    
    # Render charts sequentially
    st.plotly_chart(fig, use_container_width=True)
    st.markdown("---")
    
    # Status Header
    st.markdown(f"<h3 style='text-align: center; color: {status_color};'>{status_text}</h3>", unsafe_allow_html=True)
    st.plotly_chart(fig_gauge, use_container_width=True)
    
    legend_html = """
    <div style='margin-top: 30px; font-size: 15px; color: #e0e0e0;'>
        <h4 style='margin-bottom: 15px;'>What do the colors mean?</h4>
        <ul style='list-style: none; padding-left: 0;'>
            <li style='margin-bottom: 10px;'><span style='display:inline-block; width:14px; height:14px; background-color:#ff4b4b; border-radius:3px; margin-right:10px; vertical-align:middle;'></span><strong style='color: white;'>Overreaching (< -10)</strong>: High risk of injury or illness. You are carrying too much fatigue and need to recover.</li>
            <li style='margin-bottom: 10px;'><span style='display:inline-block; width:14px; height:14px; background-color:#ffa000; border-radius:3px; margin-right:10px; vertical-align:middle;'></span><strong style='color: white;'>Heavy Training (-10 to -4)</strong>: The productive "sweet spot". You are building fitness but actively accumulating fatigue.</li>
            <li style='margin-bottom: 10px;'><span style='display:inline-block; width:14px; height:14px; background-color:#ffd166; border-radius:3px; margin-right:10px; vertical-align:middle;'></span><strong style='color: white;'>Optimal / Neutral (-4 to 3)</strong>: A balanced transitional zone where you are maintaining fitness.</li>
            <li style='margin-bottom: 10px;'><span style='display:inline-block; width:14px; height:14px; background-color:#06d6a0; border-radius:3px; margin-right:10px; vertical-align:middle;'></span><strong style='color: white;'>Fresh (3 to 10)</strong>: You are fully rested, tapered, and in prime form to execute a race or hard workout!</li>
            <li style='margin-bottom: 10px;'><span style='display:inline-block; width:14px; height:14px; background-color:#ffa000; border-radius:3px; margin-right:10px; vertical-align:middle;'></span><strong style='color: white;'>Detraining (> 10)</strong>: You have rested too much and are beginning to lose fitness.</li>
        </ul>
    </div>
    """
    st.markdown(legend_html, unsafe_allow_html=True)
else:
    st.info("No training load data available for this period.")
