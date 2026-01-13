"""
Created on 08-01-2026
@author: Xavier MD
"""

import sys
import sqlite3
from pathlib import Path

lmt_analysis_path = Path(__file__).parent.parent
sys.path.append(lmt_analysis_path.as_posix())

from dim_c_brains.scripts.reports_manager import HTMLReportManager
from dim_c_brains.scripts.data_extractor import DataFrameConstructor
from dim_c_brains.scripts.plotting import plt_curve_shaded
from dim_c_brains.scripts.event import get_event_reports
from dim_c_brains.scripts.activity import get_activity_reports
from dim_c_brains.list_events import ICM_event_list

from lmtanalysis.Animal import Animal, AnimalPool
from lmtanalysis.Measure import oneDay, oneHour, oneMinute

if __name__ == "__main__":
    data_nadege = (
        Path.home()
        / "Syncnot"
        / "lmt-analysis"
        / "LMT"
        / "dim_c_brains"
        / "res"
        / "data"
        / "groupe1-cage1-LMT1.sqlite"
    )
    data_example = (
        Path.home()
        / "Syncnot"
        / "lmt-analysis"
        / "LMT"
        / "dim_c_brains"
        / "res"
        / "data"
        / "20180110_validation_4_ind_Experiment_6644_e.sqlite"
    )

    #   DATA CHOICE
    # data_path = data_nadege
    data_path = data_example

    # start_time = 12*oneHour
    # end_time = 13*oneHour

    connection = sqlite3.connect(data_path.as_posix())
    repo_manager = HTMLReportManager()
    df_creator = DataFrameConstructor(connection=connection)

    get_event_reports(repo_manager, df_creator)
    get_activity_reports(repo_manager, df_creator)

    output_folder = repo_manager.cwd / "test_analysis"
    repo_manager.generate_local_output(output_folder)
