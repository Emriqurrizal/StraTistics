import streamlit as st
import pandas as pd
from db import run_query
from components.filters import render_sidebar_filters
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from components.charts import CHART_LAYOUT

st.title("Training Load (PMC)")
st.markdown("---")

filters = render_sidebar_filters()

#1. PMC
st.subheader("Performance Management Chart (PMC)")
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
        status_text = "DETRAINING — Loss of fitness"
        status_color = "#ffa000"
    elif latest_tsb > 3:
        status_text = "FRESH — Ready to race or hard workout"
        status_color = "#06d6a0"
    elif latest_tsb >= -4:
        status_text = "OPTIMAL — Productive training zone"
        status_color = "#ffd166"
    elif latest_tsb >= -10:
        status_text = "HEAVY — Accumulated fatigue, consider recovery"
        status_color = "#ffa000"
    else:
        status_text = "OVERREACHING — High risk of injury/illness"
        status_color = "#ff4b4b"
        
    # Plot PMC
    fig = make_subplots(
        rows=2, cols=1, 
        shared_xaxes=True, 
        vertical_spacing=0.05, 
        row_heights=[0.8, 0.2]
    )
    
    # Background TSB zones
    fig.add_hrect(y0=10, y1=15, fillcolor="orange", opacity=0.1, line_width=0, layer="below", row=1, col=1)
    fig.add_hrect(y0=3, y1=10, fillcolor="green", opacity=0.1, line_width=0, layer="below", row=1, col=1)
    fig.add_hrect(y0=-4, y1=3, fillcolor="yellow", opacity=0.1, line_width=0, layer="below", row=1, col=1)
    fig.add_hrect(y0=-10, y1=-4, fillcolor="orange", opacity=0.1, line_width=0, layer="below", row=1, col=1)
    fig.add_hrect(y0=-15, y1=-10, fillcolor="red", opacity=0.1, line_width=0, layer="below", row=1, col=1)

    # TSB (Area)
    fig.add_trace(go.Scatter(
        x=pmc_df['date_day'], y=pmc_df['tsb'],
        mode='lines',
        name='TSB (Form)',
        line=dict(color='rgba(255, 255, 255, 0)'), # hide line
        fill='tozeroy',
        fillcolor='rgba(255, 200, 0, 0.3)'
    ), row=1, col=1)
    
    # CTL (Fitness)
    fig.add_trace(go.Scatter(
        x=pmc_df['date_day'], y=pmc_df['ctl'],
        mode='lines',
        name='CTL (Fitness)',
        line=dict(color='#2196F3', width=2)
    ), row=1, col=1)
    
    # ATL (Fatigue)
    fig.add_trace(go.Scatter(
        x=pmc_df['date_day'], y=pmc_df['atl'],
        mode='lines',
        name='ATL (Fatigue)',
        line=dict(color='#E91E63', width=2)
    ), row=1, col=1)
    
    # Daily distance bars on thin sparkline (row 2)
    fig.add_trace(go.Bar(
        x=pmc_df['date_day'], y=pmc_df['daily_distance'],
        name='Daily Distance',
        marker_color='rgba(200, 200, 200, 0.4)'
    ), row=2, col=1)

    # Add a prominent dot at the end of the TSB line
    fig.add_trace(go.Scatter(
        x=[pmc_df['date_day'].iloc[-1]],
        y=[latest_tsb],
        mode='markers',
        name='Current Form',
        marker=dict(
            color=status_color,
            size=12,
            line=dict(color='white', width=2)
        ),
        showlegend=False,
        hoverinfo='skip'
    ), row=1, col=1)

    # Add a sleek, premium floating callout
    fig.add_annotation(
        x=pmc_df['date_day'].iloc[-1],
        y=latest_tsb,
        text=f"<span style='font-size: 10px; color: #a0a0a0;'>CURRENT TSB</span><br><b>{latest_tsb:.2f}</b>",
        showarrow=True,
        arrowhead=0,
        arrowwidth=1.5,
        arrowcolor="rgba(255, 255, 255, 0.3)",
        ax=0,
        ay=55,
        font=dict(color=status_color, size=16),
        bgcolor="rgba(20, 20, 20, 0.9)",
        bordercolor="rgba(255, 255, 255, 0.15)",
        borderwidth=1,
        borderpad=6,
        row=1, col=1
    )

    # Calculate y-axis range based on data so shapes don't zoom out the chart
    min_y = pmc_df[['ctl', 'atl', 'tsb']].min().min()
    max_y = pmc_df[['ctl', 'atl', 'tsb']].max().max()

    fig.update_layout(
        title=" ",
        yaxis=dict(title="CTL/ATL/TSB", range=[min_y - 3, max_y + 3]),
        yaxis2=dict(
            title="Dist (km)",
            showgrid=False,
            range=[0, pmc_df['daily_distance'].max() * 1.1]
        ),
        hovermode="x unified",
        **CHART_LAYOUT
    )
    
    # Calculate 7-day trend
    if len(pmc_df) > 7:
        tsb_7d_ago = pmc_df['tsb'].iloc[-8]
    elif len(pmc_df) > 1:
        tsb_7d_ago = pmc_df['tsb'].iloc[0]
    else:
        tsb_7d_ago = latest_tsb
    
    # Gauge Chart for Latest TSB
    fig_gauge = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=latest_tsb,
        number={'font': {'color': "white"}},
        delta={
            'reference': tsb_7d_ago, 
            'position': "bottom", 
            'valueformat': ".1f",
            'increasing': {'color': '#06d6a0', 'symbol': '↑ '},
            'decreasing': {'color': '#ff4b4b', 'symbol': '↓ '}
        },
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
    
    # Render PMC Chart
    st.plotly_chart(fig, use_container_width=True)
    
    st.markdown("<hr style='margin: 40px 0;'>", unsafe_allow_html=True)
    
    # Render Form Status Section
    st.subheader("Form Status (TSB)")
    st.markdown(f"<div style='color: {status_color}; font-size: 16px; margin-bottom: -30px;'>{status_text}</div>", unsafe_allow_html=True)
    st.plotly_chart(fig_gauge, use_container_width=True)
    
    legend_html = """
    <div style='margin-top: 10px; padding: 10px; border-radius: 6px; background-color: rgba(255,255,255,0.05); font-size: 13px; color: #e0e0e0; display: flex; justify-content: center; gap: 20px; flex-wrap: wrap;'>
        <span><span style='color:#ff4b4b; font-size: 14px;'>■</span> Overreaching (< -10)</span>
        <span><span style='color:#ffa000; font-size: 14px;'>■</span> Heavy (-10 to -4)</span>
        <span><span style='color:#ffd166; font-size: 14px;'>■</span> Optimal (-4 to 3)</span>
        <span><span style='color:#06d6a0; font-size: 14px;'>■</span> Fresh (3 to 10)</span>
        <span><span style='color:#ffa000; font-size: 14px;'>■</span> Detraining (> 10)</span>
    </div>
    """
    st.markdown(legend_html, unsafe_allow_html=True)
else:
    st.info("No training load data available for this period.")
