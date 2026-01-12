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


def test_activity_reports(
    report_manager: HTMLReportManager,
    df_creator: DataFrameConstructor,
):

    report_manager.reports_creation_focus("Activity")
    df = df_creator.process_activity()

    report_manager.add_title(
        name=f"Analysis of mice activity",
        content=f"""
        This section presents the analysis of mice movements recorded in the
        dataset. You can download the underlying data used for the plots
        in Excel format by clicking on the '<i>Download .xlsx</i>' link on the
        top-right hand corner.\nAll distance are in centimeters (cm) and all
        speeds are in centimeters per second (cm/s)""",
    )

    #######################################
    #   Distance   #
    #######################################
    print(df.head())
    fig = px.bar(df, "START_TIME", "DISTANCE", color="RFID")

    report_title = f"Total distance travelled"
    report_description = f"""
    Total DISTANCE travelled by each animal (RFID) over TIME.
    """
    report_manager.add_report(
        name=report_title,
        figure=fig,
        note=report_description,
        graph_datas=df[["START_TIME", "DISTANCE", "RFID"]],
    )
