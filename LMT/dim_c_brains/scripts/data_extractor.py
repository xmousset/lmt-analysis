"""
@author: xmousset
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
                raise ValueError("Bin size must be at least one minute")
            self.bin_size = bin_size
        else:
            if self.bin_size is None:
                raise ValueError("Bin size must be specified")

        if chunk_size is not None:
            if chunk_size <= oneHour:
                raise ValueError("Chunk size must be at least one hour")

            if chunk_size < self.bin_size:
                raise ValueError(
                    "Chunk size must be at least equal to bin size"
                )
            self.chunk_size = chunk_size
        else:
            if self.chunk_size is None:
                raise ValueError("Chunk size must be specified")

        if start_frame is None or start_frame < 1:
            self.start_frame = 1
        elif start_frame > self.last_frame:
            raise ValueError(
                f"start_frame out of range (start_frame = {start_frame} "
                f"> last_frame = {self.last_frame})"
            )
        else:
            self.start_frame = start_frame

        if end_frame is None or end_frame > self.last_frame:
            self.end_frame = self.last_frame
        elif end_frame < 1:
            raise ValueError(
                f"end_frame out of range (end_frame = {end_frame} < 1)"
            )
        else:
            self.end_frame = end_frame

        if self.start_frame >= self.end_frame:
            raise ValueError(
                f"Invalid frame limits (start_frame = {self.start_frame} >= "
                f"end_frame = {self.end_frame})"
            )

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

    def get_bin_iterators_for_processing(self):
        """Generates iterators over frame bins for processing. It returns a
        lisst of lists, where each sublist is a bin_iterator that correspond to
        a process window defined by the process iterator.

        Returns:
            List[List[tuple[int, int]]]: A list where each element corresponds
                to a process window, containing a list of (start, end) tuples
                for bins that are fully contained within that process window.
        """

        process_iterator = self.get_process_iterator()

        frames_start = self.get_bin_list("START")
        frames_end = self.get_bin_list("END")

        if frames_start[0] < self.start_frame:
            frames_start[0] = self.start_frame

        if frames_end[-1] > self.end_frame:
            frames_end[-1] = self.end_frame

        bin_iterators: List[List[tuple[int, int]]] = []
        for start_chunk, end_chunk in process_iterator:
            bin_iterators.append([])
            for start, end in zip(frames_start, frames_end):
                if start >= start_chunk and end <= end_chunk:
                    bin_iterators[-1].append((start, end))

        return bin_iterators

    def get_bin_iterator(self):
        """Get the full bin iterator (list of (start, end) tuples) between
        `self.start_frame` and `self.end_frame`."""

        frames_start = self.get_bin_list("START")
        frames_end = self.get_bin_list("END")

        if frames_start[0] < self.start_frame:
            frames_start[0] = self.start_frame

        if frames_end[-1] > self.end_frame:
            frames_end[-1] = self.end_frame

        bin_iterator: List[tuple[int, int]] = []
        for start, end in zip(frames_start, frames_end):
            bin_iterator.append((start, end))

        return bin_iterator


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
        processing_window: int = oneDay,
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
            processing_window (int, optional): The size (in frames) of each\
            data chunk to load into memory. Defaults to 1 day.
        """
        self.animal_pool = AnimalPool()
        self.animal_pool.loadAnimals(connection)

        self._init_binner(time_window, processing_window)
        self.set_analysis_frame_limits(start_frame, end_frame)

    def _init_binner(self, time_window: int, processing_window: int):
        """Initialize the DatetimeBinner object to compute the time bins."""
        query = "SELECT FRAMENUMBER, TIMESTAMP FROM FRAME ORDER BY FRAMENUMBER DESC LIMIT 1"
        cursor = self.animal_pool.conn.cursor()
        cursor.execute(query)
        result = cursor.fetchone()
        cursor.close()

        if not result:
            raise ValueError("No data found in FRAME table")

        lastframe, timestamp = result
        self.binner = DataProcessingBinner(
            lastframe, timestamp, time_window, processing_window
        )

    def set_time_window(self, time_window: int):
        """Set the time window (in frames) for data binning."""
        self.binner.set_parameters(bin_size=time_window)

    def get_bin_window(self) -> int:
        """Get the current time window (in frames) for data binning."""
        return self.binner.bin_size

    def set_processing_window(self, processing_window: int):
        """Set the processing window (in frames) for data chunking."""
        self.binner.set_parameters(chunk_size=processing_window)

    def get_processing_window(self) -> int:
        """Get the current processing window (in frames) for data chunking."""
        return self.binner.chunk_size

    def set_analysis_frame_limits(
        self,
        start_frame: int | None = None,
        end_frame: int | None = None,
    ):
        """Set the analysis frame limits for data processing."""
        self.binner.set_parameters(
            start_frame=start_frame, end_frame=end_frame
        )

    def set_analysis_time_limits(
        self,
        start_time: pd.Timestamp | None = None,
        end_time: pd.Timestamp | None = None,
    ):
        """Set the analysis frame limits for data processing from timestamps."""
        f_start = self.binner.time_to_frame(start_time) if start_time else None
        f_end = self.binner.time_to_frame(end_time) if end_time else None
        self.binner.set_parameters(start_frame=f_start, end_frame=f_end)

    def get_analysis_frame_limits(self) -> tuple[int, int]:
        """Get the analysis frame limits."""
        return (self.binner.start_frame, self.binner.end_frame)

    def get_analysis_time_limits(self) -> tuple[pd.Timestamp, pd.Timestamp]:
        """Get the analysis frame limits converted in timestamps."""
        start_time = self.binner.frame_to_time(self.binner.start_frame)
        end_time = self.binner.frame_to_time(self.binner.end_frame)
        return (start_time, end_time)

    def get_df_animals(self):
        """Get a DataFrame containing basic information about all animals."""
        print(f"Creating ANIMALS dataframe")
        df = pd.read_sql("SELECT * FROM ANIMAL", self.animal_pool.conn)

        return df

    def count_event_per_bin(
        self,
        animal: Animal,
        event: str,
        bin_iterator: List[tuple[int, int]] | None = None,
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
        if bin_iterator is None:
            bin_iterator = self.binner.get_bin_iterator()

        event_timeline = EventTimeLine(
            self.animal_pool.conn,
            event,
            idA=animal.baseId,
            minFrame=bin_iterator[0][0],
            maxFrame=bin_iterator[-1][1],
        )

        counts: List[int] = []
        durations: List[int] = []
        for f_min, f_max in bin_iterator:
            counts.append(event_timeline.getNumberOfEvent(f_min, f_max))
            durations.append(
                event_timeline.getTotalDurationEvent(f_min, f_max)
            )

        return (counts, durations)

    def get_df_event(
        self, event: str, bin_iterator: List[tuple[int, int]] | None = None
    ):
        """Get a DataFrame containing event counts and durations for specified
        event.
        """
        if bin_iterator is None:
            bin_iterator = list(
                zip(
                    self.binner.get_bin_list("START"),
                    self.binner.get_bin_list("END"),
                )
            )

        results = []
        for animal in self.animal_pool.getAnimalList():
            print(
                f"Creating EVENT dataframe ({event}) "
                f"for animal {animal.RFID}"
            )

            counts, durations = self.count_event_per_bin(
                animal, event, bin_iterator
            )

            for i in range(len(bin_iterator)):
                results.append(
                    {
                        "RFID": animal.RFID,
                        "ANIMALID": animal.baseId,
                        "EVENT": event,
                        "START_FRAME": bin_iterator[i][0],
                        "END_FRAME": bin_iterator[i][1],
                        "START_TIME": self.binner.frame_to_time(
                            bin_iterator[i][0]
                        ),
                        "END_TIME": self.binner.frame_to_time(
                            bin_iterator[i][1]
                        ),
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
        bin_iterators = self.binner.get_bin_iterators_for_processing()
        df = None

        for bin_iterator in bin_iterators:
            print(
                f"EVENT processing ({event}) for frames {bin_iterator[0][0]} to "
                f"{bin_iterator[-1][1]}"
            )
            processed_df = self.get_df_event(event, bin_iterator)
            if df is None:
                df = processed_df
            else:
                df = pd.concat([df, processed_df], ignore_index=True)

        if df is None:
            raise ValueError("Unable to create a dataframe")

        return self.sort_rfid_as_category(df)

    def get_df_activity(
        self,
        bin_iterator: List[tuple[int, int]] | None = None,
        filter_flickering: bool = False,
        filter_stop: bool = False,
    ):
        """Get a DataFrame containing activity data for all animals. Can apply
        filters to exclude flickering and stop from distance and speed
        calculation. (distance are in cm and speed are in cm/s)

        It include distance, speed, move time and stop time
        binned according to the time window.
        """
        if bin_iterator is None:
            bin_iterator = self.binner.get_bin_iterator()

        self.animal_pool.loadDetection(
            start=bin_iterator[0][0],
            end=bin_iterator[-1][1],
            lightLoad=True,
        )

        results = []
        for animal in self.animal_pool.getAnimalList():
            print(f"Creating ACTIVITY dataframe for animal {animal.RFID}")

            stop_counts, stop_durations = self.count_event_per_bin(
                animal, "Stop", bin_iterator
            )

            move_iso_counts, move_iso_durations = self.count_event_per_bin(
                animal, "Move isolated", bin_iterator
            )

            move_inc_counts, move_inc_durations = self.count_event_per_bin(
                animal, "Move in contact", bin_iterator
            )

            distances = animal.getDistancePerBin(
                binIterator=bin_iterator,
                filter_flickering=filter_flickering,
                filter_stop=filter_stop,
            )
            speeds = animal.getSpeedPerBin(
                binIterator=bin_iterator,
                filter_flickering=filter_flickering,
                filter_stop=filter_stop,
            )

            for i in range(len(bin_iterator)):
                results.append(
                    {
                        "RFID": animal.RFID,
                        "ANIMALID": animal.baseId,
                        "START_FRAME": bin_iterator[i][0],
                        "END_FRAME": bin_iterator[i][1],
                        "START_TIME": self.binner.frame_to_time(
                            bin_iterator[i][0],
                        ),
                        "END_TIME": self.binner.frame_to_time(
                            bin_iterator[i][1],
                        ),
                        "DISTANCE": distances[i],
                        "SPEED_MEAN": speeds[i][0],
                        "SPEED_MIN": speeds[i][1],
                        "SPEED_MAX": speeds[i][2],
                        "SPEED_SUM": speeds[i][3],
                        "SPEED_STD": speeds[i][4],
                        "SPEED_SEM": speeds[i][5],
                        "STOP_COUNT": stop_counts[i],
                        "STOP_DURATION": stop_durations[i]
                        / 30
                        / 60,  # in minutes
                        "MOVE_COUNT": move_iso_counts[i] + move_inc_counts[i],
                        "MOVE_DURATION": (
                            move_iso_durations[i] + move_inc_durations[i]
                        )
                        / 30
                        / 60,  # in minutes
                        "UNDETECTED_DURATION": (
                            bin_iterator[i][1]
                            - bin_iterator[i][0]
                            - stop_durations[i]
                            - (move_iso_durations[i] + move_inc_durations[i])
                        )
                        / 30
                        / 60,  # in minutes
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
        bin_iterators = self.binner.get_bin_iterators_for_processing()
        df = None

        for bin_iterator in bin_iterators:
            print(
                f"ACTIVITY processing for frames {bin_iterator[0][0]} to "
                f"{bin_iterator[-1][1]}"
            )
            processed_df = self.get_df_activity(
                bin_iterator, filter_flickering, filter_stop
            )
            if df is None:
                df = processed_df
            else:
                df = pd.concat([df, processed_df], ignore_index=True)

        if df is None:
            raise ValueError("Unable to create a dataframe")

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

    def calculate_sensors_statistics(
        self,
        sensor_name: str,
        frame_values: List[int],
        sensor_values: List[float],
        bin_iterator: List[tuple[int, int]],
    ):
        """Get sensors data (mean, min, max, std, sem) for a bin bordered by
        bin_start_frame and bin_end_frame.

        Returns a list of dicts, one per bin, always matching the number of bins.
        If no data in a bin, fills with np.nan.
        """

        results: List[Dict[str, float]] = []
        i_min = 0
        i_max = 0
        for _, f_max in bin_iterator:
            while frame_values[i_max] < f_max:
                i_max += 1
            arr = np.array(sensor_values[i_min : i_max + 1])
            i_min = i_max + 1
            results.append(
                {
                    f"{sensor_name}_MEAN": float(arr.mean()),
                    f"{sensor_name}_MIN": float(arr.min()),
                    f"{sensor_name}_MAX": float(arr.max()),
                    f"{sensor_name}_STD": (
                        float(arr.std()) if len(arr) > 1 else 0.0
                    ),
                    f"{sensor_name}_SEM": (
                        float(arr.std() / np.sqrt(len(arr)))
                        if len(arr) > 1
                        else 0.0
                    ),
                }
            )
        return results

    def get_df_sensors(
        self, bin_iterator: List[tuple[int, int]] | None = None
    ):

        if bin_iterator is None:
            bin_iterator = self.binner.get_bin_iterator()

        query_limits = f" WHERE FRAMENUMBER >= {bin_iterator[0][0]} AND FRAMENUMBER <= {bin_iterator[-1][1]}"

        sensors = [
            "TEMPERATURE",
            "HUMIDITY",
            "SOUND",
            "LIGHTVISIBLE",
            "LIGHTVISIBLEANDIR",
        ]

        cursor = self.animal_pool.conn.cursor()
        cursor.execute(f"SELECT FRAMENUMBER FROM FRAME" + query_limits)
        frame_rows = cursor.fetchall()
        cursor.close()
        frames = [row[0] for row in frame_rows]

        sensors_data: Dict[str, List[Dict[str, float]]] = {}
        for sensor in sensors:
            print(f"Creating SENSOR dataframe ({sensor})")
            try:
                cursor = self.animal_pool.conn.cursor()
                cursor.execute(f"SELECT {sensor} FROM FRAME" + query_limits)
                values = [row[0] for row in cursor.fetchall()]
                cursor.close()
                sensors_data[sensor] = self.calculate_sensors_statistics(
                    sensor, frames, values, bin_iterator
                )
            except:
                print(f"Cannot access data for {sensor} => Skipping")

        if not sensors_data.keys():
            print("No sensor data available")
            return None
        else:
            for sensor in sensors:
                if sensor not in sensors_data:
                    sensors.remove(sensor)

        results: List[Dict[str, Any]] = []
        for i in range(len(bin_iterator)):
            results.append(
                {
                    "START_FRAME": bin_iterator[i][0],
                    "END_FRAME": bin_iterator[i][1],
                    "START_TIME": self.binner.frame_to_time(
                        bin_iterator[i][0]
                    ),
                    "END_TIME": self.binner.frame_to_time(bin_iterator[i][1]),
                }
            )
            for sensor in sensors:
                for key, value in sensors_data[sensor][i].items():
                    results[-1][key] = value

        df = pd.DataFrame(results)
        return df

    def process_sensors(self):
        """Process data between start and end frames to get a DataFrame
        containing sensors data. It will process the whole dataset using
        the process window.
        """
        bin_iterators = self.binner.get_bin_iterators_for_processing()
        df = None

        for bin_iterator in bin_iterators:
            print(
                f"SENSORS processing for frames {bin_iterator[0][0]} to "
                f"{bin_iterator[-1][1]}"
            )
            processed_df = self.get_df_sensors(bin_iterator=bin_iterator)
            if df is None:
                df = processed_df
            else:
                df = pd.concat([df, processed_df], ignore_index=True)

        if df is None:
            print("Unable to create the sensors dataframe")
            return None

        return df
