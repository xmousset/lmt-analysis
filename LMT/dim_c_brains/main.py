import os
import sys
import math
import webbrowser
from pathlib import Path
from abc import abstractmethod
from typing import Literal, List, Any

from IPython.display import clear_output

import sqlite3
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.colors import qualitative, sequential

lmt_analysis_path = Path(__file__).parent.parent
sys.path.append(lmt_analysis_path.as_posix())

from dim_c_brains.scripts.reports_manager import HTMLReportManager
from dim_c_brains.scripts.events import generic_events_list
from dim_c_brains.scripts.data_extractor import DataFrameCreator, LargeDataFrameCreator
from dim_c_brains.scripts.plotting import plt_curve_shaded
from dim_c_brains.scripts.ICM.mouse_characterization import ICM_event_analysis, ICM_movement_analysis

from lmtanalysis.Animal import Animal, AnimalPool
from lmtanalysis.Measure import oneDay, oneHour, oneMinute
from lmtanalysis.Event import EventTimeLine
from lmtanalysis.ParametersMouse import ParametersMouse

if __name__ == "__main__":
    data_path = Path.home() / "Syncnot" / "lmt-blocks" / "experiments" / "xmd" / "nadege" / "groupe1-cage1-LMT1.sqlite"
    connection = sqlite3.connect(data_path.as_posix())
    repo_manager = HTMLReportManager()
    
    # start_time = 12*oneHour
    # end_time = 13*oneHour

    df_creator = LargeDataFrameCreator(
        connection= connection,
        chunk_size= oneDay
    )
    
    ICM_event_analysis(repo_manager, df_creator)
    ICM_movement_analysis(repo_manager, df_creator)
    repo_manager.generate_local_output("test_nadege")