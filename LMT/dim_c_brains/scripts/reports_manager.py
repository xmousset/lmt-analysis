import os
import sys
import webbrowser
from pathlib import Path
from typing import Literal, List

import pandas as pd
import plotly.graph_objects as go

from dim_c_brains.res.report.Report import Report
from dim_c_brains.res.report.WebSite import WebSite


class HTMLReportManager():
    """
    A manager for creating, organizing, and exporting HTML reports with
    Plotly figures and tables.

    This class provides methods to add individual or multiple Plotly figures,
    tables, and custom HTML content as reports. Reports can be arranged in
    rows or grids, and optional notes can be included. The manager can
    generate a local HTML website containing all accumulated reports, using
    a specified template and asset folder structure.

    Main Features:
        - Add single or multiple Plotly figures or HTML blocks as reports.
        - Arrange figures in rows or grids for flexible layouts.
        - Add tables (from pandas DataFrames) and custom HTML titles/notes.
        - Generate a local HTML output website with all reports, using
          templates and assets.

    Parameters
    ----------
        exp_name (str): Name of the experiment or report collection (used for
            folder organization).
    """
    def __init__(self):
        self.reports = []
        self.exp_name = "main"
        self.html_param = {
            "full_html": False,
            "include_plotlyjs": "cdn",
            "config": {"displaylogo": False},
        }
        self.cwd = Path(__file__).parent.parent
    
    def reports_creation_focus(self, exp_name : str = "main"):
        """Define where the new reports will be added. The main page is
        focused by default. If the input name is the same as an experiment
        that already exist, the new reports will be added after all the reports
        already created.
        """
        self.exp_name = exp_name
    
    def add_report(
        self,
        name: str,
        figure: go.Figure|str,
        note: str|None = None,
        graph_datas: pd.DataFrame|None = None
        ):
        """Add a report in `self.reports` with the appropriate parameters.
        Can automatically get a go.Figure and convert it in html.

        Parameters
        ----------
        name : str
            Name of the report.
        html : go.Figure | str
            Plotly figure to add in the report.
        """
        html = ""
        if note is not None:
            html += note + "<hr>"
        
        if isinstance(figure, go.Figure):
            html += figure.to_html(**self.html_param)
        else:
            html += figure
        
        report = Report(
            name,
            html,
            experimentName= self.exp_name
        )
        if graph_datas is not None:
            report.setDownloadableContent("Download .xlsx", graph_datas)
        self.reports.append(report)
    
    def add_multi_fig_report(
        self,
        name: str,
        figures: List[go.Figure|str],
        note: str|None = None,
        max_fig_in_row: int|None = None,
        graph_datas: pd.DataFrame|None = None,
        ):
        """
        Add multiple Plotly figures as a single report, displayed in a matrix
        layout.

        Parameters
        ----------
        name : str
            The name of the report.
        figures : List[go.Figure | str]
            A list of Plotly figures or HTML strings to include in the report.
        note : str | None
            An optional note to include above the figures.
        max_fig_in_row : int | None
            Maximum number of figures to display in each row. If None, all
            figures will be displayed in a single row.
        """
        nb_fig = len(figures)
        html = ""
        
        if nb_fig == 0:
            return
        
        if max_fig_in_row is None:
            cols = nb_fig
            rows = 1
        else:
            cols = min(max_fig_in_row, nb_fig)
            rows = (nb_fig + cols - 1) // cols
        
        if note is not None:
            html += note + "<hr>"
        
        html += "<div class='container'>"
        for j in range(rows):
            html += "<div class='row'>"
            for i in range(cols):
                idx = j * cols + i
                if idx < nb_fig:
                    html += f"<div class='col-{12 // cols}'>"
                    figure = figures[idx]
                    if isinstance(figure, str):
                        html += figure
                    else:
                        html += figure.to_html(**self.html_param)
                    html += "</div>"
            html += "</div>"
        html += "</div>"
        
        report = Report(
            name,
            html,
            experimentName= self.exp_name
        )
        
        if graph_datas is not None:
            report.setDownloadableContent("Download .xlsx", graph_datas)
            
        self.reports.append(report)
    
    def add_title(
        self,
        name: str,
        content: str = "",
        style: Literal["primary", "success", "danger", "warning"]= "success"
        ):
        """Add a title block as a report."""
        report = Report(
            name,
            content,
            experimentName= self.exp_name,
            template= "splitter.html",
            style= style
        )
        self.reports.append(report)
    
    def add_table(self, name: str, df: pd.DataFrame):
        """Add a table report from a pandas DataFrame."""
        report = Report(
            name,
            df,
            experimentName= self.exp_name,
            template= "table.html",
        )
        report.setDownloadableContent("Download .xlsx", df)
        self.reports.append(report)
    
    def generate_local_output(
        self,
        output_name: str,
        ):
        """Generate an HTML output locally from the accumulated reports."""
        output_folder = self.cwd / f"{output_name}"
        output_folder.mkdir(parents=True, exist_ok=True)
        print(output_folder.as_posix())
        webSite = WebSite(
            templateFolder= (self.cwd/"res"/"template").as_posix(),
            outFolder= output_folder.as_posix() + "/",
            defaultWebSiteFolder= (self.cwd/"res"/"assets").as_posix(),
            passFile= "None"
        )
        
        webSite.initWebSiteOutFolder()
        
        for report in self.reports:
            webSite.addReport(report)
    
        webSite.generateWebSite()
        print(output_folder / "index.html")
        webbrowser.open((output_folder / "index.html").as_posix())
