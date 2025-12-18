import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, List

import plotly.express as px

from lmtanalysis.Measure import oneMinute
from lmtanalysis.Event import EventTimeLine
from lmtanalysis.Animal import Animal, AnimalPool
from lmtanalysis.Util import convert_to_d_h_m_s, d_h_m_s_toText


class DataFrameManager:
    """A class to construct pandas DataFrames from AnimalPool for easy
    data manipulation and analysis.
    """
    def __init__(
        self,
        animal_pool: AnimalPool|None = None,
        time_window: int = 15*oneMinute
        ):
        """Initialize the DataFrameConstructor. All datas will be binned
        according to the time window provided. The default is 15 minutes.
        
        Parameters
        ----------
        animal_pool : AnimalPool, optional
            An AnimalPool instance to extract data from,
            by default None.
        time_window : int, optional
            The time window (in frames) for binning data,
            by default 15 minutes.
        """
        self.df : pd.DataFrame|None = None
        self.animal_pool = animal_pool
        self.time_window = time_window
        self.ref_datetime : pd.Timestamp|None = None
        self.time : List[int]|None = None
        if self.animal_pool is not None:
            self.time = self.animal_pool.detectionStartFrame
    
    def _get_time_ref(self):
        """Find round datetime (like 12h00) to compute the time bins.
        """
        if self.animal_pool is None:
            raise ValueError("AnimalPool is not set.")
        
        query = "select MIN(FRAMENUMBER), FROM FRAME"

        cursor = self.animal_pool.conn.cursor()
        cursor.execute("SELECT FRAMENUMBER, TIMESTAMP FROM FRAME ORDER BY FRAMENUMBER ASC LIMIT 1")
        result = cursor.fetchone()
        cursor.close()

        if not result:
            raise ValueError("No data found in FRAME table.")
        
        framenumber, timestamp = result
        print(f"FRAMENUMBER: {framenumber}, TIMESTAMP: {timestamp}")
        frame_0_timestamp : int = timestamp - (framenumber / 30 * 1000)
        
        self.ref_datetime = pd.to_datetime(frame_0_timestamp, unit='ms')
        
        self.ref_bin = self.ref_datetime.floor(f"{self.time_window // oneMinute}min")
    
    def get_time_bins(self, start: int, end: int) -> pd.DataFrame:
        """Get time bins between start and end frames.
        
        Parameters
        ----------
        start : int
            Start frame number.
        end : int
            End frame number.
        
        Returns
        -------
        pd.DataFrame
            A DataFrame with time bins and corresponding timestamps.
        """
        if self.ref_datetime is None:
            self._get_time_ref()
        
        bins = list(range(start, end + self.time_window, self.time_window))
        bin_labels = []
        for b in bins[:-1]:
            delta = pd.to_timedelta(b / 30, unit='s')
            bin_time = self.ref_datetime + delta
            bin_labels.append(bin_time)
        
        time_bins_df = pd.DataFrame({
            "bin_start": bins[:-1],
            "bin_end": bins[1:],
            "timestamp": bin_labels
        })
        return time_bins_df
    
    def reset(self):
        """Reset the constructor.
        """
        self.df = None
        self.time_window = 15*oneMinute
        print("DataFrameConstructor reset, 'time_window' set to 15 minutes.")
    
    def plot_df(self):
        """Plot the constructed DataFrame using plotly.
        """
        if self.df is None:
            raise ValueError("DataFrame is not constructed yet.")
        
        if "value" in self.df.columns:
            y_name = "value"
        elif "count" in self.df.columns:
            y_name = "count"
        else:
            raise ValueError("DataFrame not plotable.")
        
        fig = px.line(
            self.df,
            x="time", y=y_name, color="animal_id",
            title=f"{y_name} over time"
        )
        fig.show()
    
    def get_events(self, animal_pool: AnimalPool, events: list[str]) -> pd.DataFrame:
        results = []
        for animal in animal_pool.animalDictionary.values():
            for evnt in events:
                evnt_TL = EventTimeLine(
                    conn= animal_pool.conn,
                    eventName= evnt,
                    idA= animal.baseId
                )
                results.append({
                    "animal_id": animal.baseId,
                    "event": evnt,
                    "count": len(evnt_TL.getDictionary())
                })
        self.df = pd.DataFrame(results)
        return self.df