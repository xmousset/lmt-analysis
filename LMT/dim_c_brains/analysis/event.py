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
    #   Total per animal   #
    #######################################

    df_plot = (
        df.groupby(["RFID"], observed=True)[["EVENT_COUNT", "FRAME_COUNT"]]
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
        )
    )
    figs.append(
        px.bar(
            df_plot,
            x="RFID",
            y="FRAME_COUNT",
            color="RFID",
            title=f"Total {event_name_italic} events duration per animal",
        )
    )

    report_description = f"""
    Total number of {event_name_italic} events and duration per animal.
    """
    report_manager.add_multi_fig_report(
        name=f"{event_name_italic} events resume",
        figures=figs,
        note=report_description,
        graph_datas=df_plot,
    )

    #######################################
    #   Mean and STD per animal   #
    #######################################

    df_plot = (
        df.groupby("RFID")["FRAME_COUNT"].agg(["mean", "std"]).reset_index()
    )
    df_plot.rename(
        columns={"mean": "FRAME_COUNT_MEAN", "std": "FRAME_COUNT_STD"},
        inplace=True,
    )

    fig = px.bar(
        df_plot,
        x="RFID",
        y="FRAME_COUNT_MEAN",
        color="RFID",
        error_y="FRAME_COUNT_STD",
        error_y_minus=[0] * len(df_plot),
        title="Mean and Std of FRAME_COUNT per RFID",
    )

    report_title = f"""
    {event_name_italic} events mean duration and standard deviation
    (FRAME_COUNT_MEAN and FRAME_COUNT_STD) per animal (RFID)"""
    report_description = f"""
    Bar plot showing the FRAME_COUNT_MEAN of {event_name_italic} events per animal (RFID).
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
    df_plot["HOUR"] = df_plot["TIME"].apply(lambda x: x.hour)
    df_plot = (
        df_plot.groupby(["RFID", "HOUR"], observed=True)[
            ["EVENT_COUNT", "FRAME_COUNT"]
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
            r="FRAME_COUNT",
            theta="HOUR",
            color="RFID",
            title="Hourly FRAME_COUNT",
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
            r="FRAME_COUNT",
            theta="HOUR",
            line_close=True,
            color="RFID",
            title="Hourly FRAME_COUNT (Line)",
        )
    )

    report_description = f"""
    Total number of {event_name_italic} events and duration per animal and per
    hour of the day.
    """
    report_manager.add_multi_fig_report(
        name=f"{event_name_italic} events per hour of the day",
        figures=figs,
        note=report_description,
        max_fig_in_row=2,
        graph_datas=df_plot,
    )

    #######################################
    #   Event counts   #
    #######################################

    vars = ["TIME", "EVENT_COUNT", "RFID"]
    fig = px.bar(
        df,
        x=vars[0],
        y=vars[1],
        color=vars[2],
        title=f"{vars[1]} per animal over {vars[0]}",
    )

    report_title = f"{event_name_italic} number of events ({vars[1]}) per animal over  {vars[0]}"
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

    vars = ["TIME", "FRAME_COUNT", "RFID"]
    fig = px.bar(
        df,
        x=vars[0],
        y=vars[1],
        color=vars[2],
        title=f"{vars[1]} per animal over {vars[0]}",
    )

    report_title = f"{event_name_italic} events duration ({vars[1]}) per animal over {vars[0]}"
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
    report_manager.add_table(
        name=f"{event_name_italic} events complete table", df=df
    )
