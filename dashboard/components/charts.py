import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np

# Standard layout configuration for all charts
CHART_LAYOUT = dict(
    paper_bgcolor='rgba(0,0,0,0)',
    plot_bgcolor='rgba(0,0,0,0)',
    font=dict(color='#FAFAFA'),
    margin=dict(l=10, r=10, t=40, b=10),
    legend_title_text='',
    legend=dict(
        orientation="h",
        yanchor="top",
        y=-0.2,
        xanchor="center",
        x=0.5
    )
)
HR_ZONE_COLOR_MAP = {
    'Z5': '#EF4444',   # Bright red
    'Z4': '#F97316',   # Bright orange
    'Z3': '#EAB308',   # Gold
    'Z2': '#22C55E',   # Bright green
    'Z1': '#3B82F6'    # Bright blue
}

WORKOUT_COLOR_MAP = {
    'Easy Run': '#FDBA74',    # Soft peach-orange — gentle effort
    'Easy': '#FDBA74',
    'Tempo Run': '#FC5200',   # Strava signature orange — threshold
    'Tempo': '#FC5200',
    'Long Run': '#B91C1C',    # Deep crimson — endurance
    'Intervals': '#EF4444',   # Bright coral-red — high intensity
    'Race': '#FBBF24',        # Warm amber-gold — race day
    'Regular': '#FB923C',     # Medium orange — everyday run
    'Base Run': '#FB923C',
    'Workout': '#EF4444'
}

STRAVA_HEATMAP_COLORSCALE = [
    [0.0,    '#1A1D23'],   # Zero — matches secondaryBackgroundColor
    [0.0001, '#3D1E00'],   # Faintest warm
    [0.25,   '#7A3500'],   # Dark amber
    [0.50,   '#B95000'],   # Mid orange
    [0.75,   '#E06000'],   # Rich orange
    [1.0,    '#FC4C02']    # Full Strava orange
]

