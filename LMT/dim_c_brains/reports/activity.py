"""
@author: xmousset
"""

from typing import Any

import pandas as pd
import plotly.express as px

from dim_c_brains.scripts.reports_manager import HTMLReportManager
from dim_c_brains.scripts.plotting_functions import (
    draw_nights,
    line_with_shade,
)
from LMT.dim_c_brains.reports.overview import get_activity_card
from dim_c_brains.scripts.settings import AnalysisSettings, ComparisonSettings


def generic_reports(
    report_manager: HTMLReportManager,
    df: pd.DataFrame | None,
    settings: AnalysisSettings | ComparisonSettings,
):
    """Construct all the generic reports into the given `HTMLReportManager`
    using the given dataframe."""

    report_manager.reports_creation_focus("Activity")

    if df is None:
        report_manager.add_title(
            name="Analysis of animal activity",
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

    # remove first value if specified in settings, to avoid rendering issues in
    # some graphs (e.g. speed graphs with min max values)
    # if settings.bin_rounding:
    #     df = df[df["START_FRAME"] != df["START_FRAME"].iloc[0]]

    nights_parameters = {
        "start_time": df[x_axis].min(),
        "end_time": df[x_axis].max(),
        "night_begin": settings.night_begin,
        "night_duration": settings.night_duration,
    }

    plot_param = settings.get_plot_parameters(df)
    xlsx_param = settings.get_xlsx_parameters(df)

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
        name=f"Analysis of animal activity",
        content=f"""
        This section presents the analysis of mice Activity recorded in the
        dataset. You can download the underlying data used for the plots
        in Excel format by clicking on the '<i>Download data</i>' link in the
        top-right hand corner.""",
    )
    report_manager.add_card(
        name="Distance unit",
        content="All distances are in centimeters (<i>cm</i>).",
    )
    report_manager.add_card(
        name="Speed unit",
        content="All speeds are in centimeters per second (<i>cm/s</i>).",
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
    #   Activity overview card   #
    #######################################

    if isinstance(settings, AnalysisSettings):
        card = get_activity_card(df, NB_ANIMALS, NB_DAYS, settings)
        report_manager.add_card(
            name="Animal Average Overview",
            content=card,
        )

    #######################################
    #   Distance   #
    #######################################

    fig = plot(
        df,
        x_axis,
        "DISTANCE",
        labels={"DISTANCE": "DISTANCE (<i>cm</i>)"},
        **plot_param,
    )
    fig = draw_nights(fig, **nights_parameters)

    report_title = f"Total distance travelled"
    report_description = f"""
    This graph shows the total distance in centimeters (DISTANCE) travelled by
    each {comparator} over {x_axis} during the interval time window.
    <br>
    This graph shows the locomotor activity of each {comparator} over time.
    """
    report_manager.add_report(
        name=report_title,
        html_or_figure=fig,
        top_note=report_description,
        graph_datas=df[[*xlsx_param, "DISTANCE"]],
    )

    #######################################
    #   Event: Stop   #
    #######################################

    fig = plot(
        df,
        x_axis,
        "STOP_DURATION",
        labels={"STOP_DURATION": "STOP_DURATION (<i>min</i>)"},
        **plot_param,
    )
    fig = draw_nights(fig, **nights_parameters)

    report_title = f"Stop duration"
    report_description = f"""
    Duration in minutes of event <i>Stop</i> (STOP_DURATION) by each 
    {comparator} over time ({x_axis}) during the interval time window.
    <br>
    This graph shows the time spent immobile by each {comparator} over time.
    """
    report_manager.add_report(
        name=report_title,
        html_or_figure=fig,
        top_note=report_description,
        graph_datas=df[[*xlsx_param, "STOP_DURATION"]],
    )

    #######################################
    #   Event: Move   #
    #######################################

    fig = plot(
        df,
        x_axis,
        "MOVE_DURATION",
        labels={"MOVE_DURATION": "MOVE_DURATION (<i>min</i>)"},
        **plot_param,
    )
    fig = draw_nights(fig, **nights_parameters)

    report_title = f"Move duration"
    report_description = f"""
    Duration in minutes of event <i>Move</i> (MOVE_DURATION) by each 
    {comparator} over time ({x_axis}) during the interval time window.
    <br>
    This graph shows the time spent moving by each {comparator} over time.
    """
    report_manager.add_report(
        name=report_title,
        html_or_figure=fig,
        top_note=report_description,
        graph_datas=df[[*xlsx_param, "MOVE_DURATION"]],
    )

    #######################################
    #   Event: Undetected   #
    #######################################

    fig = plot(
        df,
        x_axis,
        "UNDETECTED_DURATION",
        labels={"UNDETECTED_DURATION": "UNDETECTED_DURATION (<i>min</i>)"},
        **plot_param,
    )
    fig = draw_nights(fig, **nights_parameters)

    report_title = f"Undetected duration"
    report_description = f"""
    Duration in minutes of event <i>Undetected</i> (UNDETECTED_DURATION) by 
    each {comparator} over time ({x_axis}) during the interval time window.
    <br>
    This graph shows, over time, the duration when each {comparator} was not 
    detected by the LMT.
    """
    report_manager.add_report(
        name=report_title,
        html_or_figure=fig,
        top_note=report_description,
        graph_datas=df[[*xlsx_param, "UNDETECTED_DURATION"]],
    )

    #######################################
    #   Movement and stop duration per hour of the day   #
    #######################################
    df_plot = df.copy()
    df_plot["HOUR"] = df_plot[x_axis].apply(lambda x: x.hour)
    df_plot = (
        df_plot.groupby([comparator, "HOUR"], observed=True)[
            ["MOVE_DURATION", "STOP_DURATION"]
        ]
        .sum()
        .reset_index()
        .sort_values(by="HOUR")
    )
    df_plot["HOUR"] = df_plot["HOUR"].astype(str) + "h"

    figs = []
    figs.append(
        px.line_polar(
            df_plot,
            r="MOVE_DURATION",
            theta="HOUR",
            line_close=True,
            title="Hourly MOVE_DURATION (<i>min</i>)",
            **plot_param,
        )
    )
    figs.append(
        px.line_polar(
            df_plot,
            r="STOP_DURATION",
            theta="HOUR",
            line_close=True,
            title="Hourly STOP_DURATION (<i>min</i>)",
            **plot_param,
        )
    )

    report_description = f"""
    Cumulated time taken by <i>Stop</i> events (STOP_DURATION) by each 
    {comparator} over each hour of the day.
    <br>
    The opposite is the time spent moving (MOVE_DURATION) in minutes. It is
    calculated as the interval time window minus STOP_DURATION.
    <br>
    This graph shows the activity of each {comparator} hours by
    hours.
    """
    report_manager.add_multi_fig_report(
        name=f"Movement and stop duration per hour of the day",
        figures=figs,
        top_note=report_description,
        max_fig_in_row=2,
        graph_datas=df_plot,
    )

    #######################################
    #   Cumulative speeds   #
    #######################################

    # fig = plot(
    #     df,
    #     TIME,
    #     "SPEED_SUM",
    #     labels={"SPEED_SUM": "SPEED_SUM (<i>cm/s</i>)"},
    #     **plot_parameters,
    # )
    # fig = draw_nights(fig, **nights_parameters)

    # report_title = f"Cumulative speed"
    # report_description = f"""
    # Cumulated speed (SPEED_SUM) of each {comparator} over {x_axis} during
    # the interval time window.
    # <br>
    # This graph shows how much the activity of each {comparator}
    # hours by hours.
    # """
    # report_manager.add_report(
    #     name=report_title,
    #     figure=fig,
    #     note=report_description,
    #     graph_datas=df[[*xlsx_parameters, "SPEED_SUM"]],
    # )

    #######################################
    #   Speed mean and min max   #
    #######################################

    if comparator == "RFID":
        fig = line_with_shade(
            df,
            x_axis,
            "SPEED_MEAN",
            y_std_col="SPEED_STD",
            # y_min_col="SPEED_MIN",
            # y_max_col="SPEED_MAX",
            **plot_param,
        )
    else:
        fig = px.scatter(
            df,
            x_axis,
            "SPEED_MEAN",
            error_y="SPEED_STD",
            labels={"SPEED_MEAN": "SPEED_MEAN (<i>cm/s</i>)"},
            **plot_param,
        )
        fig.update_traces(opacity=0.7)

    fig.update_yaxes(range=[0, None])
    fig.update_layout(yaxis_title="SPEED_MEAN (<i>cm/s</i>)")
    fig = draw_nights(fig, **nights_parameters)

    # description for STD
    report_title = f"Mean speed with std"
    report_description = f"""
    SPEED_MEAN with the standard deviation SPEED_STD for each
    {comparator} over {x_axis}.
    """

    # description for min max
    # report_title = f"Mean speed with min and max"
    # report_description = f"""
    # SPEED_MEAN with SPEED_MIN and SPEED_MAX for each
    # {comparator} over {x_axis}.
    # """

    report_manager.add_report(
        name=report_title,
        html_or_figure=fig,
        top_note=report_description,
        graph_datas=df[[*xlsx_param, "SPEED_MEAN", "SPEED_STD"]],
    )

    #######################################
    #   TABLE   #
    #######################################
    report_manager.add_table_headers(name="complete table", df=df)
