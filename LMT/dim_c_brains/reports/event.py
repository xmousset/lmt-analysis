"""
@author: xmousset
"""

import pandas as pd
import plotly.express as px

from dim_c_brains.scripts.reports_manager import HTMLReportManager
from dim_c_brains.scripts.plotting_functions import (
    floor_power10,
    draw_nights,
)
from LMT.dim_c_brains.reports.overview import get_event_card
from dim_c_brains.scripts.settings import AnalysisSettings, ComparisonSettings


def generic_reports(
    report_manager: HTMLReportManager,
    df: pd.DataFrame | None,
    event_name: str,
    settings: AnalysisSettings | ComparisonSettings,
):
    """For any event, construct all the generic reports into the given
    `HTMLReportManager` using the given dataframe."""

    report_manager.reports_creation_focus(event_name)

    if df is None:
        report_manager.add_title(
            name=f"Analysis of {event_name} event",
            content="""
            No data available for the selected time interval. Please adjust
            the processing limits or check the database connection.""",
        )
        return None

    #######################################
    #   Constants & Parameters   #
    #######################################

    x_axis = settings.report_x_axis
    comparator = settings.report_color

    NB_ANIMALS = df["RFID"].nunique()
    EXP_DURATION = (
        df["END_TIME"].max() - df["START_TIME"].min()
    ).total_seconds()
    NB_DAYS = EXP_DURATION / 3600 / 24

    # if settings.bin_rounding:
    #     df = df[df["START_FRAME"] != df["START_FRAME"].iloc[0]]

    nights_parameters = {
        "start_time": df["START_TIME"].min(),
        "end_time": df["END_TIME"].max(),
        "night_begin": settings.night_begin,
        "night_duration": settings.night_duration,
    }

    plot_param = settings.get_plot_parameters(df)
    xlsl_param = settings.get_xlsx_parameters(df)

    ################
    #   Graph style   #
    ################
    if comparator == "RFID":
        plot = px.line
    else:
        plot = px.scatter

    #######################################
    #   Titles   #
    #######################################

    report_manager.add_title(
        name=f"Analysis of <i>{event_name}</i> events",
        content=f"""
        This section presents the analysis of <i>{event_name}</i> events
        recorded in the dataset.<br>
        You can download the underlying data used for the plots in Excel format
        by clicking on the '<i>Download data</i>' link in the top-right hand
        corner.""",
    )
    report_manager.add_card(
        name="Duration unit",
        content="All durations are in minutes (min).",
    )

    if isinstance(settings, AnalysisSettings):
        report_manager.add_card(
            name="Time interval (bin)",
            content=f"""
            Calculated time bin is {settings.time_window} frames.
            <br>It corresponds to 
            {(settings.time_window / settings.fps / 60):.1f} minutes.
            """,
        )
    else:
        msg = """
        Calculated time bin depends on the experiment analysis. As an 
        information, we show here the analysis binning chose for each animal:
        """
        for rfid in sorted(df["RFID"].unique()):
            time_window = df[df["RFID"] == rfid]["START_TIME"].diff().max()
            time_window_min = round(time_window.total_seconds() / 60)
            msg += f"<br> - {rfid}: {time_window_min} min"
        report_manager.add_card(
            name="Time interval (bin) for each animal",
            content=msg,
        )

    #######################################
    #   Event overview card   #
    #######################################

    card = get_event_card(df, [event_name], NB_ANIMALS, NB_DAYS)

    report_manager.add_card(
        name="Animal Average Overview",
        content=card,
    )

    #######################################
    #   Total event   #
    #######################################

    df_plot = (
        df.groupby([comparator], observed=True)[["EVENT_COUNT", "DURATION"]]
        .sum()
        .reset_index()
    )

    figs = []
    figs.append(
        px.bar(
            df_plot,
            x=comparator,
            y="EVENT_COUNT",
            title=(
                f"Total <i>{event_name}</i> number of events "
                f"per {comparator}"
            ),
            **plot_param,
        )
    )
    figs.append(
        px.bar(
            df_plot,
            x=comparator,
            y="DURATION",
            title=(
                f"Total <i>{event_name}</i> events duration "
                f"per {comparator}"
            ),
            labels={"DURATION": "DURATION (min)"},
            **plot_param,
        )
    )

    report_description = f"""
    Total number of <i>{event_name}</i> event (EVENT_COUNT) and the sum of
    their duration in minutes (DURATION) for each {comparator}.
    <br>
    This graph allows a visualization of the number of events each 
    {comparator} has done and the time spent in this event.<br>
    <br>
    <div style="color: #DE9BDE"><i>
    <b>Note:</b> Data for each {comparator} is always valid.<br>
    However, if an event involves N animals (N > 1) and is symmetrical
    (e.g., an 'Oral-oral contact' event), the total number of events is
    obtained by dividing the sum of the number of events for each animal by N.
    </i></div>
    """
    report_manager.add_multi_fig_report(
        name=f"Event overview",
        figures=figs,
        top_note=report_description,
        graph_datas=df_plot,
    )

    #######################################
    #   Mean and STD   #
    #######################################

    figs = []

    df_plot = (
        df.groupby(comparator, observed=True)[["EVENT_COUNT", "DURATION"]]
        .agg(["mean", "std"])
        .reset_index()
    )
    df_plot.columns = [
        comparator,
        "EVENT_COUNT_MEAN",
        "EVENT_COUNT_STD",
        "DURATION_MEAN",
        "DURATION_STD",
    ]

    figs.append(
        px.bar(
            df_plot,
            x=comparator,
            y="EVENT_COUNT_MEAN",
            error_y="EVENT_COUNT_STD",
            error_y_minus=[0] * len(df_plot),
            title=(
                f"Mean and Std of EVENT_COUNT per bin " f"per {comparator}"
            ),
            labels={"EVENT_COUNT_MEAN": "EVENT_COUNT per bin"},
            **plot_param,
        )
    )

    figs.append(
        px.bar(
            df_plot,
            x=comparator,
            y="DURATION_MEAN",
            error_y="DURATION_STD",
            error_y_minus=[0] * len(df_plot),
            title=(f"Mean and Std of DURATION per bin " f"per {comparator}"),
            labels={"DURATION_MEAN": "DURATION (min) per bin"},
            **plot_param,
        )
    )

    report_title = "Event duration mean and standard deviation"
    report_description = f"""
    The mean of all <i>{event_name}</i> events duration (DURATION_MEAN) with
    the standard deviation (DURATION_STD) per {comparator}.
    <br>
    This graph allows a visualization of the mean duration of one event for
    each {comparator} as well as the variability of this duration.
    """
    report_manager.add_multi_fig_report(
        name=report_title,
        figures=figs,
        top_note=report_description,
        graph_datas=df_plot,
    )

    #######################################
    #   Event per hour of the day   #
    #######################################

    df_plot = df.copy()
    df_plot["DAYS"] = df_plot[x_axis].apply(lambda x: x.day)
    df_plot["HOUR"] = df_plot[x_axis].apply(lambda x: x.hour)

    nb_days_per_hour = []
    for h in range(24):
        nb_days_per_hour.append(
            df_plot[df_plot["HOUR"] == h]["DAYS"].nunique()
        )

    df_plot = (
        df_plot.groupby([comparator, "HOUR"], observed=True)[
            ["EVENT_COUNT", "DURATION"]
        ]
        .sum()
        .reset_index()
        .sort_values(by="HOUR")
    )

    for color in plot_param["category_orders"][comparator]:
        for h in sorted(
            df_plot[df_plot[comparator] == color]["HOUR"].unique()
        ):
            df_plot.loc[
                (df_plot[comparator] == color) & (df_plot["HOUR"] == h),
                "DAYS",
            ] = nb_days_per_hour[h]

    df_plot["EVENT_COUNT_PER_DAY"] = df_plot["EVENT_COUNT"] / df_plot["DAYS"]
    df_plot["DURATION_PER_DAY"] = df_plot["DURATION"] / df_plot["DAYS"]

    df_plot["HOUR"] = df_plot["HOUR"].astype(str) + "h"

    figs = []
    figs.append(
        px.line_polar(
            df_plot,
            r="EVENT_COUNT_PER_DAY",
            theta="HOUR",
            line_close=True,
            title="Hourly EVENT_COUNT_PER_DAY",
            **plot_param,
        )
    )
    last_tick = floor_power10(df_plot["EVENT_COUNT_PER_DAY"].max())
    if last_tick < 1:
        tick_label = f"{last_tick:.1f}"
    else:
        tick_label = str(int(last_tick))
    figs[-1].update_polars(
        radialaxis_tickvals=[last_tick], radialaxis_ticktext=[tick_label]
    )

    figs.append(
        px.line_polar(
            df_plot,
            r="DURATION_PER_DAY",
            theta="HOUR",
            line_close=True,
            title="Hourly DURATION_PER_DAY (min)",
            **plot_param,
        )
    )
    last_tick = floor_power10(df_plot["DURATION_PER_DAY"].max())
    if last_tick < 1:
        tick_label = f"{last_tick:.1f}"
    else:
        tick_label = str(int(last_tick))
    figs[-1].update_polars(
        radialaxis_tickvals=[last_tick], radialaxis_ticktext=[tick_label]
    )

    report_description = f"""
    Total number of <i>{event_name}</i> events and duration per 
    {comparator} and per hour of the day.
    
    Cumulated number (EVENT_COUNT_PER_DAY) and cumulated time
    (DURATION_PER_DAY) taken by <i>{event_name}</i> event for each 
    {comparator} over each hour of the day divided by the numbers 
    of times this hour occurs (DAYS).
    <br>
    This graph allows a visualization hours by hours of the <i>{event_name}</i>
    event for each {comparator}.
    """
    report_manager.add_multi_fig_report(
        name=f"Event per hour of the day",
        figures=figs,
        top_note=report_description,
        max_fig_in_row=2,
        graph_datas=df_plot,
    )

    #######################################
    #   Event counts   #
    #######################################

    fig = plot(
        df,
        x=x_axis,
        y="EVENT_COUNT",
        title=f"EVENT_COUNT per {comparator} over {x_axis}",
        **plot_param,
    )
    fig = draw_nights(fig, **nights_parameters)

    report_title = f"Number of event per {comparator} over time"
    report_description = f"""
    Number of <i>{event_name}</i> event (EVENT_COUNT) for each
    {comparator} over time ({x_axis}) during the interval time 
    window.
    <br>
    This graph allows a visualization of the time spent by each 
    {comparator} in this event over time.
    """

    report_manager.add_report(
        name=report_title,
        html_or_figure=fig,
        top_note=report_description,
        graph_datas=df[[*xlsl_param, "EVENT_COUNT", "DURATION"]],
    )

    #######################################
    #   Event duration   #
    #######################################

    fig = plot(
        df,
        x=x_axis,
        y="DURATION",
        title=f"DURATION per {comparator} over {x_axis}",
        labels={"DURATION": "DURATION (min)"},
        **plot_param,
    )
    fig = draw_nights(fig, **nights_parameters)

    report_title = (
        f"Number of event & event duration per " f"{comparator} over time"
    )
    report_description = f"""
    Duration of <i>{event_name}</i> event (DURATION) for each
    {comparator} over time ({x_axis}) during the interval time 
    window.
    <br>
    This graph allows a visualization of the time spent by each 
    {comparator} in this event over time.
    """

    report_manager.add_report(
        name=report_title,
        html_or_figure=fig,
        top_note=report_description,
        graph_datas=df[[*xlsl_param, "EVENT_COUNT", "DURATION"]],
    )

    #######################################
    #   TABLE   #
    #######################################
    report_manager.add_table_headers(name="complete table", df=df)
