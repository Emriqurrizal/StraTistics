import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

# Standard layout configuration for all charts
CHART_LAYOUT = dict(
    paper_bgcolor='rgba(0,0,0,0)',
    plot_bgcolor='rgba(0,0,0,0)',
    font=dict(color='#FAFAFA'),
    margin=dict(l=10, r=10, t=40, b=10)
)

def create_time_series(df: pd.DataFrame, x: str, y_cols: list, title: str, 
                      y_title: str = "", inverted_y: bool = False) -> go.Figure:
    """Create a time series chart with one or more lines."""
    fig = go.Figure()
    
    colors = ['#FC4C02', '#4CAF50', '#2196F3', '#FFC107']
    
    for i, col in enumerate(y_cols):
        line_style = dict(color=colors[i % len(colors)])
        if 'rolling' in col.lower() or 'avg' in col.lower():
            if i > 0:
                line_style['dash'] = 'dot' if i > 1 else 'dash'
                
        fig.add_trace(go.Scatter(
            x=df[x], y=df[col],
            mode='lines',
            name=col.replace('_', ' ').title(),
            line=line_style
        ))
        
    fig.update_layout(
        title=title,
        yaxis_title=y_title,
        **CHART_LAYOUT
    )
    
    if inverted_y:
        fig.update_yaxes(autorange="reversed")
        
    return fig

def create_stacked_bar(df: pd.DataFrame, x: str, y: str, color: str, title: str) -> go.Figure:
    """Create a stacked bar chart."""
    fig = px.bar(df, x=x, y=y, color=color, title=title, 
                 color_discrete_sequence=px.colors.qualitative.Bold)
    fig.update_layout(**CHART_LAYOUT)
    return fig

def create_scatter(df: pd.DataFrame, x: str, y: str, color: str, size: str, 
                  hover_data: list, title: str, inverted_y: bool = False) -> go.Figure:
    """Create a scatter plot."""
    fig = px.scatter(df, x=x, y=y, color=color, size=size, 
                     hover_data=hover_data, title=title,
                     color_discrete_sequence=px.colors.qualitative.Bold)
    fig.update_layout(**CHART_LAYOUT)
    
    if inverted_y:
        fig.update_yaxes(autorange="reversed")
        
    return fig

def create_heatmap(df: pd.DataFrame, x: str, y: str, z: str, title: str) -> go.Figure:
    """Create a heatmap."""
    fig = go.Figure(data=go.Heatmap(
        z=df[z],
        x=df[x],
        y=df[y],
        colorscale='Oranges',
        hoverongaps=False
    ))
    fig.update_layout(title=title, **CHART_LAYOUT)
    return fig

def create_donut(df: pd.DataFrame, names: str, values: str, title: str) -> go.Figure:
    """Create a donut chart."""
    fig = px.pie(df, values=values, names=names, hole=0.4, title=title,
                 color_discrete_sequence=px.colors.qualitative.Pastel)
    fig.update_layout(**CHART_LAYOUT)
    return fig

def create_histogram(df: pd.DataFrame, x: str, title: str, ref_line: float = None) -> go.Figure:
    """Create a histogram with an optional vertical reference line."""
    fig = px.histogram(df, x=x, title=title, color_discrete_sequence=['#FC4C02'])
    
    if ref_line is not None:
        fig.add_vline(x=ref_line, line_width=2, line_dash="dash", line_color="green")
        
    fig.update_layout(**CHART_LAYOUT)
    return fig
