import numpy as np
import pandas as pd
from pathlib import Path
from typing import Any, Dict, List

from sqlite3 import Connection
import plotly.express as px

from lmtanalysis.Measure import oneMinute, oneHour, oneDay
from lmtanalysis.Event import EventTimeLine
from lmtanalysis.Animal import Animal, AnimalPool
from lmtanalysis.Util import convert_to_d_h_m_s, d_h_m_s_toText


class DatetimeBinner:
    
    def __init__(
        self,
        framenumber : int,
        timestamp : int,
        frame_window : int
        ):
        """Initialize DatetimeBinner with a frame number and its
        corresponding timestamp (in ms), with a specified frame window.
        """
        if not isinstance(framenumber, (int, float)):
            raise ValueError("framenumber must be an integer or float.")
        if not isinstance(timestamp, (int, float)):
            raise ValueError("timestamp must be an integer or float.")
        
        self.timestamp_0 = timestamp - (framenumber / 30 * 1000)
        self.datetime_0 = self.frame_to_datetime(0)
        self.frame_bin_window = frame_window
        
        print(f"DatetimeBinner - FRAMENUMBER: {framenumber} "\
            f"- TIMESTAMP: {timestamp} - FRAME_WINDOW: {frame_window}")
        print(f"Experiment launch at {self.frame_to_datetime(1)}")
    
    def frame_to_datetime(self, framenumber: int):
        """Convert a frame number to a pandas Timestamp.
        """
        return pd.to_datetime(
            self.timestamp_0 + (framenumber / 30 * 1000),
            unit="ms"
        )
    
    def datetime_to_frame(self, dt: pd.Timestamp):
        """Convert a pandas Timestamp to a frame number.
        """
        return int((dt - self.datetime_0).total_seconds() * 30)
    
    def _set_bin_0(self):
        """Initialize the the binning time.
        """
        dt_0 = self.frame_to_datetime(self.frame_bin_window)
        dt_bin_0 = dt_0.floor(f"{self.frame_bin_window // oneMinute}min")
        self.bin_0_end_frame = self.datetime_to_frame(dt_bin_0)
    
    def get_frame_bins(self, start_frame: int, end_frame: int):
        """Get the frame number bins between start_frame and end_frame.
        """
        self._set_bin_0()
        
        frame_bins : List[int] = []
        f = self.bin_0_end_frame
        
        while f <= start_frame:
            f += self.frame_bin_window
        
        frame_bins.append(f)
        
        while f <= end_frame:
            f += self.frame_bin_window
            frame_bins.append(f)
        
        return frame_bins
    
    def get_datetime_bins(self, frame_bins: List[int]):
        """Get the corresponding datetime bins rounded to the nearest minute.
        """
        dt_bins = [self.frame_to_datetime(f).round("min") for f in frame_bins]
        return dt_bins


