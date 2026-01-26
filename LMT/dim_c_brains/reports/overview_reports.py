"""
@author: xmousset
"""

from pathlib import Path
from typing import Literal

import plotly.express as px
import pandas as pd

from dim_c_brains.scripts.reports_manager import HTMLReportManager
from dim_c_brains.scripts.data_extractor import DataFrameConstructor
from dim_c_brains.scripts.plotting_functions import (
    str_h_min,
    draw_nights,
    line_with_shade,
)


def generate_overview_reports(
    report_manager: HTMLReportManager,
    df_constructor: DataFrameConstructor,
    df_activity: pd.DataFrame | None = None,
    df_events: pd.DataFrame | None = None,
    df_sensors: pd.DataFrame | None = None,
    **kwargs,
):
    """This function uses the provided report manager to create a structured
    summary of the experiment, including cards for experiment details, animal
    activity, analyzed events, and sensor readings.

    kwargs:
    - file_path (Path): Path to the dataset.
    - filter_flickering (bool): Whether to filter flickering activity.
    - filter_stop (bool): Whether to filter stop activity.
    - night_begin (int): The hour when the night begins.
    - night_duration (int): The duration of the night in hours.
    """

    report_manager.reports_creation_focus("main")
    df_animals = df_constructor.get_df_animals()

    #######################################
    #   Constants   #
    #######################################

    NB_ANIMALS = df_animals["RFID"].nunique()

    EXP_START, EXP_END = df_constructor.get_analysis_limits("TIME")
    EXP_DURATION = EXP_END - EXP_START
    NB_DAYS = EXP_DURATION.total_seconds() / 3600 / 24

    EXP_NAME = kwargs.get("file_path", None)
    if EXP_NAME is not None:
        EXP_NAME = EXP_NAME.stem
    else:
        EXP_NAME = "Unknown experiment"

    #######################################
    #   Titles   #
    #######################################

    report_manager.add_title(
        name=EXP_NAME,
        content=f"""
        <div style="width:80%; margin: 0 auto; text-align: center;">
            <div style="margin-bottom:1em;">
                This is a summary of the <i>{EXP_NAME}</i> dataset
                analysis. As a reminder, if you want to compare this analysis
                with another one, you must ensure they have the same binning
                size.
                <hr>
            </div>
        </div>
        <style>
            table.dataframe {{
                border-collapse: collapse;
                border: 2px solid #fff;
            }}
            table.dataframe th, table.dataframe td {{
                border: none;
                padding: 8px;
                text-align: center;
            }}
            table.dataframe th {{
                font-weight: bold;
            }}
        </style>
        <center>{df_animals.to_html(index=False, border=1)}</center>
        """,
    )

    #######################################
    #   Experiment card   #
    #######################################

    t_format = "%Y %B - %A %d - %H:%M"
    report_manager.add_card(
        name=f"Experiment informations",
        content=f"""
        <div style="flex: 0 0 320px; min-width: 220px; max-width: 400px;">
                <div style="margin:0; padding:0;">
                    <p style="margin: 0.5em 0;">Include <strong>
                    {NB_ANIMALS} animals
                    </strong></p>
                    <p style="margin: 0.5em 0;">Run during <strong>
                    {EXP_DURATION.days} days
                    </strong> and <strong>
                    {EXP_DURATION.seconds // 3600} hours
                    </strong> and <strong>
                    {(EXP_DURATION.seconds // 60) % 60} minutes
                    </strong></p>
                    <p style="margin: 0.5em 0;">Binned every <strong>
                    {df_constructor.binner.bin_size / 30 / 60} minutes
                    </strong></p>
                    <p style="margin: 0.5em 0;">
                    {EXP_START.strftime(t_format)} - start
                    </p>
                    <p style="margin: 0.5em 0;">
                    {EXP_END.strftime(t_format)} - end
                    </p>
                </div>
            </div>
        """,
    )

    #######################################
    #   Activity card   #
    #######################################
    if df_activity is not None:

        card = """<div style="flex: 0 0 320px; min-width: 220px;
        max-width: 400px;"> <div style="margin:0; padding:0;">
        """
        filters = []
        if kwargs.get("filter_flickering", False):
            filters.append("Flickering")
        if kwargs.get("filter_stop", False):
            filters.append("Stop")
        filters_str = ", ".join(filters) if filters else "no filters applied"
        card += f"""
        <p style='margin: 0.5em 0;'><strong>Applied filters</strong>: 
        {filters_str}
        </p>
        """

        mean_distance = round(
            df_activity["DISTANCE"].sum() / NB_ANIMALS / NB_DAYS / 100
        )
        card += f"""
        <p style='margin: 0.5em 0;'><strong>Distance</strong>: 
        {mean_distance} <i>m</i> each day</p>
        """

        mean_speed = round(df_activity["SPEED_MEAN"].mean())
        card += f"""
        <p style='margin: 0.5em 0;'><strong>Speed</strong>: 
        {mean_speed} <i>cm/s</i></p>
        """

        mean_duration = (
            df_activity["MOVE_DURATION"].sum() / NB_ANIMALS / NB_DAYS
        )
        card += f"""
        <p style='margin: 0.5em 0;'><strong>Move</strong>: 
        {str_h_min(mean_duration)} each day
        </p>
        """

        mean_duration = (
            df_activity["STOP_DURATION"].sum() / NB_ANIMALS / NB_DAYS
        )
        card += f"""
        <p style='margin: 0.5em 0;'><strong>Stop</strong>: 
        {str_h_min(mean_duration)} each day
        </p>
        """

        mean_duration = (
            df_activity["UNDETECTED_DURATION"].sum() / NB_ANIMALS / NB_DAYS
        )
        card += f"""
        <p style='margin: 0.5em 0;'><strong>Undetected</strong>: 
        {str_h_min(mean_duration)} each day
        </p>
        """

        card += "</div></div>"

        report_manager.add_card(
            name="Animal Average Activity",
            content=card,
        )
    else:
        report_manager.add_card(
            name="Animal Average Activity",
            content="<p>No activity analysed.</p>",
        )

    #######################################
    #   Events card   #
    #######################################
    if df_events is not None:

        card = """<div style="flex: 0 0 320px; min-width: 220px;
        max-width: 400px;"> <div style="margin:0; padding:0;">
        """
        for event in df_events["EVENT"].unique():
            mean_count = round(
                df_events[df_events["EVENT"] == event]["EVENT_COUNT"].sum()
                / NB_ANIMALS
                / NB_DAYS
            )
            mean_duration = round(
                df_events[df_events["EVENT"] == event]["DURATION"].sum()
                / NB_ANIMALS
                / NB_DAYS
            )
            card += f"""
            <p style='margin:0;'><strong>{event}</strong></p>
            <ul style='margin:0;'>
                <li>{str_h_min(mean_duration)} each day</li>
                <li>{mean_count} event each day</li>
            </ul>
            """
        card += "</div></div>"

        report_manager.add_card(
            name="Animal Average Events",
            content=card,
        )
    else:
        report_manager.add_card(
            name="Animal Average Events",
            content="<p>No event analysed.</p>",
        )

    #######################################
    #   Sensors card   #
    #######################################
    if df_sensors is not None:
        sensors = [
            "TEMPERATURE",
            "HUMIDITY",
            "SOUND",
            "LIGHTVISIBLE",
            "LIGHTVISIBLEANDIR",
        ]
        sensors_labels = [
            "Temperature",
            "Humidity",
            "Sound",
            "Light visible",
            "Light visible + IR",
        ]
        units = [
            "°C",
            "%",
            "?",
            "?",
            "?",
        ]

        card = """<div style="flex: 0 0 320px; min-width: 220px;
        max-width: 400px;"> <div style="margin:0; padding:0;">
        """
        for sensor, label, unit in zip(sensors, sensors_labels, units):
            if (
                sensor + "_MEAN" not in df_sensors.columns
                or df_sensors[sensor + "_MEAN"].isnull().all()
            ):
                card += (
                    "<p style='margin: 0.5em 0;'>"
                    f"{label} data not available"
                    "</p>"
                )
            else:
                mean = round(df_sensors[sensor + "_MEAN"].mean(), 2)
                std = round(df_sensors[sensor + "_MEAN"].std(), 2)
                card += (
                    f"<p style='margin: 0.5em 0;'>{label} : "
                    f"<strong>{mean}</strong> <span>&plusmn;</span> "
                    f"{std} <i>{unit}</i>"
                    "</p>"
                )
        card += "</div></div>"

        report_manager.add_card(
            name="Average Sensors",
            content=card,
        )
    else:
        report_manager.add_card(
            name="Average Sensors",
            content="<p>No sensor data available.</p>",
        )

    #######################################
    #   Return   #
    #######################################
    return df_animals
