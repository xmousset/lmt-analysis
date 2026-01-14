"""
@author: Xavier MD
"""

import numpy as np
import pandas as pd
from pathlib import Path
from typing import Any, Dict, List, Literal

from sqlite3 import Connection
import plotly.express as px

from lmtanalysis.Measure import oneMinute, oneHour, oneDay
from lmtanalysis.Event import EventTimeLine
from lmtanalysis.Animal import Animal, AnimalPool
from lmtanalysis.Util import convert_to_d_h_m_s, d_h_m_s_toText


class DataProcessingBinner:
    """
    Utility class design to manage the binning with frame numbers.

    It manages :
    - the conversion between frame numbers and datetime
    - the bins for plotting datas
    - the chuns for processing datas (chunk size)
    """

    def __init__(
        self,
        last_frame: int,
        last_timestamp: int,
        bin_size: int,
        chunk_size: int,
        start_frame: int | None = None,
        end_frame: int | None = None,
    ):
        """
        Initialize DatetimeBinner with last FRAMENUMBER and TIMESTAMP of a
        SQLite database produce by LMT experiment.
        Bins size is for the data that will be ploted.
        Chunk size is for data processing when using a large database. It will
        not appear in the data outputs but will be used to load data in chunks.

        Args:
            last_frame (int): last FRAMENUMBER value in LMT FRAME table.
            last_timestamp (int): TIMESTAMP value of 'last_frame' (in ms).
            bin_size (int): binning value (in frames), must be at least\
                one minute.
            chunk_size (int, optional): binning value (in frames) for\
                processing data in chunks, must be at least one hour.
        """
        self.last_frame = last_frame
        self.bin_0: Dict[str, Any] = {
            "FRAMENUMBER": 0,
            "TIMESTAMP": last_timestamp - (last_frame / 30 * 1000),
            "DATETIME": None,
        }
        self.bin_0["DATETIME"] = self.frame_to_time(0)

        self.set_parameters(bin_size, chunk_size, start_frame, end_frame)

        print(f"DatetimeBinner")
        print(f"last FRAMENUMBER: {last_frame}")
        print(f"last TIMESTAMP: {last_timestamp}")
        print(f"BIN size: {bin_size}")
        print(f"CHUNK size: {chunk_size}")
        print(f"Experiment started at {self.frame_to_time(1)}")

    def frame_to_time(self, framenumber: int) -> pd.Timestamp:
        """Convert a frame number to a pandas Timestamp."""
        timestamp = self.bin_0["TIMESTAMP"] + (framenumber / 30 * 1000)
        return pd.to_datetime(timestamp, unit="ms")

    def time_to_frame(self, pd_datetime: pd.Timestamp) -> int:
        """Convert a pandas Timestamp to a frame number."""
        return round(
            (pd_datetime - self.bin_0["DATETIME"]).total_seconds() * 30
        )

    def set_parameters(
        self,
        bin_size: int | None = None,
        chunk_size: int | None = None,
        start_frame: int | None = None,
        end_frame: int | None = None,
    ):
        """Set bin size, chunk size, and frame limits (all in frames)."""

        if bin_size is not None:
            if bin_size <= oneMinute:
                raise ValueError("Bin size must be at least one minute.")
            self.bin_size = bin_size
        else:
            if self.bin_size is None:
                raise ValueError("Bin size must be specified.")

        if chunk_size is not None:
            if chunk_size <= oneHour:
                raise ValueError("Chunk size must be at least one hour.")

            if chunk_size < self.bin_size:
                raise ValueError(
                    "Chunk size must be at least equal to bin size."
                )
            self.chunk_size = chunk_size
        else:
            if self.chunk_size is None:
                raise ValueError("Chunk size must be specified.")

        if start_frame is None or start_frame < 1:
            self.start_frame = 1
        else:
            self.start_frame = start_frame

        if end_frame is None or end_frame > self.last_frame:
            self.end_frame = self.last_frame
        else:
            self.end_frame = end_frame

        if self.start_frame >= self.end_frame:
            raise ValueError("You have not : start_frame < end_frame.")

        if self.start_frame > self.last_frame:
            raise ValueError("start_frame out of range.")

        if self.end_frame < 1:
            raise ValueError("end_frame out of range.")

        self.calculate_bin_df()
        self.calculate_chunk_df()

    def calculate_bin_df(self):
        """Calculate the bin dataframe with START_FRAME, END_FRAME, START_TIME,
        and END_TIME as columns."""

        # get the first bin starting frame number
        # it is a negative value because bins start at round hours
        dt_0 = self.frame_to_time(self.bin_size)
        dt_bin_0 = dt_0.floor(f"{self.bin_size // oneMinute}min")
        start_frame_bin_1 = self.time_to_frame(dt_bin_0)

        # calculate starting frame of each bins until last frame
        bin_start_frames: List[int] = []
        f = start_frame_bin_1 - self.bin_size
        while f < self.last_frame:
            bin_start_frames.append(f)
            f += self.bin_size

        # create the dataframe with all bin information
        list_df = []
        for f in bin_start_frames:
            start_frame = f if f > 0 else 1
            end_frame = (
                f + self.bin_size - 1
                if f <= self.last_frame
                else self.last_frame
            )
            list_df.append(
                {
                    "START_FRAME": start_frame,
                    "END_FRAME": end_frame,
                    "START_TIME": self.frame_to_time(f),
                    "END_TIME": self.frame_to_time(f + self.bin_size - 1),
                }
            )

        self.bin_df = pd.DataFrame(list_df)
        return self.bin_df

    def calculate_chunk_df(self):
        """Calculate the chunk dataframe with START_FRAME, END_FRAME,
        START_TIME, and END_TIME as columns between frames limits.
        """

        list_df = []

        # manage 1 bin case
        if len(self.bin_df) == 1:
            list_df.append(
                {
                    "START_FRAME": self.bin_df["START_FRAME"].loc[0],
                    "END_FRAME": self.bin_df["END_FRAME"].loc[0],
                    "START_TIME": self.bin_df["START_TIME"].loc[0],
                    "END_TIME": self.bin_df["END_TIME"].loc[0],
                }
            )
            self.chunk_df = pd.DataFrame(list_df)
            return self.chunk_df

        list_df.append(
            {
                "START_FRAME": self.bin_df["START_FRAME"].loc[0],
                "END_FRAME": None,
                "START_TIME": self.bin_df["START_TIME"].loc[0],
                "END_TIME": None,
            }
        )

        # define first chunk limit
        chunk_lim: Any = self.start_frame - 1
        if self.start_frame < self.bin_df["END_FRAME"].loc[0]:
            chunk_lim = self.chunk_size

        # calculate each chunks
        for idx in range(1, len(self.bin_df)):
            row = self.bin_df.loc[idx]

            if row["END_FRAME"] > chunk_lim:
                list_df[-1]["END_FRAME"] = self.bin_df["END_FRAME"].loc[
                    idx - 1
                ]
                list_df[-1]["END_TIME"] = self.bin_df["END_TIME"].loc[idx - 1]
                list_df.append(
                    {
                        "START_FRAME": row["START_FRAME"],
                        "END_FRAME": None,
                        "START_TIME": row["START_TIME"],
                        "END_TIME": None,
                    }
                )
                chunk_lim = list_df[-1]["START_FRAME"] + self.chunk_size - 1

        if list_df[-1]["END_FRAME"] is None:
            list_df[-1]["END_FRAME"] = self.bin_df["END_FRAME"].max()
        if list_df[-1]["END_TIME"] is None:
            list_df[-1]["END_TIME"] = self.bin_df["END_TIME"].max()

        self.chunk_df = pd.DataFrame(list_df)
        return self.chunk_df

    def get_bin_list(
        self,
        bin_edge: Literal["START", "END"],
        unit: Literal["FRAME", "TIME"] = "FRAME",
    ):
        """
        Get a list of bin edges (frame numbers or timestamps) between
        start_frame and end_frame.

        Parameters
        ----------
        bin_edge : {'START', 'END'}
            Whether to return the start or end of each bin.
        unit : {'FRAME', 'TIME'}, optional
            Whether to return frame numbers ('FRAME') or timestamps ('TIME').
            Default is 'FRAME'.

        Returns
        -------
        list of int or list of pandas.Timestamp
            List of bin edges (either frame numbers or timestamps) within the
            specified range.

        Examples
        --------
        Suppose self.bin_df contains:

        >>> # START_FRAME  END_FRAME  START_TIME           END_TIME
        >>> # 1            12_999      2026-01-01 00:00:00  2026-01-01 00:14:59
        >>> # 13_000       39_999      2026-01-01 00:15:00  2026-01-01 00:29:59
        >>> # 40_000       56_999      2026-01-01 00:30:00  2026-01-01 00:44:59

        The following code would yield:
        >>> # if start_frame is None and end_frame is None :
        >>> DatetimeBinner.get_bin_list('END')
        [12_999, 39_999, 56_999, ...]

        >>> # if start_frame is 5_000 and end_frame is 25_000 :
        >>> DatetimeBinner.get_bin_list('START', unit='TIME')
        [Timestamp('2026-01-01 00:00:00'), Timestamp('2026-01-01 00:15:00')]
        """

        mask = (self.bin_df["END_FRAME"] >= self.start_frame) & (
            self.bin_df["START_FRAME"] <= self.end_frame
        )

        return self.bin_df[f"{bin_edge}_{unit}"].loc[mask].tolist()

    def get_chunk_list(
        self,
        chunk_edge: Literal["START", "END"],
        unit: Literal["FRAME", "TIME"] = "FRAME",
    ):
        """
        Get a list of chunk edges (frame numbers or timestamps) between
        start_frame and end_frame. Works similarly to `get_bin_list`.

        Parameters
        ----------
        chunk_edge : {'START', 'END'}
            Whether to return the start or end of each chunk.
        unit : {'FRAME', 'TIME'}, optional
            Whether to return frame numbers ('FRAME') or timestamps ('TIME').
            Default is 'FRAME'.

        Returns
        -------
        list of int or list of pandas.Timestamp
            List of chunk edges (either frame numbers or timestamps) within
            the specified range.
        """

        mask = (self.chunk_df["END_FRAME"] >= self.start_frame) & (
            self.chunk_df["START_FRAME"] <= self.end_frame
        )

        return self.chunk_df[f"{chunk_edge}_{unit}"].loc[mask].tolist()

    def exceeds_process_limit(self) -> bool:
        """Check if the processing window exceeds the chunk size."""
        process_window = self.end_frame - self.start_frame
        return process_window > self.chunk_size

    def get_process_iterator(self):

        frames_start = self.get_chunk_list("START")
        frames_end = self.get_chunk_list("END")

        if frames_start[0] < self.start_frame:
            frames_start[0] = self.start_frame

        if frames_end[-1] > self.end_frame:
            frames_end[-1] = self.end_frame

        chunk_iterator: List[tuple[int, int]] = []
        for start, end in zip(frames_start, frames_end):
            chunk_iterator.append((start, end))

        return chunk_iterator


