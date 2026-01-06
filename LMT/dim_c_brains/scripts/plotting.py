import re
from typing import Any, List

from plotly.colors import qualitative
from plotly import graph_objects as go
from pandas import DataFrame


def make_rgb_transparent(color_sequence : List[str]):
	transparent_colors = [
		f"rgba{tuple(map(int, re.findall(r'\d+', c))) + (0.2,)}"
		for c in color_sequence
    ]
	return transparent_colors


def add_trace_with_shaded_min_max(
    fig : go.Figure,
    df : DataFrame,
    x_col : str,
    y_col : str,
    y_up : Any,
    y_down : Any,
    colors : tuple[List[str], List[str]]|None = None,
    idx : int = 0,
    ):
    """
    Adds a line plot with a shaded region (min-max or confidence interval) to a
    Plotly figure.

    Parameters
    ----------
    fig : go.Figure
        The Plotly figure to add traces to.
    df : DataFrame
        DataFrame containing the data to plot.
    x_col : str
        Column name for x-axis values.
    y_col : str
        Column name for y-axis (mean/central) values.
    y_up : Any
        Upper bound values for the shaded region.
    y_down : Any
        Lower bound values for the shaded region.
    colors : tuple[list[str], list[str]]
        Tuple of color lists for line and fill.
    idx : int, optional
        Index for color selection. Defaults to 0.
    """
    
    fig.add_trace(go.Scatter(
        x= list(df[x_col]) + list(df[x_col])[::-1],
        y= list(y_up) + list(y_down)[::-1],
        fill= "toself",
        fillcolor= colors[1][idx % len(colors[1])] if colors is not None else colors,
        line= dict(color= "rgba(255,255,255,0)"), # no border
        # hoverinfo= "skip", # display info when mouse on it
        showlegend= True,
        name= y_col + " ± STD"
    ))

    fig.add_trace(go.Scatter(
        x= df[x_col],
        y= df[y_col],
        mode= "lines",
        name= y_col,
        line = dict(color= colors[0][idx % len(colors[0])]) if colors is not None else colors
    ))


def plt_curve_shaded(
    df : DataFrame,
    x_col : str,
    y_col : str,
    y_std_col : str|None = None,
    y_min_col : str|None = None,
    y_max_col : str|None = None,
    color : str|None = None,
    color_discrete_sequence : list[str]|None = None,
    ):
    """
    Plot a line curve with shaded error or range using Plotly.
    
    Parameters
    ----------
    df : DataFrame
        Input data containing columns for x, y, color, and error/range.
    x_col : str
        Name of the column to use for the x-axis.
    y_col : str
        Name of the column to use for the y-axis.
    color : str
        Name of the column to group and color the lines.
    y_std_col : str or None, optional
        Name of the column with standard deviation values for shading. 
        Required if y_min_col and y_max_col are not provided.
    y_min_col : str or None, optional
        Name of the column with minimum values for shading. 
        Required if y_std_col is not provided.
    y_max_col : str or None, optional
        Name of the column with maximum values for shading. 
        Required if y_std_col is not provided.
    color_discrete_sequence : list of str or None, optional
        List of colors to use for the lines. If None, a default color sequence is used.
    Returns
    -------
    fig : plotly.graph_objs.Figure
        Plotly figure object with the shaded curve plot.
    Raises
    ------
    ValueError
        If neither y_std_col nor both y_min_col and y_max_col are provided.
    """
    
    if y_std_col is None and (y_min_col is None or y_max_col is None):
        raise ValueError("Either y_std_col or both y_min_col and y_max_col must be provided.")
    
    if y_std_col is not None:
        use_std = True
    else:
        use_std = False
    
    if color_discrete_sequence is None:
        color_discrete_sequence = qualitative.Bold[::-1]
    
    transparent_colors = make_rgb_transparent(color_discrete_sequence)
    
    df_copy = df.copy().fillna(0)
    
    fig = go.Figure()

    n_clr = 1
    unique_colors = None
    if color is not None:
        unique_colors = df_copy[color].unique()
        n_clr = len(unique_colors)
    
    for i in range(n_clr):
        if unique_colors is None:
            sub_df = df_copy
        else:
            sub_df = df_copy[df_copy[color] == unique_colors[i]]
        
        if use_std:
            std_up = sub_df[y_col] + sub_df[y_std_col]
            std_low = sub_df[y_col] - sub_df[y_std_col]
        else:
            std_up = sub_df[y_max_col]
            std_low = sub_df[y_min_col]

        add_trace_with_shaded_min_max(
            fig,
            sub_df,
            x_col,
            y_col,
            std_up,
            std_low,
            colors= (color_discrete_sequence, transparent_colors) if color_discrete_sequence is not None else None,
            idx= i
        )

    fig.update_layout(
        xaxis_title= x_col,
        yaxis_title= y_col
    )
    
    return fig
