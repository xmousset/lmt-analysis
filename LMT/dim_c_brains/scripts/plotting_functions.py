"""
@author: Xavier MD
"""

import re
from typing import Any, List

import pandas as pd
from pandas import DataFrame
from plotly.colors import qualitative
from plotly import graph_objects as go


def draw_nights(
    fig: go.Figure,
    start_time: pd.Timestamp,
    end_time: pd.Timestamp,
    night_begin: int,
    night_duration: int,
):
    """
    Adds shaded rectangles to a Plotly figure to indicate night periods.

    Args:
        fig (go.Figure): The Plotly figure to modify.
        start_time (pd.Timestamp): The start time of the plot.
        end_time (pd.Timestamp): The end time of the plot.
        night_begin (int): The hour at which night begins (0-23).
        night_duration (int): Duration of the night in hours.

    Returns:
        go.Figure: The figure with night periods shaded.
    """
    # Collect all x values from all traces in fig.data
    x_values = []
    for trace in getattr(fig, "data"):
        if hasattr(trace, "x") and trace.x is not None:
            x_values.extend(trace.x)

    if not x_values:
        print("[WARN] draw_nights: No x values found in figure.")
        return fig

    # Convert to pandas Timestamps if needed
    x_values = pd.to_datetime(x_values)
    start_time = min(x_values)
    end_time = max(x_values)

    time = start_time
    while time < end_time:
        if time.hour == night_begin:
            x_start = time
            x_end = time + pd.Timedelta(hours=night_duration)
            if x_end > end_time:
                x_end = end_time
            fig.add_vrect(
                x0=x_start,
                x1=x_end,
                line_width=0,
                fillcolor="black",
                layer="below",
                opacity=0.1,
            )
        time += pd.Timedelta(hours=1)
    return fig


def make_rgb_transparent(color_sequence: List[str]):
    transparent_colors = [
        f"rgba{tuple(map(int, re.findall(r'\d+', c))) + (0.2,)}"
        for c in color_sequence
    ]
    return transparent_colors


def add_trace_with_shaded_min_max(
    fig: go.Figure,
    df: DataFrame,
    x_col: str,
    y_col: str,
    y_up: Any,
    y_down: Any,
    colors: tuple[List[str], List[str]] | None = None,
    idx: int = 0,
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
    colors = None
    fig.add_trace(
        go.Scatter(
            x=list(df[x_col]) + list(df[x_col])[::-1],
            y=list(y_up) + list(y_down)[::-1],
            fill="toself",
            fillcolor=(
                colors[1][idx % len(colors[1])]
                if colors is not None
                else colors
            ),
            line=dict(color="rgba(255,255,255,0)"),  # no border
            hoverinfo="skip",  # display info when mouse on it
            showlegend=True,
            name=y_col + " ± STD",
        )
    )

    fig.add_trace(
        go.Scatter(
            x=df[x_col],
            y=df[y_col],
            mode="lines",
            name=y_col,
            line=(
                dict(color=colors[0][idx % len(colors[0])])
                if colors is not None
                else colors
            ),
        )
    )


def plt_curve_shaded(
    df: DataFrame,
    x_col: str,
    y_col: str,
    y_std_col: str | None = None,
    y_min_col: str | None = None,
    y_max_col: str | None = None,
    color: str | None = None,
    color_discrete_sequence: list[str] | None = None,
    **kwargs: Any,
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
        raise ValueError(
            "Either y_std_col or both y_min_col and y_max_col must be provided."
        )

    if y_std_col is not None:
        use_std = True
    else:
        use_std = False

    if color_discrete_sequence is None:
        color_discrete_sequence = qualitative.Plotly

    transparent_colors = make_rgb_transparent(color_discrete_sequence)

    df_copy = df.copy()
    for col in [x_col, y_col, y_std_col, y_min_col, y_max_col]:
        if col is not None and col in df_copy.columns:
            df_copy[col].fillna(0)

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
            colors=(
                (color_discrete_sequence, transparent_colors)
                if color_discrete_sequence is not None
                else None
            ),
            idx=i,
        )

    fig.update_layout(xaxis_title=x_col, yaxis_title=y_col)

    return fig