class DataFrameConstructor:
    """A class to construct pandas DataFrames from AnimalPool easy
    data manipulation and analysis. It is designed to handle large time
    windows (> oneDay), by processing data in chunks to reduce memory usage. By
    default, chunk size is set to one day.
    """

    def __init__(
        self,
        connection: Connection,
        time_window: int = 15 * oneMinute,
        processing_limit: int = oneDay,
        start_frame: int | None = None,
        end_frame: int | None = None,
    ):
        """
        instanciate pandas dataframes constructor. All datas will be binned
        according to the time window provided (15 minutes by default) and will
        be processed in chunks of specified size (1 day by default).

        Args:
            connection (Connection): SQLite database connection.
            time_window (int, optional): The time window (in frames) for\
                binning data. Defaults to 15 minutes.
            processing_limit (int, optional): The size (in frames) of each\
            data chunk to load into memory. Defaults to 1 day.
        """
        self.animal_pool = AnimalPool()
        self.animal_pool.loadAnimals(connection)

        self._init_binner(time_window, processing_limit)
        self.set_frame_limits(start_frame, end_frame)

    def _init_binner(self, time_window: int, processing_limit: int):
        """Initialize the DatetimeBinner object to compute the time bins."""
        query = "SELECT FRAMENUMBER, TIMESTAMP FROM FRAME ORDER BY FRAMENUMBER DESC LIMIT 1"
        cursor = self.animal_pool.conn.cursor()
        cursor.execute(query)
        result = cursor.fetchone()
        cursor.close()

        if not result:
            raise ValueError("No data found in FRAME table.")

        lastframe, timestamp = result
        self.binner = DataProcessingBinner(
            lastframe, timestamp, time_window, processing_limit
        )

    def set_time_window(self, time_window: int):
        """Set the time window for data binning."""
        self.binner.set_parameters(bin_size=time_window)

    def get_time_window(self) -> int:
        """Get the current time window for data binning."""
        return self.binner.bin_size

    def set_processing_limits(self, processing_limit: int):
        """Set the processing limit for data chunking."""
        self.binner.set_parameters(chunk_size=processing_limit)

    def get_processing_limits(self) -> int:
        """Get the current processing limit for data chunking."""
        return self.binner.chunk_size

    def set_frame_limits(
        self,
        start_frame: int | None = None,
        end_frame: int | None = None,
    ):
        """Set the frame limits for data processing."""
        self.binner.set_parameters(
            start_frame=start_frame, end_frame=end_frame
        )

    def get_frame_limits(self) -> tuple[int, int]:
        """Get the current frame limits for data processing."""
        return (self.binner.start_frame, self.binner.end_frame)

    def count_event(
        self,
        animal: Animal,
        event: str,
    ):
        """Count occurrences of a specific event according to binning.

        Returns
        -------
        Tuple of two lists (counts, durations)
            counts : List[int]
                Number of occurrences of the event in each bin.
            durations : List[int]
                Total duration (in frames) of the event in each bin.
        """
        event_timeline = EventTimeLine(
            conn=self.animal_pool.conn, eventName=event, idA=animal.baseId
        )

        counts: List[int] = []
        durations: List[int] = []
        bins_start = self.binner.get_bin_list("START")
        bins_end = self.binner.get_bin_list("END")

        for f_min, f_max in zip(bins_start, bins_end):
            counts.append(event_timeline.getNumberOfEvent(f_min, f_max))
            durations.append(
                event_timeline.getTotalDurationEvent(f_min, f_max)
            )

        return (counts, durations)

    def get_df_event(self, event: str):
        """Get a DataFrame containing event counts and durations for specified
        event.
        """
        start_frames = self.binner.get_bin_list("START")
        end_frames = self.binner.get_bin_list("END")
        start_times = self.binner.get_bin_list("START", unit="TIME")
        end_times = self.binner.get_bin_list("END", unit="TIME")

        results = []
        for animal in self.animal_pool.animalDictionary.values():
            counts, durations = self.count_event(animal, event)

            for i in range(len(start_frames)):
                results.append(
                    {
                        "RFID": animal.RFID,
                        "ANIMALID": animal.baseId,
                        "EVENT": event,
                        "START_FRAME": start_frames[i],
                        "END_FRAME": end_frames[i],
                        "START_TIME": start_times[i],
                        "END_TIME": end_times[i],
                        "EVENT_COUNT": counts[i],
                        "FRAME_COUNT": durations[i],
                        "DURATION": durations[i] / 30 / 60,  # in minutes
                    }
                )

        df = pd.DataFrame(results)
        return df

    def process_event(self, event: str):
        """Process data between start and end frames to get a DataFrame
        containing the specified event counts and durations. It will process
        the whole dataset using the process window.
        """
        process_iterator = self.binner.get_process_iterator()
        df = None

        for process_frames in process_iterator:
            self.animal_pool.loadDetection(
                start=process_frames[0],
                end=process_frames[1],
                lightLoad=True,
            )
            processed_df = self.get_df_event(event)
            if df is None:
                df = processed_df
            else:
                df = pd.concat([df, processed_df], ignore_index=True)

        if df is None:
            raise ValueError("Unable to create a dataframe.")

        return self.sort_rfid_as_category(df)

    def get_df_activity(
        self,
        filter_flickering: bool = False,
        filter_stop: bool = False,
    ):
        """Get a DataFrame containing activity data for all animals. Can apply
        filters to exclude flickering and stop from distance and speed
        calculation. (distance are in cm and speed are in cm/s)

        It include distance, speed, move time and stop time
        binned according to the time window.
        """
        start_frames = self.binner.get_bin_list("START")
        end_frames = self.binner.get_bin_list("END")
        start_times = self.binner.get_bin_list("START", unit="TIME")
        end_times = self.binner.get_bin_list("END", unit="TIME")

        results = []
        for animal in self.animal_pool.animalDictionary.values():
            dist_list = animal.getDistancePerBin(
                binFrameSize=self.binner.bin_size,
                minFrame=start_frames[0],
                maxFrame=end_frames[-1],
                filter_flickering=filter_flickering,
                filter_stop=filter_stop,
            )
            speeds_list = animal.getSpeedPerBin(
                binFrameSize=self.binner.bin_size,
                minFrame=start_frames[0],
                maxFrame=end_frames[-1],
                filter_flickering=filter_flickering,
                filter_stop=filter_stop,
            )

            counts, durations = self.count_event(animal, "Stop")

            for i in range(len(dist_list)):
                results.append(
                    {
                        "RFID": animal.RFID,
                        "ANIMALID": animal.baseId,
                        "START_FRAME": start_frames[i],
                        "END_FRAME": end_frames[i],
                        "START_TIME": start_times[i],
                        "END_TIME": end_times[i],
                        "DISTANCE": dist_list[i],
                        "SPEED_MEAN": speeds_list[i][0],
                        "SPEED_STD": speeds_list[i][1],
                        "SPEED_MIN": speeds_list[i][2],
                        "SPEED_MAX": speeds_list[i][3],
                        "SPEED_SUM": speeds_list[i][4],
                        "STOP_COUNT": counts[i],
                        "STOP_DURATION": durations[i],
                        "MOVE_DURATION": self.binner.bin_size - durations[i],
                    }
                )

        df = pd.DataFrame(results)
        return df

    def process_activity(
        self,
        filter_flickering: bool = False,
        filter_stop: bool = False,
    ):
        """Process data between start and end frames to get a DataFrame
        containing activity data. It will process the whole dataset using
        the process window.
        """
        process_iterator = self.binner.get_process_iterator()
        df = None

        for process_frames in process_iterator:
            self.animal_pool.loadDetection(
                start=process_frames[0],
                end=process_frames[1],
                lightLoad=True,
            )
            processed_df = self.get_df_activity(filter_flickering, filter_stop)
            if df is None:
                df = processed_df
            else:
                df = pd.concat([df, processed_df], ignore_index=True)

        if df is None:
            raise ValueError("Unable to create a dataframe.")

        return self.sort_rfid_as_category(df)

    def sort_rfid_as_category(self, df: pd.DataFrame) -> pd.DataFrame:
        """Set the RFID column as a categorical data (sorted) type for better
        performance in plotting and analysis.

        Args:
            df (pd.DataFrame): The input DataFrame with an 'RFID' column.

        Returns:
            pd.DataFrame: The modified DataFrame with 'RFID' as a category.
        """
        sorted_rfids = sorted(df["RFID"].unique())
        df["RFID"] = pd.Categorical(
            df["RFID"], categories=sorted_rfids, ordered=True
        )
        return df
