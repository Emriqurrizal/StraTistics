import streamlit as st
import pandas as pd
from db import run_query
from components.filters import render_sidebar_filters
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from components.charts import CHART_LAYOUT

st.title("Training Load Analytics")
st.markdown("Insights into your physical stress and recovery utilizing the Performance Management Chart (PMC) to guide your training intensity and prevent overtraining.")
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
    # Calculate Ramp Rate (7-day change in CTL)
    pmc_df['ramp_rate'] = pmc_df['ctl'] - pmc_df['ctl'].shift(7)
    
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
    
    # Highlight High Risk Ramp Rate Periods (> 8 CTL/week)
    in_risk = False
    risk_start = None
    for idx, row in pmc_df.iterrows():
        if pd.notna(row['ramp_rate']) and row['ramp_rate'] > 8:
            if not in_risk:
                risk_start = row['date_day']
                in_risk = True
        else:
            if in_risk:
                fig.add_vrect(x0=risk_start, x1=row['date_day'], fillcolor="red", opacity=0.15, line_width=0, layer="below", row=1, col=1)
                in_risk = False
    if in_risk:
        fig.add_vrect(x0=risk_start, x1=pmc_df['date_day'].iloc[-1], fillcolor="red", opacity=0.15, line_width=0, layer="below", row=1, col=1)
    
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
        arrowcolor="rgba(128, 128, 128, 0.5)",
        ax=0,
        ay=55,
        font=dict(color=status_color, size=16),
        bgcolor="rgba(128, 128, 128, 0.1)",
        bordercolor="rgba(128, 128, 128, 0.3)",
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
        number={'font': {'color': status_color}, 'valueformat': '.2f'},
        delta={
            'reference': tsb_7d_ago, 
            'position': "bottom", 
            'valueformat': ".2f",
            'increasing': {'color': '#06d6a0', 'symbol': '↑ '},
            'decreasing': {'color': '#ff4b4b', 'symbol': '↓ '}
        },
        gauge={
            'axis': {'range': [-15, 15], 'tickwidth': 1, 'tickvals': [-15, -10, -5, 0, 5, 10, 15]},
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
    
    # Ramp Rate Logic
    latest_rr = pmc_df['ramp_rate'].iloc[-1]
    if pd.isna(latest_rr):
        rr_status_text = "No data"
        rr_status_color = "grey"
    elif latest_rr < 0:
        rr_status_text = "DETRAINING — Loss of fitness"
        rr_status_color = "#607d8b"
    elif latest_rr <= 3:
        rr_status_text = "CONSERVATIVE — Safe build"
        rr_status_color = "#06d6a0"
    elif latest_rr <= 5:
        rr_status_text = "OPTIMAL BUILD — Productive zone"
        rr_status_color = "#00b4d8"
    elif latest_rr <= 8:
        rr_status_text = "AGGRESSIVE — Monitor fatigue"
        rr_status_color = "#ffa000"
    else:
        rr_status_text = "HIGH INJURY RISK — Too fast"
        rr_status_color = "#ff4b4b"
        
    # Ramp Rate Sparkline Chart
    fig_ramp = go.Figure()
    
    # Convert hex to rgba for sparkline fill
    def hex_to_rgba(hex_color, opacity=0.2):
        hex_color = hex_color.lstrip('#')
        if len(hex_color) == 6:
            r, g, b = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
            return f"rgba({r}, {g}, {b}, {opacity})"
        return 'rgba(255,255,255,0.1)'
        
    rr_7d_ago = pmc_df['ramp_rate'].iloc[-8] if len(pmc_df) > 7 else 0
    
    fig_ramp.add_trace(go.Indicator(
        mode="number+delta",
        value=round(latest_rr, 2) if not pd.isna(latest_rr) else 0,
        number={'font': {'color': rr_status_color}, 'valueformat': ".2f"},
        delta={
            'reference': round(rr_7d_ago, 2), 
            'position': "bottom", 
            'valueformat': ".2f",
            'increasing': {'color': '#06d6a0', 'symbol': '↑ '},
            'decreasing': {'color': '#ff4b4b', 'symbol': '↓ '}
        },
        domain={'y': [0.4, 1], 'x': [0, 1]}
    ))
    
    spark_df_daily = pmc_df.dropna(subset=['ramp_rate'])
    if not spark_df_daily.empty:
        # Sample every 7 days starting from the latest day
        spark_df = spark_df_daily.iloc[::-7].iloc[::-1]
        
        max_y = max(8, spark_df['ramp_rate'].max() * 1.1)
        min_y = min(0, spark_df['ramp_rate'].min() * 1.1)
        
        # Add subtle background shading for zones
        fig_ramp.add_hrect(y0=8, y1=max_y + 5, fillcolor="#ff4b4b", opacity=0.1, line_width=0, layer="below")
        fig_ramp.add_hrect(y0=5, y1=8, fillcolor="#ffa000", opacity=0.1, line_width=0, layer="below")
        fig_ramp.add_hrect(y0=3, y1=5, fillcolor="#00b4d8", opacity=0.1, line_width=0, layer="below")
        fig_ramp.add_hrect(y0=0, y1=3, fillcolor="#06d6a0", opacity=0.1, line_width=0, layer="below")
        fig_ramp.add_hrect(y0=min_y - 5, y1=0, fillcolor="#607d8b", opacity=0.1, line_width=0, layer="below")

        fig_ramp.add_trace(go.Scatter(
            x=spark_df['date_day'],
            y=spark_df['ramp_rate'],
            mode='lines+markers',
            line=dict(color=rr_status_color, width=2),
            marker=dict(size=6, color=rr_status_color),
            fill='tozeroy',
            fillcolor=hex_to_rgba(rr_status_color, 0.2) if rr_status_color != "grey" else "rgba(128,128,128,0.2)",
            hovertemplate='%{x|%b %d, %Y}<br>Ramp Rate: %{y:.2f}<extra></extra>'
        ))
    
    ramp_layout = CHART_LAYOUT.copy()
    ramp_layout.update(
        height=300,
        margin=dict(l=20, r=20, t=50, b=20),
        xaxis=dict(showgrid=False, showticklabels=False, zeroline=False),
        yaxis=dict(showgrid=False, showticklabels=False, zeroline=False, domain=[0, 0.3], autorange=True)
    )
    fig_ramp.update_layout(**ramp_layout)

    # Render PMC Chart
    st.plotly_chart(fig, use_container_width=True)
    
    st.markdown("<hr style='margin: 40px 0;'>", unsafe_allow_html=True)
    
    # Render Form Status Section
    st.subheader("Form Status (TSB)")
    st.markdown(f"<div style='color: {status_color}; font-size: 16px; margin-bottom: -30px;'>{status_text}</div>", unsafe_allow_html=True)
    st.plotly_chart(fig_gauge, use_container_width=True)
    
    legend_html_tsb = """
    <div style='margin-top: 10px; padding: 10px; border-radius: 6px; background-color: var(--secondary-background-color); font-size: 13px; color: var(--text-color); display: flex; justify-content: center; gap: 15px; flex-wrap: wrap;'>
        <span><span style='color:#ff4b4b; font-size: 14px;'>■</span> Overreaching (< -10)</span>
        <span><span style='color:#ffa000; font-size: 14px;'>■</span> Heavy (-10 to -4)</span>
        <span><span style='color:#ffd166; font-size: 14px;'>■</span> Optimal (-4 to 3)</span>
        <span><span style='color:#06d6a0; font-size: 14px;'>■</span> Fresh (3 to 10)</span>
        <span><span style='color:#ffa000; font-size: 14px;'>■</span> Detraining (> 10)</span>
    </div>
    """
    st.markdown(legend_html_tsb, unsafe_allow_html=True)
    
    st.markdown("<hr style='margin: 40px 0;'>", unsafe_allow_html=True)
    
    # Render Ramp Rate Section
    st.subheader("Ramp Rate (CTL/week)")
    st.markdown(f"<div style='color: {rr_status_color}; font-size: 16px; margin-bottom: -30px;'>{rr_status_text}</div>", unsafe_allow_html=True)
    st.plotly_chart(fig_ramp, use_container_width=True)
    
    legend_html_rr = """
    <div style='margin-top: 10px; padding: 10px; border-radius: 6px; background-color: var(--secondary-background-color); font-size: 13px; color: var(--text-color); display: flex; justify-content: center; gap: 15px; flex-wrap: wrap;'>
        <span><span style='color:#ff4b4b; font-size: 14px;'>■</span> Risk (> 8)</span>
        <span><span style='color:#ffa000; font-size: 14px;'>■</span> Aggressive (5-8)</span>
        <span><span style='color:#00b4d8; font-size: 14px;'>■</span> Optimal (3-5)</span>
        <span><span style='color:#06d6a0; font-size: 14px;'>■</span> Conservative (0-3)</span>
        <span><span style='color:#607d8b; font-size: 14px;'>■</span> Detraining (< 0)</span>
    </div>
    """
    st.markdown(legend_html_rr, unsafe_allow_html=True)
else:
    st.info("No training load data available for this period.")