class DataFrameCreator:
    """A class to construct pandas DataFrames from AnimalPool for easy
    data manipulation and analysis.
    """
    
    def __init__(
        self,
        connection : Connection,
        time_window : int = 15*oneMinute
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
        self.animal_pool = AnimalPool()
        self.animal_pool.loadAnimals(connection)
        
        self.time_window = time_window
        
        self._init_binning()
        
        self.detection_loaded = False
    
    def _check_detection_loaded(self):
        """Check if detection data has been loaded.
        """
        if not self.detection_loaded:
            raise ValueError(
                "Detection data not loaded. "\
                "Must use load_detection_* before current action."
                )
    
    def load_detection_from_frames(
        self,
        start_frame : int|None = None,
        end_frame : int|None = None,
        ):
        """Define and load the detection time window from frame numbers.
        """
        
        if (end_frame is None
            or start_frame is None
            or end_frame - start_frame > oneDay
            ):
            print("[WARN] You probably try to load detection for more than "\
                "one day. Please, consider using LargeDataFrameCreator for "\
                "large time windows."
                )
        self.animal_pool.loadDetection(
            start= start_frame,
            end= end_frame,
            lightLoad= True
            )
        self._init_timestamp()
        self.detection_loaded = True
    
    def load_detection_from_time(
        self,
        start_time : pd.Timestamp|None = None,
        end_time : pd.Timestamp|None = None,
        ):
        """Define and load the detection time window from real time.
        """
        # TODO : convert start_time and end_time to frame number
        start_frame = None
        end_frame = None
        # TODO : load detection from time in AnimalPool
        # self.animal_pool.loadDetection(
        #     start= start_frame,
        #     end= end_frame,
        #     lightLoad= True
        #     )
        # self._init_timestamp()
        raise NotImplementedError("load_detection_from_time is not implemented yet.")
    
    def _init_timestamp(self):
        """Initialize loading detection data and prepare the time DataFrame.
        """
        
        if self.animal_pool.detectionStartFrame is None or \
           self.animal_pool.detectionEndFrame is None:
            raise ValueError(
                "AnimalPool detectionStartFrame or detectionEndFrame is None."
                )
        
        frames = self.binning.get_frame_bins(
            self.animal_pool.detectionStartFrame,
            self.animal_pool.detectionEndFrame
        )
        
        times = self.binning.get_datetime_bins(frames)
        
        self.time_df = pd.DataFrame({
            "FRAMENUMBER": frames,
            "TIME": times,
        })
    
    def _init_binning(self):
        """Initialize the DatetimeBinner object to compute the time bins.
        """
        
        query = "SELECT FRAMENUMBER, TIMESTAMP FROM FRAME ORDER BY FRAMENUMBER ASC LIMIT 1"

        cursor = self.animal_pool.conn.cursor()
        cursor.execute(query)
        result = cursor.fetchone()
        cursor.close()

        if not result:
            raise ValueError("No data found in FRAME table.")
        
        framenumber, timestamp = result
        
        self.binning = DatetimeBinner(framenumber, timestamp, self.time_window)
    
    def get_bins(self):
        """Get the list of frame numbers corresponding to the time bins ends.
        """
        self._check_detection_loaded()
        
        return self.time_df["FRAMENUMBER"].tolist()
    
    def count_event(self, animal : Animal, event : str):
        """Count occurrences of a specific event according to binning.
        
        Returns
        -------
        Tuple of two lists (counts, durations)
            counts : List[int]
                Number of occurrences of the event in each bin.
            durations : List[int]
                Total duration (in frames) of the event in each bin.
        """
        self._check_detection_loaded()
        
        event_timeline = EventTimeLine(
            conn= self.animal_pool.conn,
            eventName= event,
            idA= animal.baseId
            )
        
        counts : List[int] = []
        durations : List[int] = []
        frames = self.get_bins()
        
        for bin in range(len(frames)):
            f_min = frames[bin] - self.time_window + 1
            f_max = frames[bin]
            counts.append(event_timeline.getNumberOfEvent(f_min, f_max))
            durations.append(event_timeline.getTotalDurationEvent(f_min, f_max))
        
        return (counts, durations, frames)
    
    def get_df_events(self, events: str|list[str]):
        """Get a DataFrame containing event counts and durations for specified
        event or list of events.
        """
        self._check_detection_loaded()
        
        if isinstance(events, str):
            events = [events]
        
        results = []
        for animal in self.animal_pool.animalDictionary.values():
            for event in events:
                counts, durations, frames = self.count_event(animal, event)
                for i in range(len(frames)):
                    results.append({
                    "RFID": animal.RFID,
                    "ANIMALID": animal.baseId,
                    "EVENT": event,
                    "FRAMENUMBER": frames[i],
                    "EVENT_COUNT": counts[i],
                    "FRAME_COUNT": durations[i],
                    })
        
        df = pd.DataFrame(results)
        
        return pd.merge(df, self.time_df, on="FRAMENUMBER")
    
    def get_df_movement(
        self,
        filter_flickering: bool = False,
        filter_stop: bool = False,
        ):
        """Get a DataFrame containing movement data for all animals. Can apply
        filters to exclude flickering and stop from distance and speed
        calculation. (distance are in cm and speed are in cm/s)
        
        It include distance, speed, move time and stop time
        binned according to the time window.
        """
        frames = self.get_bins()
        results = []
        for animal in self.animal_pool.animalDictionary.values():
            dist_list = animal.getDistancePerBin(
                binFrameSize = self.time_window,
                minFrame = frames[0] - self.time_window + 1,
                maxFrame = frames[-1],
                filter_flickering = filter_flickering,
                filter_stop = filter_stop
                )
            speeds_list = animal.getSpeedPerBin(
                binFrameSize = self.time_window,
                minFrame = frames[0] - self.time_window + 1,
                maxFrame = frames[-1],
                filter_flickering = filter_flickering,
                filter_stop = filter_stop
            )
            counts, durations, _ = self.count_event(animal, "Stop")
            
            
            for i in range(len(dist_list)):
                results.append({
                    "RFID": animal.RFID,
                    "ANIMALID": animal.baseId,
                    "FRAMENUMBER": frames[i],
                    "DISTANCE": dist_list[i],
                    "SPEED_MEAN": speeds_list[i][0],
                    "SPEED_STD": speeds_list[i][1],
                    "SPEED_MIN": speeds_list[i][2],
                    "SPEED_MAX": speeds_list[i][3],
                    "SPEED_SUM": speeds_list[i][4],
                    
                    "STOP_COUNT": counts[i],
                    "STOP_DURATION": durations[i],
                    "MOVE_DURATION": self.time_window - durations[i],
                    })
        
        df = pd.DataFrame(results)
        
        return pd.merge(df, self.time_df, on="FRAMENUMBER")


class LargeDataFrameCreator(DataFrameCreator):
    """A class to construct pandas DataFrames from AnimalPool for large time
    windows (> oneDay), to reduce memory usage.
    """
    
    def __init__(
        self,
        connection : Connection,
        time_window : int = 15*oneMinute,
        chunk_size : int = oneDay
        ):
        """Initialize the LargeDataFrameConstructor. All datas will be binned
        according to the time window provided. The default is 15 minutes.
        
        Parameters
        ----------
        animal_pool : AnimalPool, optional
            An AnimalPool instance to extract data from,
            by default None.
        time_window : int, optional
            The time window (in frames) for binning data,
            by default 15 minutes.
        chunk_size : int, optional
            The size (in frames) of each data chunk to load into memory,
            by default 1 day.
        """
        super().__init__(connection, time_window)
        self.chunk_size = chunk_size
        self.bin_process_window = int(chunk_size/time_window)
        self._init_largetimestamp()
    
    def _init_largetimestamp(self):
        """Initialize loading detection data and prepare the time DataFrame,
        for large time windows.
        """
        
        query = "SELECT FRAMENUMBER FROM FRAME ORDER BY FRAMENUMBER DESC LIMIT 1"

        cursor = self.animal_pool.conn.cursor()
        cursor.execute(query)
        result = cursor.fetchone()
        cursor.close()

        if not result:
            raise ValueError("No data found in FRAME table.")
        
        frames = self.binning.get_frame_bins(1, result[0])
        
        times = self.binning.get_datetime_bins(frames)
        
        self.time_largedf = pd.DataFrame({
            "FRAMENUMBER": frames,
            "TIME": times,
        })
    
    def get_largebins(self):
        """Get the list of frame numbers corresponding to the time bins ends
        for large time windows.
        """
        return self.time_largedf["FRAMENUMBER"].tolist()
    
    def get_largedf_events(self, events: str|list[str]):
        """Get a DataFrame containing event counts and durations for specified
        event or list of events, handling large time windows.
        """
        bins = self.get_largebins()
        large_df = None
        
        for i in range(len(bins) // self.bin_process_window):
            
            start_bin = i * self.bin_process_window
            end_bin = (i+1) * self.bin_process_window - 1
            
            start_frame = bins[start_bin] - self.time_window + 1
            if end_bin >= len(bins):
                end_frame = bins[-1]
            else:
                end_frame = bins[end_bin]
            
            self.load_detection_from_frames(
                start_frame= start_frame,
                end_frame= end_frame
                )
            
            chunk_df = self.get_df_events(events)
            
            if large_df is None:
                large_df = chunk_df
            else:
                large_df = pd.concat([large_df, chunk_df], ignore_index= True)
        
        if large_df is None:
            raise ValueError("Unable to create a dataframe.")
        
        return large_df
    
    def get_largedf_movement(
        self,
        filter_flickering: bool = False,
        filter_stop: bool = False,
        ):
        """Get a DataFrame containing movement data for all animals. Can apply
        filters to exclude flickering and stop from distance and speed
        calculation, handling large time windows.
        
        It include distance, speed, move time and stop time
        binned according to the time window.
        """
        bins = self.get_largebins()
        # TODO : create an empty dataframe and ensure that concat will function accordingly
        large_df = None

        for i in range(len(bins) // self.bin_process_window):
            
            start_bin = i * self.bin_process_window
            end_bin = (i+1) * self.bin_process_window - 1
            
            start_frame = bins[start_bin] - self.time_window
            if end_bin >= len(bins):
                end_frame = bins[-1]
            else:
                end_frame = bins[end_bin]
            
            self.load_detection_from_frames(start_frame, end_frame)

            chunk_df = self.get_df_movement(filter_flickering, filter_stop)

            if large_df is None:
                large_df = chunk_df
            else:
                large_df = pd.concat([large_df, chunk_df], ignore_index=True)

        if large_df is None:
            raise ValueError("Unable to create a dataframe.")
        
        return large_df
        