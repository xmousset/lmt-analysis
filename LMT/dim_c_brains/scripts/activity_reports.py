"""
@author: xmousset
"""

import plotly.express as px

from dim_c_brains.scripts.reports_manager import HTMLReportManager
from dim_c_brains.scripts.data_extractor import DataFrameConstructor
from dim_c_brains.scripts.plotting_functions import (
    draw_nights,
    line_with_shade,
)


def generate_activity_reports(
    report_manager: HTMLReportManager,
    df_constructor: DataFrameConstructor,
    filter_flickering: bool = False,
    filter_stop: bool = False,
    night_begin: int = 20,
    night_duration: int = 12,
):
    """Analyse mice activity and creates a generic dataframe using the given
    `DataFrameConstructor` and construct all the generic reports into the given
    `HTMLReportManager` and returning the generated dataframe.
    """

    df = df_constructor.process_activity(filter_flickering, filter_stop)
    report_manager.reports_creation_focus("Activity")

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
        name=f"Analysis of mice activity",
        content=f"""
        This section presents the analysis of mice Activity recorded in the
        dataset. You can download the underlying data used for the plots
        in Excel format by clicking on the '<i>Download .xlsx</i>' link on the
        top-right hand corner.""",
    )

    report_manager.add_card(
        name="Time interval unit",
        content=f"""
        Calculated time bin is {df_constructor.binner.bin_size} frames.<br>
        It corresponds to {df_constructor.binner.bin_size / 30 / 60} minutes.
        """,
    )
    report_manager.add_card(
        name="Distance unit",
        content="All distances are in centimeters (cm).",
    )
    report_manager.add_card(
        name="Speed unit",
        content="All speeds are in centimeters per second (cm/s).",
    )

    #######################################
    #   Distance   #
    #######################################

    fig = px.bar(
        df,
        "START_TIME",
        "DISTANCE",
        labels={"DISTANCE": "DISTANCE (cm)"},
        **plot_parameters,
    )
    fig = draw_nights(fig, **nights_parameters)

    report_title = f"Total distance travelled"
    report_description = f"""
    This graph shows the total distance in centimeters (DISTANCE) travelled by
    each animal (RFID) over time (START_TIME) during the interval time window.
    <br>
    This graph allows a visualization of the locomotor activity of each animal
    over time.
    """
    report_manager.add_report(
        name=report_title,
        html_figure=fig,
        top_note=report_description,
        graph_datas=df[["START_TIME", "DISTANCE", "RFID"]],
    )

    #######################################
    #   Stop count   #
    #######################################

    fig = px.bar(df, "START_TIME", "STOP_COUNT", **plot_parameters)
    fig = draw_nights(fig, **nights_parameters)

    report_title = f"Total stop count"
    report_description = f"""
    Total number of event "Stop" (STOP_COUNT) by each animal (RFID) over time
    (START_TIME) during the interval time window.
    <br>
    This graph allows a visualization of how many pauses each animal has taken
    over time.
    """
    report_manager.add_report(
        name=report_title,
        html_figure=fig,
        top_note=report_description,
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
            title="Hourly MOVE_DURATION",
            **plot_parameters,
        )
    )
    figs.append(
        px.bar_polar(
            df_plot,
            r="STOP_DURATION",
            theta="HOUR",
            title="Hourly STOP_DURATION",
            **plot_parameters,
        )
    )
    figs.append(
        px.line_polar(
            df_plot,
            r="MOVE_DURATION",
            theta="HOUR",
            line_close=True,
            title="Hourly MOVE_DURATION (Line)",
            **plot_parameters,
        )
    )
    figs.append(
        px.line_polar(
            df_plot,
            r="STOP_DURATION",
            theta="HOUR",
            line_close=True,
            title="Hourly STOP_DURATION (Line)",
            **plot_parameters,
        )
    )

    report_description = f"""
    Cumulated time taken by <i>Stop</i> events (STOP_DURATION) by each animal
    (RFID) over each hour of the day.
    <br>
    The opposite is the time spent moving (MOVE_DURATION). It is calculated as
    the interval time window minus STOP_DURATION.
    <br>
    This graph allows a visualization of the activity of each animal hours by
    hours.
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

    # fig = px.bar(
    #     df,
    #     "START_TIME",
    #     "SPEED_SUM",
    #     color="RFID",
    #     labels={"SPEED_SUM": "SPEED_SUM (cm/s)"},
    # )
    # fig = draw_nights(fig, **nights_parameters)

    # report_title = f"Cumulative speed"
    # report_description = f"""
    # Cumulated speed (SPEED_SUM) of each animal (RFID) over time (START_TIME)
    # during the interval time window.
    # <br>
    # This graph allows a visualization of how much the activity of each animal
    # hours by hours.
    # """
    # report_manager.add_report(
    #     name=report_title,
    #     figure=fig,
    #     note=report_description,
    #     graph_datas=df[["START_TIME", "SPEED_SUM", "RFID"]],
    # )

    #######################################
    #   Speed mean and std   #
    #######################################

    fig = line_with_shade(
        df,
        "START_TIME",
        "SPEED_MEAN",
        y_std_col="SPEED_STD",
        **plot_parameters,
    )
    fig.update_layout(yaxis_title="SPEED_MEAN (cm/s)")
    fig = draw_nights(fig, **nights_parameters)

    report_title = f"Mean speed with std"
    report_description = f"""
    Mean speed (SPEED_MEAN) with the standard deviation (SPEED_STD) for each
    animal (RFID) over time (START_TIME).
    """

    report_manager.add_report(
        name=report_title,
        html_figure=fig,
        top_note=report_description,
        graph_datas=df[["START_TIME", "SPEED_MEAN", "SPEED_STD", "RFID"]],
    )

    #######################################
    #   TABLE   #
    #######################################
    report_manager.add_table(name=f"complete table", df=df)

    #######################################
    #   Return   #
    #######################################
    return df
