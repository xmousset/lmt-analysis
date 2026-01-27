"""
@author: xmousset
"""

import sqlite3
from typing import Any

import pandas as pd

from dim_c_brains.scripts.reports_manager import HTMLReportManager
from dim_c_brains.scripts.data_extractor import DataFrameConstructor
from dim_c_brains.scripts.rebuild_events import ReBuildEvents
from dim_c_brains.reports import (
    event_reports,
    sensors_reports,
    activity_reports,
    overview_reports,
)
from dim_c_brains.scripts.tkinter_tools import (
    select_sqlite_file,
    select_folder,
)

from lmtanalysis.Measure import oneMinute, oneDay


def main(
    rebuild_events: bool = False,
    start: int | str | None = None,
    end: int | str | None = None,
    **kwargs: Any,
):
    """
    Runs the main analysis workflow for LMT data, generating HTML reports and
    saving them to the selected output folder.
    *(timestamp string example: "2026-01-01 00:00:00")*

    Parameters
    ----------
    start : int or str or None, optional
        Start of the analysis period. Can be an integer frame number or a
        timestamp string. Defaults to None.
    end : int or str or None, optional
        End of the analysis period. Can be an integer frame number or a
        timestamp string. Defaults to None.

    Other Parameters
    ----------------
    file_path : Path, optional
        Path to the SQLite data file. If not provided, prompts user to select
        file.
    time_window : int, optional
        Time window in seconds for binning data. Defaults to 15 *min*
        (27 000 *frames*).
    processing_limit : int, optional
        Maximum processing duration in seconds. Defaults to 1 *day* (2 592 000
        *frames*).
    night_begin : int, optional
        Hour when the night begins. Defaults to 20 (8 *p.m.*).
    night_duration : int, optional
        Duration of the night in hours. Defaults to 12 (8 *p.m.* to 8 *a.m.*).
    filter_flickering : bool, optional
        Whether to filter flickering activity. Defaults to False.
    filter_stop : bool, optional
        Whether to filter stop activity. Defaults to False.
    event_list : list of str, optional
        List of event names to analyze. By default, no event analysis is
        performed (None).
    overview_event_list : list of str, optional
        List of event names for overview reports. By default, no overview event
        analysis is performed (None).
    output_folder : Path or None, optional
        Folder to save the output reports. By default, prompts user to select
        folder (None).
    """

    param = {}
    param["file_path"] = kwargs.get("file_path", None)
    if param["file_path"] is None:
        param["file_path"] = select_sqlite_file()
    param["time_window"] = kwargs.get("time_window", 15 * oneMinute)
    param["processing_limit"] = kwargs.get("processing_limit", oneDay)
    param["night_begin"] = kwargs.get("night_begin", 20)
    param["night_duration"] = kwargs.get("night_duration", 12)
    param["filter_flickering"] = kwargs.get("filter_flickering", False)
    param["filter_stop"] = kwargs.get("filter_stop", False)
    param["event_list"] = kwargs.get("event_list", None)
    param["overview_event_list"] = kwargs.get("overview_event_list", None)
    param["output_folder"] = kwargs.get("output_folder", None)

    repo_manager = HTMLReportManager()

    connection = sqlite3.connect(str(param["file_path"]))

    if rebuild_events:
        if param["event_list"] is None:
            raise ValueError("event_list must be provided to rebuild events.")
        rebuilder = ReBuildEvents(
            connection, str(param["file_path"]), param["event_list"]
        )
        rebuilder.set_events_to_rebuild("missing")
        rebuilder.rebuild()

    df_constructor = DataFrameConstructor(
        connection,
        bin_window=param["time_window"],
        processing_window=param["processing_limit"],
    )

    if type(start) != type(end) and start is not None and end is not None:
        raise ValueError(
            f"start_analysis ({type(start)}) and "
            f"end_analysis ({type(end)}) must be of the same type"
        )

    if isinstance(start, (int, type(None))) and isinstance(
        end, (int, type(None))
    ):
        df_constructor.set_analysis_limits(
            start=start,
            end=end,
        )

    if isinstance(start, (str, type(None))) and isinstance(
        end, (str, type(None))
    ):
        t_start = None if start is None else pd.Timestamp(start)
        t_end = None if end is None else pd.Timestamp(end)
        df_constructor.set_analysis_limits(start=t_start, end=t_end)

    df_activity = activity_reports.generic(
        repo_manager, df_constructor, **param
    )

    if param["event_list"] is None:
        df_events = None
    else:
        df_events = pd.DataFrame()
        for event in param["event_list"]:
            df_events = pd.concat(
                [
                    df_events,
                    event_reports.generic(
                        repo_manager,
                        df_constructor,
                        event_name=event,
                        **param,
                    ),
                ]
            )

    df_sensors = sensors_reports.generic(repo_manager, df_constructor, **param)

    df_mice = overview_reports.generic(
        repo_manager,
        df_constructor,
        df_activity=df_activity,
        df_events=df_events,
        df_sensors=df_sensors,
        **param,
    )

    if param["output_folder"] is None:
        output_folder = select_folder()
    else:
        output_folder = param["output_folder"]

    if output_folder:
        repo_manager.generate_local_output(output_folder)
        print(f"Save analysis at\n{output_folder}")
    else:
        output_folder = repo_manager.cwd / (
            "analysis" + param["file_path"].stem
        )
        print(f"Save analysis to default folder\n{output_folder}")
