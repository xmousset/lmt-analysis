"""
@author: Xavier MD
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
    print(example_data)
    connection = sqlite3.connect(str(example_data))

    bin_size = oneMinute * 5
    df_creator = DataFrameConstructor(connection, time_window=bin_size)
    repo_manager = HTMLReportManager()

    generate_activity_reports(repo_manager, df_creator)
    generate_event_reports(repo_manager, df_creator)

    output_folder = select_folder()
    repo_manager.generate_local_output(output_folder)


def ICM_analysis():
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

    connection = sqlite3.connect(str(data_path))
    df_creator = DataFrameConstructor(connection)
    repo_manager = HTMLReportManager()

    generate_event_reports(repo_manager, df_creator)
    generate_activity_reports(repo_manager, df_creator)

    output_folder = repo_manager.cwd / "ICM_analysis"
    repo_manager.generate_local_output(output_folder)


def main():
    data_file = select_sqlite_file()

    connection = sqlite3.connect(str(data_file))
    df_creator = DataFrameConstructor(connection)
    repo_manager = HTMLReportManager()

    generate_event_reports(repo_manager, df_creator)
    generate_activity_reports(repo_manager, df_creator)

    output_folder = select_folder()
    if output_folder is not None:
        repo_manager.generate_local_output(output_folder)
        print(f"Save analysis at\n{output_folder}")
    else:
        output_folder = repo_manager.cwd / "analysis"
        print(f"Save analysis to default folder\n{output_folder}")


def test_sensors():
    sensors_path = Path.home() / "Downloads" / "test_sensors.sqlite"
    print(sensors_path)
    connection = sqlite3.connect(str(sensors_path))

    df_creator = DataFrameConstructor(connection)
    repo_manager = HTMLReportManager()
    generate_sensors_reports(repo_manager, df_creator)

    output_folder = select_folder()
    if output_folder is not None:
        repo_manager.generate_local_output(output_folder)
        print(f"Save analysis at\n{output_folder}")
    else:
        output_folder = repo_manager.cwd / "analysis"
        print(f"Save analysis to default folder\n{output_folder}")


if __name__ == "__main__":
    # main()
    # ICM_analysis()
    # test_generic_analysis()
    test_sensors()
