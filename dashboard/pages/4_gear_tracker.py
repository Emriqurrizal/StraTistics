import streamlit as st
import pandas as pd
from db import run_query
from components.filters import render_sidebar_filters
import plotly.express as px
from components.charts import CHART_LAYOUT

st.title("4. Gear Tracker")

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
    
    # Create color map based on mileage
    def get_gear_color(km, retired):
        if retired:
            return "rgba(100, 100, 100, 0.5)" # Greyed out
        if pd.isna(km):
            return "green"
        if km > 700:
            return "red"
        if km > 500:
            return "orange"
        return "green"
        
    gear_df['color'] = gear_df.apply(lambda row: get_gear_color(row['cumulative_distance_km'], row['retired']), axis=1)
    
    fig = px.bar(
        gear_df, 
        y='name', 
        x='cumulative_distance_km',
        orientation='h',
        color='color',
        color_discrete_map="identity",
        text='cumulative_distance_km',
        hover_data=['brand_name', 'model_name', 'retired']
    )
    
    fig.add_vline(x=500, line_dash="dash", line_color="orange", annotation_text="Warning (500km)")
    fig.add_vline(x=700, line_dash="dash", line_color="red", annotation_text="Replace (700km)")
    
    fig.update_traces(texttemplate='%{text:.1f} km', textposition='outside')
    fig.update_layout(yaxis={'categoryorder':'total ascending'}, **CHART_LAYOUT)
    
    st.plotly_chart(fig, use_container_width=True)
    
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
        fig_area = px.area(
            usage_df, 
            x='week', 
            y='distance', 
            color='gear_name',
            title="Weekly Distance by Shoe",
            color_discrete_sequence=px.colors.qualitative.Bold
        )
        fig_area.update_layout(**CHART_LAYOUT)
        st.plotly_chart(fig_area, use_container_width=True)
else:
    st.info("No gear data available.")
