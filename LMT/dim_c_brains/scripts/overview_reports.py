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
    draw_nights,
    line_with_shade,
)


def generate_overview_reports(
    report_manager: HTMLReportManager,
    df_constructor: DataFrameConstructor,
    file_path: Path,
    df_activity: pd.DataFrame | None = None,
    df_events: pd.DataFrame | None = None,
    df_sensors: pd.DataFrame | None = None,
):

    report_manager.reports_creation_focus("main")
    df_animals = df_constructor.get_df_animals()

    exp_start_time, exp_end_time = df_constructor.get_time_limits()
    experiment = {
        "name": file_path.stem,
        "start_time": exp_start_time,
        "end_time": exp_end_time,
        "duration": exp_end_time - exp_start_time,
        "nb_animals": df_animals["RFID"].nunique(),
        "binning_frames": df_constructor.binner.bin_size,
        "binning_minutes": df_constructor.binner.bin_size / 30 / 60,
    }

    days_for_mean = experiment["duration"].total_seconds() / 3600 / 24

    #######################################
    #   Titles   #
    #######################################

    report_manager.add_title(
        name=f"{file_path.stem}",
        content=f"""
        <div style="width:80%; margin: 0 auto; text-align: center;">
            <div style="margin-bottom:1em;">
                This is a summary of the <i>{file_path.stem}</i> dataset analysis. As a
                reminder, if you want to compare this analysis with another one,
                you must ensure they have the same binning size.
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

    report_manager.add_card(
        name=f"Experiment informations",
        content=f"""
        <div style="flex: 0 0 320px; min-width: 220px; max-width: 400px;">
                <div style="margin:0; padding:0;">
                    <p style="margin: 0.5em 0;">Include <strong>{experiment["nb_animals"]} animals</strong></p>
                    <p style="margin: 0.5em 0;">Run during <strong>{experiment["duration"].days} days</strong> and <strong>{experiment["duration"].seconds // 3600} hours</strong></p>
                    <p style="margin: 0.5em 0;">Binned every <strong>{experiment["binning_minutes"]} minutes</strong></p>
                    <p style="margin: 0.5em 0;">{experiment["start_time"].strftime("%Y %B - %A %d - %H:%M")} - start</p>
                    <p style="margin: 0.5em 0;">{experiment["end_time"].strftime("%Y %B - %A %d - %H:%M")} - end</p>
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

        mean_distance = round(
            df_activity["DISTANCE"].sum()
            / experiment["nb_animals"]
            / days_for_mean
            / 100
        )
        card += f"""
        <p style='margin: 0.5em 0;'><strong>Distance</strong>, 
        average of {mean_distance} m / animal / day</p>
        """

        mean_speed = round(df_activity["SPEED_MEAN"].mean())
        card += f"""
        <p style='margin: 0.5em 0;'><strong>Speed</strong>, 
        average of {mean_speed} cm/s for each animals</p>
        """

        mean_move_duration = round(
            df_activity["MOVE_DURATION"].sum()
            / experiment["nb_animals"]
            / days_for_mean
            / 60
        )
        card += f"""
        <p style='margin: 0.5em 0;'><strong>Active time</strong>, 
        average of {mean_move_duration} hours / animal / day</p>
        """

        mean_stop_duration = round(
            df_activity["STOP_DURATION"].sum()
            / experiment["nb_animals"]
            / days_for_mean
            / 60
        )
        card += f"""
        <p style='margin: 0.5em 0;'><strong>Idle time</strong>, 
        average of {mean_stop_duration} hours / animal / day</p>
        """

        card += "</div></div>"

        report_manager.add_card(
            name="Activity",
            content=card,
        )
    else:
        report_manager.add_card(
            name="Activity",
            content="<p>No activity analysed.</p>",
        )

    #######################################
    #   Analysed events   #
    #######################################
    if df_events is not None:

        card = """<div style="flex: 0 0 320px; min-width: 220px;
        max-width: 400px;"> <div style="margin:0; padding:0;">
        """
        for event in df_events["EVENT"].unique():
            mean_count = round(
                df_events[df_events["EVENT"] == event]["EVENT_COUNT"].sum()
                / experiment["nb_animals"]
                / days_for_mean
            )
            mean_duration = round(
                df_events[df_events["EVENT"] == event]["DURATION"].sum()
                / experiment["nb_animals"]
                / days_for_mean
                / 60,
                1,
            )
            card += f"<p style='margin: 0.5em 0;'><strong>{event}</strong>, <span>&asymp;</span> {mean_duration} hours / animal / day for this event with <span>&asymp;</span> {mean_count} total events / animal / day</p>"
        card += "</div></div>"

        report_manager.add_card(
            name="Events",
            content=card,
        )
    else:
        report_manager.add_card(
            name="Events",
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
            if sensor + "_MEAN" not in df_sensors.columns:
                card += f"<p style='margin: 0.5em 0;'>{label} data not available</p>"
            else:
                mean = round(df_sensors[sensor + "_MEAN"].mean(), 2)
                std = round(df_sensors[sensor + "_MEAN"].std(), 2)
                card += f"<p style='margin: 0.5em 0;'>{label} : <strong>{mean}</strong> <span>&plusmn;</span> {std} {unit}</p>"
        card += "</div></div>"

        report_manager.add_card(
            name="Sensors",
            content=card,
        )
    else:
        report_manager.add_card(
            name="Sensors",
            content="<p>No sensor data available.</p>",
        )
