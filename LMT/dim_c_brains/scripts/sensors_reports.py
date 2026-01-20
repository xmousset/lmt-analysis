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


def generate_sensors_reports(
    report_manager: HTMLReportManager,
    df_creator: DataFrameConstructor,
    night_begin: int = 20,
    night_duration: int = 12,
):
    """Get the sensors data and construct all corresponding reports."""

    df = df_creator.process_sensors()
    report_manager.reports_creation_focus("Sensors")

    nights_parameters = {
        "start_time": df["START_TIME"].min(),
        "end_time": df["END_TIME"].max(),
        "night_begin": night_begin,
        "night_duration": night_duration,
    }

    #######################################
    #   Titles   #
    #######################################

    report_manager.add_title(
        name=f"Sensors data visualization",
        content=f"""
        This section presents the visualization of the sensors data recorded in
        the dataset. All sensors data can be downloaded in Excel format by
        clicking on the '<i>Download .xlsx</i>' link on the top-right hand
        corner of the last report (<i>complete table</i>).""",
    )

    report_manager.add_card(
        name="Time interval unit",
        content=f"""
        Calculated time bin is {df_creator.binner.bin_size} frames.<br>
        It corresponds to {df_creator.binner.bin_size / 30 / 60} minutes.
        """,
    )
    report_manager.add_card(
        name="Sensors units",
        content="???.",
    )

    #######################################
    #   Sensors plots   #
    #######################################

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

    for sensor, sensor_label, unit in zip(sensors, sensors_labels, units):

        mean_col = f"{sensor}_MEAN"
        min_col = f"{sensor}_MIN"
        max_col = f"{sensor}_MAX"

        if mean_col in df.columns:
            fig = line_with_shade(
                df,
                "START_TIME",
                mean_col,
                y_min_col=min_col,
                y_max_col=max_col,
            )
            fig = draw_nights(fig, **nights_parameters)

            fig.update_layout(
                title=f"{sensor_label} over time",
                yaxis_title=f"{sensor_label} ({unit})",
                xaxis_title="Time (START_TIME)",
            )

            report_title = f"{sensor_label} mean with min and max"
            report_description = f"""
            {sensor_label} mean ({mean_col}) with the minimum and maximum as
            the shaded area ({min_col}, {max_col}) over time (START_TIME).<br>
            """
            if sensor == "LIGHTVISIBLE":
                report_description += """
                This graph allows a visualization of the Day and Night cycle
                between what is expected (grey bands) and what the sensors
                recorded (line with shaded area).
                """

            report_manager.add_report(
                name=report_title,
                html_figure=fig,
                top_note=report_description,
                graph_datas=df[
                    [
                        "START_TIME",
                        "END_TIME",
                        mean_col,
                        min_col,
                        max_col,
                    ]
                ],
            )
        else:
            report_manager.add_report(
                name=f"{sensor_label} data not available",
                html_figure=f"""
                No data available for {sensor} sensor in this dataset.
                """,
            )

    #######################################
    #   TABLE   #
    #######################################
    report_manager.add_table(name=f"complete table", df=df)
