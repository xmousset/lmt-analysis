"""
@author: xmousset
"""

import sys
import sqlite3
from pathlib import Path
from typing import Any

import pandas as pd

lmt_analysis_path = Path(__file__).parent.parent
sys.path.append(lmt_analysis_path.as_posix())

from dim_c_brains.scripts.reports_manager import HTMLReportManager
from dim_c_brains.scripts.data_extractor import DataFrameConstructor
from dim_c_brains.scripts.event_reports import generate_event_reports
from dim_c_brains.scripts.sensors_reports import generate_sensors_reports
from dim_c_brains.scripts.activity_reports import generate_activity_reports
from dim_c_brains.scripts.overview_reports import generate_overview_reports
from dim_c_brains.scripts.tkinter_tools import (
    select_sqlite_file,
    select_folder,
)
from dim_c_brains.scripts.events_and_modules import events_to_modules
from dim_c_brains.teams.teams_events_choice import ICM_events_list

from lmtanalysis.Measure import oneMinute, oneDay


def main(
    start: int | str | None = None,
    end: int | str | None = None,
    **kwargs: Any,
):
    """
    Runs the main analysis workflow for LMT data, generating HTML reports and saving them to the selected output folder.

    Parameters
    ----------
    start : int or str or None, optional
        Start of the analysis period. Can be an integer frame number or a
        timestamp string. Defaults to None. (e.g., "2026-01-01 00:00:00")
    end : int or str or None, optional
        End of the analysis period. Can be an integer frame number or a
        timestamp string. Defaults to None. (e.g., "2026-01-01 00:00:00")

    Other Parameters
    ----------------
    file_path : Path, optional
        Path to the SQLite data file. If not provided, prompts user to select
        file.
    time_window : int, optional
        Time window in seconds for binning data. Defaults to 15 minutes.
    processing_limit : int, optional
        Maximum processing duration in seconds. Defaults to one day.
    night_begin : int, optional
        Hour when the night begins. Defaults to 20.
    night_duration : int, optional
        Duration of the night in hours. Defaults to 12.
    filter_flickering : bool, optional
        Whether to filter flickering activity. Defaults to False.
    filter_stop : bool, optional
        Whether to filter stop activity. Defaults to False.
    event_list : list of str, optional
        List of event names to analyze. If None, no event analysis is
        performed. Defaults to None.
    output_folder : Path or None, optional
        Folder to save the output reports. If None, prompts user to select
        folder. Defaults to None.
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
    param["output_folder"] = kwargs.get("output_folder", None)

    repo_manager = HTMLReportManager()

    connection = sqlite3.connect(str(param["file_path"]))
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

    df_activity = generate_activity_reports(
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
                    generate_event_reports(
                        repo_manager,
                        df_constructor,
                        event_name=event,
                        **param,
                    ),
                ]
            )

    df_sensors = generate_sensors_reports(
        repo_manager, df_constructor, **param
    )

    df_mice = generate_overview_reports(
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


def get_ICM_param():
    data_path = (
        Path.home()
        / "Syncnot"
        / "lmt-analysis"
        / "LMT"
        / "dim_c_brains"
        / "res"
        / "data"
        / "groupe1-cage1-LMT1.sqlite"
    )

    icm_param = {
        "file_path": data_path,
        "time_window": 15 * oneMinute,
        "processing_limit": oneDay,
        "night_begin": 20,
        "night_duration": 12,
        "filter_flickering": True,
        "filter_stop": True,
        "event_list": ["Oral-oral Contact"],
        "output_folder": Path.home() / "Desktop" / "ICM_analysis",
    }
    return icm_param


def get_test_param():
    example_path = Path(__file__).parent / "examples"
    dataset = (
        example_path / "20180110_validation_4_ind_Experiment_6644_e.sqlite"
    )

    test_param = {
        "file_path": dataset,
        "time_window": 3 * oneMinute,
        "processing_limit": oneDay,
        "night_begin": 20,
        "night_duration": 12,
        "filter_flickering": False,
        "filter_stop": False,
        "event_list": [
            "Oral-oral Contact",
            "Move isolated",
        ],
        "output_folder": Path.home() / "Desktop" / "test_analysis",
    }

    return test_param


if __name__ == "__main__":

    # PARAM = get_ICM_param()
    PARAM = get_test_param()

    main(**PARAM)