def create_time_series(df: pd.DataFrame, x: str, y_cols: list, title: str, 
                      y_title: str = "", inverted_y: bool = False) -> go.Figure:
    """Create a time series chart with one or more lines."""
    fig = go.Figure()
    
    colors = ['#FC4C02', '#4CAF50', '#2196F3', '#FFC107']
    dash_styles = ['solid', 'dash', 'dot', 'dashdot', 'longdash', 'longdashdot']
    
    for i, col in enumerate(y_cols):
        line_style = dict(color=colors[i % len(colors)])
        if 'rolling' in col.lower() or 'avg' in col.lower():
            if i > 0:
                line_style['dash'] = dash_styles[i % len(dash_styles)]
                
        fig.add_trace(go.Scatter(
            x=df[x], y=df[col],
            mode='lines+markers',
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

def create_stacked_bar(df: pd.DataFrame, x: str, y: str, color: str, title: str, color_discrete_map: dict = None) -> go.Figure:
    """Create a stacked bar chart."""
    fig = px.bar(df, x=x, y=y, color=color, title=title, 
                 color_discrete_sequence=px.colors.qualitative.Bold if not color_discrete_map else None,
                 color_discrete_map=color_discrete_map)
    fig.update_layout(**CHART_LAYOUT)
    return fig

def create_bar(df: pd.DataFrame, x: str, y: str, title: str, color: str = None, color_discrete_map: dict = None) -> go.Figure:
    """Create a bar chart."""
    fig = px.bar(df, x=x, y=y, color=color, title=title, 
                 color_discrete_sequence=px.colors.qualitative.Bold if not color_discrete_map else None,
                 color_discrete_map=color_discrete_map)
    fig.update_layout(**CHART_LAYOUT)
    return fig

def create_scatter(df: pd.DataFrame, x: str, y: str, color: str, size: str, 
                  hover_data: list, title: str, inverted_y: bool = False, color_discrete_map: dict = None) -> go.Figure:
    """Create a scatter plot."""
    fig = px.scatter(df, x=x, y=y, color=color, size=size, 
                     hover_data=hover_data, title=title,
                     color_discrete_sequence=px.colors.qualitative.Bold if not color_discrete_map else None,
                     color_discrete_map=color_discrete_map)
    fig.update_layout(**CHART_LAYOUT)
    
    if inverted_y:
        fig.update_yaxes(autorange="reversed")
        
    return fig

def create_heatmap(df: pd.DataFrame, x: str, y: str, z: str, title: str, text: str = None) -> go.Figure:
    """Create a heatmap."""
    heatmap_kwargs = dict(
        z=df[z],
        x=df[x],
        y=df[y],
        colorscale='Oranges',
        hoverongaps=False
    )
    if text:
        heatmap_kwargs['text'] = df[text]
        heatmap_kwargs['hovertemplate'] = '%{y}<br>Value: %{z}<br>Date: %{text}<extra></extra>'

    fig = go.Figure(data=go.Heatmap(**heatmap_kwargs))
    fig.update_layout(title=title, **CHART_LAYOUT)
    return fig

def _compute_month_ticks(df, date_col, week_labels):
    """Compute month boundary positions and labels for the x-axis, centered over visible weeks."""
    df_sorted = df.sort_values(date_col)
    week_index_map = {w: i for i, w in enumerate(week_labels)}
    
    month_weeks = {}
    for _, row in df_sorted.iterrows():
        month_key = row[date_col].strftime('%b %Y')  # "Jan 2024"
        wl = row['week_label']
        wi = week_index_map[wl]
        if month_key not in month_weeks:
            month_weeks[month_key] = set()
        month_weeks[month_key].add(wi)
        
    ticks = []
    boundaries = []
    
    for month_key, wis in month_weeks.items():
        wis_list = sorted(list(wis))
        start_pos = wis_list[0]
        end_pos = wis_list[-1]
        
        # Place label at the midpoint of the month's visible columns
        mid_pos = (start_pos + end_pos) // 2
        ticks.append({'text': month_key, 'pos': mid_pos})
        
        # Boundary line before the first week of the month (skip the very first column)
        if start_pos > 0:
            boundaries.append(start_pos)
            
    # Sort ticks by position
    ticks = sorted(ticks, key=lambda x: x['pos'])
    
    return {
        'vals': [week_labels[x['pos']] for x in ticks],
        'text': [x['text'] for x in ticks],
        'boundaries': boundaries
    }

def create_calendar_heatmap(
    df: pd.DataFrame,
    date_col: str,
    z_col: str,
    title: str,
    z_label: str = "Distance (km)",
    hover_extra: dict = None    # e.g. {'workout_type': 'Workout', 'pace_str': 'Pace'}
) -> go.Figure:
    df = df.copy()
    df[date_col] = pd.to_datetime(df[date_col])
    df['day_of_week'] = df[date_col].dt.dayofweek          # Mon=0 → Sun=6
    df['week_label']  = df[date_col].dt.strftime('%Y-W%V')  # ISO week label
    df['date_str']    = df[date_col].dt.strftime('%A, %b %d %Y')
    
    day_labels = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
    week_labels = df.sort_values(date_col)['week_label'].unique().tolist()
    
    # Build the z-matrix (7 rows × N-weeks columns)
    z_matrix = np.full((7, len(week_labels)), np.nan)
    text_matrix = np.full((7, len(week_labels)), '', dtype=object)
    customdata_matrix = np.empty((7, len(week_labels)), dtype=object)
    
    week_index_map = {w: i for i, w in enumerate(week_labels)}
    
    for _, row in df.iterrows():
        wi = week_index_map[row['week_label']]
        di = row['day_of_week']
        z_matrix[di][wi] = row[z_col]
        text_matrix[di][wi] = row['date_str']
        # Pack extra hover fields
        extra = []
        if hover_extra:
            for col_name, label in hover_extra.items():
                extra.append(f"{label}: {row.get(col_name, 'N/A')}")
        customdata_matrix[di][wi] = '<br>'.join(extra) if extra else ''

    fig = go.Figure(data=go.Heatmap(
        z=z_matrix,
        x=week_labels,
        y=day_labels,
        colorscale=STRAVA_HEATMAP_COLORSCALE,
        xgap=3,
        ygap=3,
        showscale=True,
        colorbar=dict(
            title=dict(text=z_label, font=dict(color='#FAFAFA'), side='top'),
            tickfont=dict(color='#FAFAFA'),
            orientation='h',
            yanchor='top',
            y=-0.15,
            xanchor='center',
            x=0.5,
            thickness=12,
            len=0.5
        ),
        hoverongaps=False,
        hovertemplate=(
            '<b>%{text}</b><br>'
            f'{z_label}: ' + '%{z:.2f}<br>'
            '%{customdata}'
            '<extra></extra>'
        ),
        text=text_matrix,
        customdata=customdata_matrix
    ))
    
    # Dynamic height: 40px per day row + margins
    num_weeks = len(week_labels)
    # Add extra height for the horizontal colorbar
    height = max(280, 40 * 7 + 120)
    
    # Determine month boundaries for x-axis tick formatting
    month_ticks = _compute_month_ticks(df, date_col, week_labels)
    
    # Limit visible range to roughly 16 weeks to keep cells square-ish
    visible_weeks = min(num_weeks, 16)
    x_range = [num_weeks - visible_weeks - 0.5, num_weeks - 0.5]
    
    fig.update_layout(
        title=title,
        height=height,
        dragmode='pan',
        yaxis=dict(
            autorange='reversed',  # Mon at top
            showgrid=False,
            fixedrange=True,
        ),
        xaxis=dict(
            range=x_range,
            minallowed=-0.5,
            maxallowed=num_weeks - 0.5,
            showgrid=False,
            fixedrange=False,
            side='top',
            tickvals=month_ticks['vals'],
            ticktext=month_ticks['text'],
        ),
        **CHART_LAYOUT
    )
    
    # Override bottom margin for this specific chart so the horizontal colorbar isn't clipped
    fig.update_layout(margin=dict(l=10, r=10, t=40, b=80))
    
    # Month separator lines
    for boundary in month_ticks['boundaries']:
        fig.add_vline(
            x=boundary - 0.5,
            line_width=1,
            line_color='rgba(128, 128, 128, 0.4)',
            line_dash='dot'
        )
    
    return fig

def create_github_heatmap(
    df: pd.DataFrame, x_col: str, z_col: str, title: str,
    z_label: str = "Distance (km)",
    hover_extra_cols: dict = None  # e.g. {'workout_types': 'Workout', 'pace_str': 'Pace'}
) -> go.Figure:
    """Create a 1D activity strip heatmap. Used for short date ranges (≤7 days)."""
    # Build customdata for enriched hover
    customdata_list = []
    if hover_extra_cols:
        for _, row in df.iterrows():
            parts = [f"{label}: {row.get(col, 'N/A')}" for col, label in hover_extra_cols.items()]
            customdata_list.append('<br>'.join(parts))
    else:
        customdata_list = [''] * len(df)

    hover_tpl = '%{x}<br>' + f'{z_label}: ' + '%{z:.2f}<br>%{customdata}<extra></extra>'

    fig = go.Figure(data=go.Heatmap(
        z=[df[z_col]],
        x=df[x_col],
        y=[''],
        colorscale=STRAVA_HEATMAP_COLORSCALE,
        customdata=[customdata_list],
        xgap=3, ygap=3,
        showscale=True,
        colorbar=dict(
            title=dict(text=z_label, font=dict(color='#FAFAFA'), side='top'),
            tickfont=dict(color='#FAFAFA'),
            orientation='h',
            yanchor='top',
            y=-0.5,
            xanchor='center',
            x=0.5,
            thickness=12,
            len=0.5
        ),
        hovertemplate=hover_tpl
    ))
    fig.update_layout(
        title=title, height=180,
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False, fixedrange=True),
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=True, fixedrange=True),
        **CHART_LAYOUT
    )
    
    # Override bottom margin so the horizontal colorbar isn't clipped
    fig.update_layout(margin=dict(l=10, r=10, t=40, b=80))
    
    return fig

def create_donut(df: pd.DataFrame, names: str, values: str, title: str, color_discrete_map: dict = None, category_orders: dict = None, sort: bool = True) -> go.Figure:
    """Create a donut chart."""
    fig = px.pie(df, values=values, names=names, color=names, hole=0.4, title=title,
                 color_discrete_sequence=px.colors.qualitative.Pastel if not color_discrete_map else None,
                 color_discrete_map=color_discrete_map,
                 category_orders=category_orders)
    fig.update_layout(**CHART_LAYOUT)
    if not sort:
        fig.update_traces(sort=False)
    return fig

def create_histogram(df: pd.DataFrame, x: str, title: str, ref_line: float = None) -> go.Figure:
    """Create a histogram with an optional vertical reference line."""
    fig = px.histogram(df, x=x, title=title, color_discrete_sequence=['#FC4C02'])
    
    if ref_line is not None:
        fig.add_vline(x=ref_line, line_width=2, line_dash="dash", line_color="green")
        
    fig.update_layout(**CHART_LAYOUT)
    return fig
