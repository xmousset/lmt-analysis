"""
@author: xmousset
"""

import sys
import sqlite3
from pathlib import Path

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
from dim_c_brains.list_events import ICM_event_list

from lmtanalysis.Measure import oneMinute, oneDay


def test_generic_analysis():
    example_path = Path(__file__).parent / "examples"
    example_data = (
        example_path / "20180110_validation_4_ind_Experiment_6644_e.sqlite"
    )
    connection = sqlite3.connect(str(example_data))

    bin_size = oneMinute * 5
    df_creator = DataFrameConstructor(connection, time_window=bin_size)
    repo_manager = HTMLReportManager()

    dic_df = {}
    dic_df["df_activity"] = generate_activity_reports(repo_manager, df_creator)
    dic_df["df_events"] = generate_event_reports(
        repo_manager, df_creator, "Oral-oral Contact"
    )
    dic_df["df_sensors"] = generate_sensors_reports(repo_manager, df_creator)
    generate_overview_reports(repo_manager, df_creator, example_data, **dic_df)

    # output_folder = select_folder()
    output_folder = Path.home() / "Desktop" / "test"
    repo_manager.generate_local_output(output_folder)


def ICM_analysis(data_path: Path):

    ICM_BINNING = {
        "time_window": 15 * oneMinute,
        "processing_limit": oneDay,
    }
    ICM_NIGHT = {
        "night_begin": 20,
        "night_duration": 12,
    }
    ICM_FILTERS = {
        "filter_flickering": True,
        "filter_stop": True,
    }

    events = ["Oral-oral Contact"]

    connection = sqlite3.connect(str(data_path))
    df_creator = DataFrameConstructor(connection, **ICM_BINNING)
    repo_manager = HTMLReportManager()

    generate_activity_reports(
        repo_manager, df_creator, **ICM_NIGHT, **ICM_FILTERS
    )

    for event in events:
        generate_event_reports(
            repo_manager, df_creator, event_name=event, **ICM_NIGHT
        )

    generate_sensors_reports(repo_manager, df_creator, **ICM_NIGHT)

    output_folder = repo_manager.cwd / "ICM_analysis"
    repo_manager.generate_local_output(output_folder)


def main():
    data_file = select_sqlite_file()

    connection = sqlite3.connect(str(data_file))
    df_creator = DataFrameConstructor(connection)
    repo_manager = HTMLReportManager()

    generate_event_reports(repo_manager, df_creator, "Oral-oral Contact")
    generate_activity_reports(repo_manager, df_creator)

    output_folder = select_folder()
    if output_folder is not None:
        repo_manager.generate_local_output(output_folder)
        print(f"Save analysis at\n{output_folder}")
    else:
        output_folder = repo_manager.cwd / "analysis"
        print(f"Save analysis to default folder\n{output_folder}")


def test_sensors():
    data_file = select_sqlite_file()
    connection = sqlite3.connect(str(data_file))

    df_creator = DataFrameConstructor(connection)
    repo_manager = HTMLReportManager()

    df_sensors = generate_sensors_reports(repo_manager, df_creator)
    generate_overview_reports(
        repo_manager, df_creator, data_file, df_sensors=df_sensors
    )

    output_folder = select_folder()
    if output_folder is not None:
        repo_manager.generate_local_output(output_folder)
        print(f"Save analysis at\n{output_folder}")
    else:
        output_folder = repo_manager.cwd / "analysis"
        print(f"Save analysis to default folder\n{output_folder}")


if __name__ == "__main__":
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
    # ICM_analysis(data_path)

    # main()
    test_generic_analysis()
    # test_sensors()
