import streamlit as st
import pandas as pd
from db import run_query
from components.filters import render_sidebar_filters
import plotly.express as px
from components.charts import CHART_LAYOUT

st.title("Gear Tracker")
st.markdown("---")

filters = render_sidebar_filters()

query_gear = """
    SELECT 
        name,
        brand_name,
        model_name,
        cumulative_distance_km,
        retired
    FROM public_gold.dim_gear
    WHERE cumulative_distance_km > 0
    ORDER BY cumulative_distance_km DESC
"""
gear_df = run_query(query_gear)

if not gear_df.empty:
    st.markdown("### Cumulative Gear Mileage")
    
    MAX_LIFE = 700.0
    gear_df['percent_used'] = (gear_df['cumulative_distance_km'] / MAX_LIFE) * 100
    
    def format_label(row):
        km = row['cumulative_distance_km']
        pct = row['percent_used']
        return f"{km:.1f} km — {pct:.0f}% used"
            
    gear_df['label'] = gear_df.apply(format_label, axis=1)
    
    # Assign consistent colors per shoe
    unique_gears = gear_df['name'].unique()
    palette = px.colors.qualitative.Bold
    gear_colors = {}
    c_idx = 0
    for name in unique_gears:
        is_retired = gear_df[gear_df['name'] == name]['retired'].iloc[0]
        if is_retired:
            gear_colors[name] = "rgba(100, 100, 100, 0.5)"
        else:
            gear_colors[name] = palette[c_idx % len(palette)]
            c_idx += 1
    
    # Sort descending by % used (for Plotly horizontal bars, we sort ascending so largest is at the top)
    gear_df = gear_df.sort_values(by='percent_used', ascending=True)
    
    fig = px.bar(
        gear_df, 
        y='name', 
        x='percent_used',
        orientation='h',
        color='name',
        color_discrete_map=gear_colors,
        text='label',
        hover_data=['brand_name', 'model_name', 'retired', 'cumulative_distance_km']
    )
    
    fig.add_vline(x=70, line_dash="dash", line_color="orange", annotation_text="70%", annotation_position="top left")
    fig.add_vline(x=100, line_dash="dash", line_color="red", annotation_text="100%", annotation_position="top left")
    
    fig.update_traces(textposition='outside', textangle=0, cliponaxis=False)
    
    # Scale X axis from 0 to at least 100, or higher if overdue
    max_pct = gear_df['percent_used'].max() if not gear_df['percent_used'].empty else 100
    fig.update_layout(
        xaxis_title="% Life Used (based on 700km replacement)", 
        xaxis=dict(range=[0, max(105, max_pct + 40)]), # Add extra space so the outside text doesn't get clipped
        showlegend=False,
        **CHART_LAYOUT
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    retired_gears = gear_df[gear_df['retired'] == True]['name'].tolist()
    
    st.markdown("---")
    st.markdown("### Gear Usage Over Time")
    query_gear_usage = """
        SELECT 
            TO_CHAR(date_trunc('week', date_day), 'YYYY-MM-DD') as week,
            gear_name,
            SUM(distance_km) as distance
        FROM public_gold.fct_activities
        WHERE date_day BETWEEN %s AND %s
        AND gear_name IS NOT NULL
        GROUP BY 1, 2
        ORDER BY 1
    """
    usage_df = run_query(query_gear_usage, (filters['start_date'], filters['end_date']))
    
    if not usage_df.empty:
        # Fill missing weeks with 0 to avoid line disappearing/overlapping weirdly
        usage_df['week'] = pd.to_datetime(usage_df['week'])
        max_week = usage_df['week'].max()
        
        full_usage = []
        for gear in usage_df['gear_name'].unique():
            gear_data = usage_df[usage_df['gear_name'] == gear]
            min_week = gear_data['week'].min()
            # Get all unique weeks in the dataset between min_week and max_week
            gear_weeks = sorted([w for w in usage_df['week'].unique() if w >= min_week])
            gear_grid = pd.DataFrame({'week': gear_weeks, 'gear_name': gear})
            full_usage.append(gear_grid)
            
        full_grid = pd.concat(full_usage, ignore_index=True)
        usage_full = pd.merge(full_grid, usage_df, on=['week', 'gear_name'], how='left')
        usage_full['distance'] = usage_full['distance'].fillna(0)
        
        # Sort and find drops to 0
        usage_full = usage_full.sort_values(['gear_name', 'week'])
        usage_full['prev_distance'] = usage_full.groupby('gear_name')['distance'].shift(1)
        
        def get_annotation(row):
            if row['distance'] == 0 and row['prev_distance'] > 0:
                return "retired" if row['gear_name'] in retired_gears else "benched"
            return ""
            
        usage_full['text'] = usage_full.apply(get_annotation, axis=1)
        usage_full['week'] = usage_full['week'].dt.strftime('%Y-%m-%d')
        
        fig_area = px.line(
            usage_full, 
            x='week', 
            y='distance', 
            color='gear_name',
            title="Weekly Distance by Shoe",
            color_discrete_map=gear_colors,
            markers=True,
            text='text'
        )
        fig_area.update_traces(textposition='top center')
        fig_area.update_layout(**CHART_LAYOUT)
        st.plotly_chart(fig_area, use_container_width=True)
else:
    st.info("No gear data available.")
