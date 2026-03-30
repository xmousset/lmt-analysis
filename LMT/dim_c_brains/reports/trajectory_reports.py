"""
@author: xmousset
"""

import pandas as pd
import plotly.express as px

from dim_c_brains.scripts.reports_manager import HTMLReportManager
from dim_c_brains.scripts.dataframe_constructor import DataFrameConstructor
from dim_c_brains.scripts.plotting_functions import (
    str_h_min,
    floor_power10,
    draw_nights,
    line_with_shade,
)
from dim_c_brains.reports.overview_reports import get_activity_card

COLOR_MAP = px.colors.qualitative.Plotly


def generic_reports(
    report_manager: HTMLReportManager,
    df_constructor: DataFrameConstructor,
    **kwargs,
):
    """Analyse mice activity and creates a generic dataframe using the given
    `DataFrameConstructor` and construct all the generic reports into the given
    `HTMLReportManager` and returning the generated dataframe.

    Other Parameters
    ----------------
    night_begin : int, optional
        The hour when the night begins (default: 20).
    night_duration : int, optional
        The duration of the night in hours (default: 12).
    """

    report_manager.reports_creation_focus("Trajectory")
    df = df_constructor.get_df_trajectory()

    if df is None:
        report_manager.add_title(
            name="Analysis of mice trajectory",
            content="""
            No data available for the selected time interval. Please adjust
            the processing limits or check the database connection.""",
        )
        return None

    #######################################
    #   Constants & Parameters   #
    #######################################

    plot_parameters = {
        "color": "RFID",
        "category_orders": {"RFID": list(df["RFID"].cat.categories)},
    }

    #######################################
    #   Titles   #
    #######################################

    report_manager.add_title(
        name=f"Analysis of mice trajectory",
        content=f"""
        This section presents the analysis of mice trajectory recorded in the
        dataset. You <b>CANNOT</b> download the underlying data used for the
        plots because the data are not binned.""",
    )

    report_manager.add_card(
        name="Distance unit",
        content="All distances are in centimeters (<i>cm</i>).",
    )

    df_count = df.groupby("RFID").size().reset_index(name="Count")
    detections_content = "<br>".join(
        f"{rfid}: {count:,}".replace(",", " ")
        for rfid, count in zip(df_count["RFID"], df_count["Count"])
    )
    report_manager.add_card(
        name="Detections",
        content=(
            "Number of detections recorded for each animal:<br>"
            f"{detections_content}"
        ),
    )

    #######################################
    #   Density contour   #
    #######################################

    fig = px.density_contour(
        df,
        x="X",
        y="Y",
        marginal_x="histogram",
        marginal_y="histogram",
        labels={"X": "X position (<i>cm</i>)", "Y": "Y position (<i>cm</i>)"},
        **plot_parameters,
    )

    report_title = f"Density contour of animal trajectory"
    report_description = f"""
    This graph shows the density contour of animal trajectory during the
    selected time interval.
    <br>
    This graph shows the locomotor activity of each animal over time.
    """
    report_manager.add_report(
        name=report_title,
        html_figure=fig,
        top_note=report_description,
    )

    #######################################
    #   Density contour heat map   #
    #######################################
    figs = []
    for i, rfid in enumerate(df["RFID"].cat.categories):
        df_animal = df[df["RFID"] == rfid]
        fig = px.density_contour(
            df_animal,
            x="X",
            y="Y",
            color_discrete_sequence=[COLOR_MAP[i]],
            labels={
                "X": "X position (<i>cm</i>)",
                "Y": "Y position (<i>cm</i>)",
            },
        )
        fig.update_layout(
            width=400,
            height=400,
            margin=dict(l=20, r=20, t=50, b=20),
            title=f"RFID: {rfid}",
            coloraxis_colorbar_title_text="Count",
        )
        fig.update_traces(
            contours_coloring="fill",
            contours_showlines=False,
            selector=dict(type="histogram2dcontour"),
            colorscale="Blues",
        )
        figs.append(fig)

    report_title = f"Density contour of animal trajectory"
    report_description = f"""
    This graph shows the density contour of animal trajectory for each animal during the
    selected time interval.
    <br>
    This graph shows the locomotor activity of each animal over time.
    """

    report_manager.add_multi_fig_report(
        name=report_title,
        figures=figs,
        top_note=report_description,
        max_fig_in_row=4,
    )

    #######################################
    #   TABLE   #
    #######################################
    # report_manager.add_table_headers(name="complete table", df=df)=

    ################
    #   Return   #
    ################
    return df
