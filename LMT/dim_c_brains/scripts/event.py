"""
@create at: 22-12-2026
@author: Xavier MD
"""

import os
import sys
import math
import webbrowser
from pathlib import Path
from abc import abstractmethod
from typing import Literal, List, Any

from IPython.display import clear_output

import sqlite3
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.colors import qualitative, sequential

from dim_c_brains.scripts.reports_manager import HTMLReportManager
from dim_c_brains.scripts.data_extractor import DataFrameConstructor
from dim_c_brains.scripts.plotting import plt_curve_shaded

from lmtanalysis.Animal import Animal, AnimalPool
from lmtanalysis.Measure import oneDay, oneHour, oneMinute
from lmtanalysis.Event import EventTimeLine
from lmtanalysis.ParametersMouse import ParametersMouse


def get_event_reports(
    report_manager: HTMLReportManager,
    df_creator: DataFrameConstructor,
    event_name: str = "Oral-oral Contact",
):
    """Analyze any event and construct all the generic reports."""

    df = df_creator.process_event(event_name)
    report_manager.reports_creation_focus(event_name)
    event_name_italic = f"<i>{event_name}</i>"

    report_manager.add_title(
        name=f"Analysis of {event_name_italic} events",
        content=f"""
        This section presents the analysis of {event_name_italic} events
        recorded in the dataset. You can download the underlying data used for
        the plots in Excel format by clicking on the '<i>Download .xlsx</i>'
        link on the top-right hand corner.""",
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
            color="RFID",
            title=f"Total {event_name_italic} number of events per animal",
            labels={"x": "RFID", "y": "EVENT_COUNT"},
        )
    )
    figs.append(
        px.bar(
            df_plot,
            x="RFID",
            y="DURATION",
            color="RFID",
            title=f"Total {event_name_italic} events duration per animal",
            labels={"x": "RFID", "y": "DURATION (min)"},
        )
    )

    report_description = f"""
    Total number of {event_name_italic} events and duration per animal.
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

    df_plot = df.groupby("RFID")["DURATION"].agg(["mean", "std"]).reset_index()
    df_plot.rename(
        columns={"mean": "DURATION_MEAN", "std": "DURATION_STD"},
        inplace=True,
    )

    fig = px.bar(
        df_plot,
        x="RFID",
        y="DURATION_MEAN",
        color="RFID",
        error_y="DURATION_STD",
        error_y_minus=[0] * len(df_plot),
        title="Mean and Std of DURATION per RFID",
        labels={"x": "RFID", "y": "DURATION (min)"},
    )

    report_title = (
        "Events mean duration and standard deviation "
        "(DURATION_MEAN and DURATION_STD) per animal (RFID)"
    )
    report_description = f"""
    Bar plot showing the DURATION_MEAN of {event_name_italic} events per animal (RFID).
    """
    report_manager.add_report(
        name=report_title,
        figure=fig,
        note=report_description,
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
            color="RFID",
            title="Hourly EVENT_COUNT",
        )
    )
    figs.append(
        px.bar_polar(
            df_plot,
            r="DURATION",
            theta="HOUR",
            color="RFID",
            title="Hourly DURATION",
        )
    )
    figs.append(
        px.line_polar(
            df_plot,
            r="EVENT_COUNT",
            theta="HOUR",
            line_close=True,
            color="RFID",
            title="Hourly EVENT_COUNT (Line)",
        )
    )
    figs.append(
        px.line_polar(
            df_plot,
            r="DURATION",
            theta="HOUR",
            line_close=True,
            color="RFID",
            title="Hourly DURATION (Line)",
        )
    )

    report_description = f"""
    Total number of {event_name_italic} events and duration per animal and per
    hour of the day.
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

    vars = ["START_TIME", "EVENT_COUNT", "RFID"]
    fig = px.bar(
        df,
        x=vars[0],
        y=vars[1],
        color=vars[2],
        title=f"{vars[1]} per animal over {vars[0]}",
    )

    report_title = f"Number of event ({vars[1]}) per animal over {vars[0]}"
    report_description = f"""
    Bar plot showing the number of {event_name_italic} events ({vars[1]}) per
    animal ({vars[2]}) over {vars[0]}. It does not quantify the duration of the
    events."""
    report_manager.add_report(
        name=report_title,
        figure=fig,
        note=report_description,
        graph_datas=df[[vars[0], vars[1], vars[2]]],
    )

    #######################################
    #   Frame counts   #
    #######################################

    vars = ["START_TIME", "DURATION", "RFID"]
    fig = px.bar(
        df,
        x=vars[0],
        y=vars[1],
        color=vars[2],
        title=f"{vars[1]} per animal over {vars[0]}",
    )

    report_title = f"Event duration ({vars[1]}) per animal over {vars[0]}"
    report_description = f"""
    Bar plot showing the {vars[1]} of {event_name_italic} events per animal over {vars[0]}.
    Each bar represents the {vars[1]} for a specific animal ({vars[2]}) at different time points.
    """
    report_manager.add_report(
        name=report_title,
        figure=fig,
        note=report_description,
        graph_datas=df[[vars[0], vars[1], vars[2]]],
    )

    #######################################
    #   TABLE   #
    #######################################
    report_manager.add_table(name=f"complete_table", df=df)
