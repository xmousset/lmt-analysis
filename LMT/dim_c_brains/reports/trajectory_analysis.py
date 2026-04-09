"""
@author: xmousset
"""

import pandas as pd
import plotly.express as px

from dim_c_brains.scripts.reports_manager import HTMLReportManager
from dim_c_brains.reports.overview_analysis import get_activity_card

COLOR_MAP = px.colors.qualitative.Plotly


def generic_reports(
    report_manager: HTMLReportManager,
    df: pd.DataFrame | None,
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
    fps : int, optional
        The frames per second of the video to use for time calculations
        (default: 30).
    """

    report_manager.reports_creation_focus("Trajectory")

    if df is None:
        report_manager.add_title(
            name="Analysis of mice trajectory",
            content="""
            No data available for the selected time interval. Please adjust
            the processing limits or check the database connection.""",
        )
        return None

    df["MIN_FROM_START"] = df["FRAME"] / kwargs.get("fps", 30) / 60

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
        f"{rfid}: {count:,} frames".replace(",", " ")
        for rfid, count in zip(df_count["RFID"], df_count["Count"])
    )
    report_manager.add_card(
        name="Detections",
        content=(
            "Number of frames where each animal was detected:<br>"
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
    fig.update_layout(
        height=600,
        xaxis=dict(scaleanchor="y", scaleratio=1),
        yaxis=dict(scaleanchor="x", scaleratio=1),
    )

    report_title = f"Density contour of animal trajectory"
    report_description = f"""
    This graph shows the density contour of animal trajectory during the
    selected time interval.
    """
    report_manager.add_report(
        name=report_title,
        html_or_figure=fig,
        top_note=report_description,
    )

    #######################################
    #   Density contour heat map   #
    #######################################
    figs = []
    for i, rfid in enumerate(plot_parameters["category_orders"]["RFID"]):
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
        fig.update_traces(
            contours_coloring="fill",
            contours_showlines=False,
            selector=dict(type="histogram2dcontour"),
            colorscale="Blues",
        )
        fig.update_layout(
            margin=dict(l=0, r=0, t=30, b=0),
            xaxis=dict(scaleanchor="y", scaleratio=1),
            yaxis=dict(scaleanchor="x", scaleratio=1),
            showlegend=False,
            title=f"RFID: {rfid}",
            plot_bgcolor="rgba(0,0,0,0)",
        )
        figs.append(fig)

    report_title = f"Density contour of animal trajectory"
    report_description = f"""
    This graph shows the density contour of animal trajectory for each animal
    during the selected time interval. The color of the trajectory lines
    represents the density of detections in this area, with darker and lighter
    colors representing respectively a higher and a lower density values.
    """

    report_manager.add_multi_fig_report(
        name=report_title,
        figures=figs,
        top_note=report_description,
        max_fig_in_row=2,
    )

    #######################################
    #   Trajectory line plot   #
    #######################################

    figs = []
    for i, rfid in enumerate(plot_parameters["category_orders"]["RFID"]):
        df_animal = df[df["RFID"] == rfid]
        fig = px.scatter(
            df_animal,
            x="X",
            y="Y",
            color="MIN_FROM_START",
            color_continuous_scale="Plotly3",
            labels={
                "X": "X position (<i>cm</i>)",
                "Y": "Y position (<i>cm</i>)",
                "MIN_FROM_START": "Time (min)",
            },
        )
        fig.update_traces(marker=dict(opacity=0.1, size=3))
        fig.update_layout(
            margin=dict(l=0, r=0, t=30, b=0),
            xaxis=dict(scaleanchor="y", scaleratio=1),
            yaxis=dict(scaleanchor="x", scaleratio=1),
            showlegend=False,
            title=f"RFID: {rfid}",
            plot_bgcolor="rgba(0,0,0,0)",
        )
        figs.append(fig)

    report_title = f"Animals trajectories"
    report_description = f"""
    This graph shows the trajectory of each animal. The color of the trajectory
    lines represents the time progression, with darker colors for the beggining 
    (earlier time points) and lighter colors for the end (later time points) of
    the experiment.
    """

    report_manager.add_multi_fig_report(
        name="",
        figures=figs,
        top_note="Trajectory lines colored by time progression",
        max_fig_in_row=2,
    )

    #######################################
    #   TABLE   #
    #######################################
    text = (
        "The complete table data used to create the above graphs can be "
        "generated using the code below. The application use the "
        "<i>get_df_trajectory</i> method from <i>DataFrameConstructor</i> that "
        "return the trajectory as a pandas DataFrame. Here is the code of "
        "this method (it supposed you already know how to connect to your "
        "SQLite database):"
    )

    code = "<pre><code class='language-python'>"
    code += """
        animal_pool = AnimalPool()
        animal_pool.loadAnimals(connection)
        animal_pool.loadDetection(lightLoad=True)
        
        # area filtering is optional,
        filter_area = False
        if filter_area:
            # Example centered area, replace with actual values
            animal_pool.filterDetectionByArea(15, 15, 35, 35)
        
        results = []
        for animal in animal_pool.getAnimalList():
            xList, yList, fList = animal.get_trajectory()
            for i in range(len(xList)):
                if np.isnan(xList[i]).any() or np.isnan(yList[i]).any():
                    continue
                results.append(
                    {
                        "RFID": animal.RFID,
                        "ANIMALID": animal.baseId,
                        "FRAME": fList[i],
                        "X": np.mean(xList[i]) * animal.parameters.scaleFactor,
                        "Y": np.mean(yList[i]) * animal.parameters.scaleFactor,
                    }
                )
        processed_df = pd.DataFrame(results)
    """
    code += "</code></pre>"

    report_manager.add_report(
        name="How to get the complete table",
        top_note=text,
        html_or_figure=code,
    )
