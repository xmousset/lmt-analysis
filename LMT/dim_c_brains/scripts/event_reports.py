"""
@author: Xavier MD
"""

import plotly.express as px

from dim_c_brains.scripts.reports_manager import HTMLReportManager
from dim_c_brains.scripts.data_extractor import DataFrameConstructor
from dim_c_brains.scripts.plotting_functions import (
    draw_nights,
    line_with_shade,
)


def generate_event_reports(
    report_manager: HTMLReportManager,
    df_creator: DataFrameConstructor,
    event_name: str = "Oral-oral Contact",
    night_begin: int = 20,
    night_duration: int = 12,
):
    """Analyze any event and construct all the generic reports."""

    df = df_creator.process_event(event_name)
    report_manager.reports_creation_focus(event_name)
    event_name_italic = f"<i>{event_name}</i>"

    nights_parameters = {
        "start_time": df["START_TIME"].min(),
        "end_time": df["END_TIME"].max(),
        "night_begin": night_begin,
        "night_duration": night_duration,
    }

    plot_parameters = {
        "color": "RFID",
        "category_orders": {"RFID": list(df["RFID"].cat.categories)},
    }

    #######################################
    #   Titles   #
    #######################################

    report_manager.add_title(
        name=f"Analysis of {event_name_italic} events",
        content=f"""
        This section presents the analysis of {event_name_italic} events
        recorded in the dataset.<br>
        You can download the underlying data used for the plots in Excel format
        by clicking on the '<i>Download .xlsx</i>' link on the top-right hand
        corner.""",
    )

    report_manager.add_card(
        name="Time interval unit",
        content=f"""
        Calculated time bin is {df_creator.binner.bin_size} frames.<br>
        It corresponds to {df_creator.binner.bin_size / 30 / 60} minutes.
        """,
    )
    report_manager.add_card(
        name="Duration unit",
        content="All durations are in minutes (min).",
    )

    #######################################
    #   Total event per animal   #
    #######################################

    df_plot = (
        df.groupby(["RFID"], observed=True)[["EVENT_COUNT", "DURATION"]]
        .sum()
        .reset_index()
    )

    figs = []
    figs.append(
        px.bar(
            df_plot,
            x="RFID",
            y="EVENT_COUNT",
            title=f"Total {event_name_italic} number of events per animal",
            **plot_parameters,
        )
    )
    figs.append(
        px.bar(
            df_plot,
            x="RFID",
            y="DURATION",
            title=f"Total {event_name_italic} events duration per animal",
            labels={"DURATION": "DURATION (min)"},
            **plot_parameters,
        )
    )

    report_description = f"""
    Total number of {event_name_italic} event (EVENT_COUNT) and the sum of
    their duration in minutes (DURATION) for each animal (RFID).
    <br>
    This graph allows a visualization of the number of events each animal has
    done and the time spent in this event.
    """
    report_manager.add_multi_fig_report(
        name=f"Event overview",
        figures=figs,
        note=report_description,
        graph_datas=df_plot,
    )

    #######################################
    #   Mean and STD per animal   #
    #######################################

    df_plot = (
        df.groupby("RFID", observed=True)["DURATION"]
        .agg(["mean", "std"])
        .reset_index()
    )
    df_plot.rename(
        columns={"mean": "DURATION_MEAN", "std": "DURATION_STD"},
        inplace=True,
    )

    fig = px.bar(
        df_plot,
        x="RFID",
        y="DURATION_MEAN",
        error_y="DURATION_STD",
        error_y_minus=[0] * len(df_plot),
        title="Mean and Std of DURATION per RFID",
        labels={"DURATION_MEAN": "DURATION (min)"},
        **plot_parameters,
    )

    report_title = "Event duration mean and standard deviation"
    report_description = f"""
    The mean of all {event_name_italic} events duration (DURATION_MEAN) with
    the standard deviation (DURATION_STD) per animal (RFID).
    <br>
    This graph allows a visualization of the mean duration of one event for
    each animal as well as the variability of this duration.
    """
    report_manager.add_report(
        name=report_title,
        html_figure=fig,
        top_note=report_description,
        graph_datas=df_plot,
    )

    #######################################
    #   Event counts by hour of the day   #
    #######################################

    df_plot = df.copy()
    df_plot["HOUR"] = df_plot["START_TIME"].apply(lambda x: x.hour)
    df_plot = (
        df_plot.groupby(["RFID", "HOUR"], observed=True)[
            ["EVENT_COUNT", "DURATION"]
        ]
        .sum()
        .reset_index()
        .sort_values(by="HOUR")
    )
    df_plot["HOUR"] = df_plot["HOUR"].astype(str) + "h"

    figs = []
    figs.append(
        px.bar_polar(
            df_plot,
            r="EVENT_COUNT",
            theta="HOUR",
            title="Hourly EVENT_COUNT",
            **plot_parameters,
        )
    )
    figs.append(
        px.bar_polar(
            df_plot,
            r="DURATION",
            theta="HOUR",
            title="Hourly DURATION",
            **plot_parameters,
        )
    )
    figs.append(
        px.line_polar(
            df_plot,
            r="EVENT_COUNT",
            theta="HOUR",
            line_close=True,
            title="Hourly EVENT_COUNT (Line)",
            **plot_parameters,
        )
    )
    figs.append(
        px.line_polar(
            df_plot,
            r="DURATION",
            theta="HOUR",
            line_close=True,
            title="Hourly DURATION (Line)",
            **plot_parameters,
        )
    )

    report_description = f"""
    Total number of {event_name_italic} events and duration per animal and per
    hour of the day.
    
    Cumulated number (EVENT_COUNT) and cumulated time (DURATION) taken by
    {event_name_italic} event for each animal (RFID) over each hour of the day.
    <br>
    This graph allows a visualization hours by hours of the {event_name_italic}
    event for each animal.
    """
    report_manager.add_multi_fig_report(
        name=f"Event per hour of the day",
        figures=figs,
        note=report_description,
        max_fig_in_row=2,
        graph_datas=df_plot,
    )

    #######################################
    #   Event counts   #
    #######################################

    fig = px.bar(
        df,
        x="START_TIME",
        y="EVENT_COUNT",
        title=f"EVENT_COUNT per animal over START_TIME",
        **plot_parameters,
    )
    fig = draw_nights(fig, **nights_parameters)

    report_title = f"Number of event (EVENT_COUNT) per animal over START_TIME"
    report_description = f"""
    Number of {event_name_italic} event (EVENT_COUNT) for each animal (RFID)
    over time (START_TIME) during the interval time window.
    <br>
    This graph allows a visualization of how many times each animal has
    performed the event over time.
    """
    report_manager.add_report(
        name=report_title,
        html_figure=fig,
        top_note=report_description,
        graph_datas=df[["START_TIME", "EVENT_COUNT", "RFID"]],
    )

    #######################################
    #   Duration   #
    #######################################

    fig = px.bar(
        df,
        x="START_TIME",
        y="DURATION",
        title=f"DURATION per animal over START_TIME",
        labels={"DURATION": "DURATION (min)"},
        **plot_parameters,
    )
    fig = draw_nights(fig, **nights_parameters)

    report_title = f"Event duration (DURATION) per animal over START_TIME"
    report_description = f"""
    Duration of {event_name_italic} event (DURATION) for each animal (RFID)
    over time (START_TIME) during the interval time window.
    <br>
    This graph allows a visualization of the time spent by each animal in this
    event over time.
    """
    report_manager.add_report(
        name=report_title,
        html_figure=fig,
        top_note=report_description,
        graph_datas=df[["START_TIME", "DURATION", "RFID"]],
    )

    #######################################
    #   TABLE   #
    #######################################
    report_manager.add_table(name=f"complete table", df=df)
