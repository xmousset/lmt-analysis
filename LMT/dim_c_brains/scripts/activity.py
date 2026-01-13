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


def get_activity_reports(
    report_manager: HTMLReportManager,
    df_creator: DataFrameConstructor,
    filter_flickering: bool = False,
    filter_stop: bool = False,
):
    """Analyze the activity and construct all the generic reports."""

    df = df_creator.process_activity(filter_flickering, filter_stop)
    report_manager.reports_creation_focus("Activity")

    report_manager.add_title(
        name=f"Analysis of mice activity",
        content=f"""
        This section presents the analysis of mice Activity recorded in the
        dataset. You can download the underlying data used for the plots
        in Excel format by clicking on the '<i>Download .xlsx</i>' link on the
        top-right hand corner.\nAll distance are in centimeters (cm) and all
        speeds are in centimeters per second (cm/s)""",
    )

    #######################################
    #   Distance   #
    #######################################

    fig = px.bar(
        df,
        "START_TIME",
        "DISTANCE",
        color="RFID",
        labels={"DISTANCE": "DISTANCE (cm)"},
    )

    report_title = f"Total distance travelled"
    report_description = f"""
    Total DISTANCE travelled by each animal (RFID) over START_TIME.
    """
    report_manager.add_report(
        name=report_title,
        figure=fig,
        note=report_description,
        graph_datas=df[["START_TIME", "DISTANCE", "RFID"]],
    )

    #######################################
    #   Stop count   #
    #######################################

    fig = px.bar(df, "START_TIME", "STOP_COUNT", color="RFID")

    report_title = f"Total stop count"
    report_description = f"""
    Total number of stops (STOP_COUNT) by each animal (RFID) over START_TIME.
    """
    report_manager.add_report(
        name=report_title,
        figure=fig,
        note=report_description,
        graph_datas=df[["START_TIME", "STOP_COUNT", "RFID"]],
    )

    #######################################
    #   Movement and stop duration per hour of the day   #
    #######################################
    df_plot = df.copy()
    df_plot["HOUR"] = df_plot["START_TIME"].apply(lambda x: x.hour)
    df_plot = (
        df_plot.groupby(["RFID", "HOUR"], observed=True)[
            ["MOVE_DURATION", "STOP_DURATION"]
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
            r="MOVE_DURATION",
            theta="HOUR",
            color="RFID",
            title="Hourly MOVE_DURATION",
        )
    )
    figs.append(
        px.bar_polar(
            df_plot,
            r="STOP_DURATION",
            theta="HOUR",
            color="RFID",
            title="Hourly STOP_DURATION",
        )
    )
    figs.append(
        px.line_polar(
            df_plot,
            r="MOVE_DURATION",
            theta="HOUR",
            line_close=True,
            color="RFID",
            title="Hourly MOVE_DURATION (Line)",
        )
    )
    figs.append(
        px.line_polar(
            df_plot,
            r="STOP_DURATION",
            theta="HOUR",
            line_close=True,
            color="RFID",
            title="Hourly STOP_DURATION (Line)",
        )
    )

    report_description = f"""
    MOVE_DURATION and STOP_DURATION per animal and per hour of the day.
    """
    report_manager.add_multi_fig_report(
        name=f"Movement and stop duration per hour of the day",
        figures=figs,
        note=report_description,
        max_fig_in_row=2,
        graph_datas=df_plot,
    )

    #######################################
    #   Cumulative speeds   #
    #######################################

    fig = px.bar(
        df,
        "START_TIME",
        "SPEED_SUM",
        color="RFID",
        labels={"SPEED_SUM": "SPEED_SUM (cm/s)"},
    )

    report_title = f"Cumulative speed"
    report_description = f"""
    Cumulative speed (SPEED_SUM) for each animal (RFID) over START_TIME.
    """
    report_manager.add_report(
        name=report_title,
        figure=fig,
        note=report_description,
        graph_datas=df[["START_TIME", "SPEED_SUM", "RFID"]],
    )

    #######################################
    #   Speed mean and std   #
    #######################################

    fig = plt_curve_shaded(
        df,
        "START_TIME",
        "SPEED_MEAN",
        y_std_col="SPEED_STD",
        color="RFID",
    )
    fig.update_layout(yaxis_title="SPEED_MEAN (cm/s)")

    report_title = f"Mean speed with std"
    report_description = f"""
    Mean speed (SPEED_MEAN) with the standard deviation (SPEED_STD) for each
    animal (RFID) over START_TIME.
    """
    report_manager.add_report(
        name=report_title,
        figure=fig,
        note=report_description,
        graph_datas=df[["START_TIME", "SPEED_MEAN", "SPEED_STD", "RFID"]],
    )

    #######################################
    #   TABLE   #
    #######################################
    report_manager.add_table(name=f"complete_table", df=df)
