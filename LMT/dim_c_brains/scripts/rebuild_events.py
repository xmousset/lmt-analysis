"""
@creation: 26-01-2026
@author: xmousset
"""

import sys
import traceback
from sqlite3 import Connection
from typing import Any, List, Literal, Set, Tuple
from types import ModuleType

import pandas as pd

from dim_c_brains.scripts.events_and_modules import (
    ALL_EVENTS,
    get_modules,
)
from dim_c_brains.scripts.binner import Binner

from lmtanalysis.Animal import AnimalPool
from lmtanalysis.AnimalType import AnimalType
from lmtanalysis.Event import Chronometer
from lmtanalysis.Measure import oneDay
from lmtanalysis import BuildDataBaseIndex, CheckWrongAnimal
from lmtanalysis.TaskLogger import TaskLogger
from lmtanalysis.EventTimeLineCache import (
    flushEventTimeLineCache,
    disableEventTimeLineCache,
)

from psutil import virtual_memory


class ReBuildEvents:
    def __init__(
        self,
        connection: Connection,
        file: Any,
        list_events: List[str] | Literal["all", "missing"] | None = None,
        processing_window: int = oneDay,
        start: int | pd.Timestamp | None = None,
        end: int | pd.Timestamp | None = None,
        animal_type: AnimalType = AnimalType.MOUSE,
    ):
        self.conn = connection
        self.file = file
        self.set_events_to_rebuild(list_events)
        self.animal_type = animal_type
        self._init_binner()
        self.set_processing_window(processing_window)
        self.set_analysis_limits(start, end)
        self.database_events = self.get_database_events()

    def get_database_events(self) -> Set[str]:
        """Get the list of existing events in the SQLite database."""
        query = "SELECT DISTINCT NAME FROM EVENT ORDER BY NAME"

        cursor = self.conn.cursor()
        cursor.execute(query)
        results = cursor.fetchall()
        cursor.close()

        database_events = set([row[0] for row in results])
        return database_events

    def get_missing_events_in_database(self) -> Set[str]:
        """Check if there are events that does not exist in the database and
        need to be rebuilt."""
        if self.list_events is None:
            raise ValueError("list_events must be initialized.")

        missing_events = set(self.list_events) - self.database_events
        return missing_events

    def need_rebuilding(self):
        """Check if there are events that does not exist in the database and
        need to be rebuilt."""
        missing_events = self.get_missing_events_in_database()
        return len(missing_events) > 0

    def _init_binner(self):
        """Initialize the DatetimeBinner object to compute the time bins."""
        query = "SELECT FRAMENUMBER, TIMESTAMP FROM FRAME ORDER BY FRAMENUMBER DESC LIMIT 1"
        cursor = self.conn.cursor()
        cursor.execute(query)
        result = cursor.fetchone()
        cursor.close()

        if not result:
            raise ValueError("No data found in FRAME table")

        lastframe, timestamp = result
        self.binner = Binner(lastframe, timestamp)

    def set_processing_window(self, processing_window: int):
        """Set the processing window (in *frames*) for processing."""
        self.binner.set_parameters(bin_size=processing_window)

    def get_processing_window(self, unit: Literal["FRAME", "TIME"] = "FRAME"):
        """Get the processing window for data analysis."""
        if unit == "FRAME":
            return self.binner.bin_size
        elif unit == "TIME":
            return self.binner.frames_to_timedelta(self.binner.bin_size)
        else:
            raise ValueError("Invalid unit. Choose 'FRAME' or 'TIME'.")

    def set_events_to_rebuild(
        self, list_events: List[str] | Literal["all", "missing"] | None = None
    ):
        """Sets the list of events to be rebuilt."""
        if list_events is None:
            self.list_events: List[str] = []
            self.list_BuildEvent: Set[ModuleType] = set()
            return

        if isinstance(list_events, str):
            if list_events == "missing":
                self.list_events = list(self.get_missing_events_in_database())
            elif list_events == "all":
                self.list_events = list(ALL_EVENTS.keys())
            else:
                raise ValueError(
                    f"Invalid string value for list_events: {list_events}"
                )
        else:
            self.list_events = list_events
        self.list_BuildEvent = get_modules(self.list_events)

    def set_analysis_limits(
        self,
        start: int | pd.Timestamp | None = None,
        end: int | pd.Timestamp | None = None,
    ):
        """Set the analysis limits for data processing from frames or
        timestamps."""

        if isinstance(start, pd.Timestamp):
            f_start = self.binner.time_to_frame(start)
        else:
            f_start = start

        if isinstance(end, pd.Timestamp):
            f_end = self.binner.time_to_frame(end)
        else:
            f_end = end

        self.binner.set_parameters(start_frame=f_start, end_frame=f_end)

    def get_analysis_limits(
        self, unit: Literal["FRAME", "TIME"] = "FRAME"
    ) -> Tuple[Any, Any]:
        """Get the analysis frame limits.

        Returns:
            Tuple: The start and end limits in the specified unit.
            It is either in frames (int) or timestamps (pd.Timestamp).
        """
        if unit == "FRAME":
            return (self.binner.start_frame, self.binner.end_frame)
        elif unit == "TIME":
            start_time = self.binner.frame_to_time(self.binner.start_frame)
            end_time = self.binner.frame_to_time(self.binner.end_frame)
            return (start_time, end_time)
        else:
            raise ValueError("Invalid unit. Choose 'FRAME' or 'TIME'.")

    def flush_events(self):
        """Flush events in the database using the specified modules."""
        chrono = Chronometer("Flushing events")

        for module in self.list_BuildEvent:
            module.flush(self.conn)

        chrono.printTimeInS()

    def flush_all_events(self):
        """Flush all events in the database using all existing modules."""
        chrono = Chronometer("Flushing all events")

        for module in get_modules("all"):
            module.flush(self.conn)

        chrono.printTimeInS()

    def check_memory(self):
        """Check available system memory and disable event caching if
        necessary."""
        mem = virtual_memory()
        availableMemoryGB = mem.total / 1_000_000_000
        print("Total memory on computer: (GB)", availableMemoryGB)

        if availableMemoryGB < 10:
            print("Not enough memory to use cache load of events.")
            disableEventTimeLineCache()

    def rebuild_window(self, window: Tuple[int, int]):
        """Rebuild events in the specified time window using the specified
        modules."""
        tmin = self.binner.frame_to_time(window[0])
        CheckWrongAnimal.check(self.conn, window[0], window[1])

        if not self.list_BuildEvent:
            print("No events to process in this window.")
            return

        animalPool = None
        flushEventTimeLineCache()
        print("Caching load of animal detection...")
        animalPool = AnimalPool()
        animalPool.loadAnimals(self.conn)
        animalPool.loadDetection(start=window[0], end=window[1])
        print("Caching load of animal detection done.")

        for BuildEvent in self.list_BuildEvent:

            event_chrono = Chronometer(str(BuildEvent))
            BuildEvent.reBuildEvent(
                self.conn,
                self.file,
                tmin=window[0],
                tmax=window[1],
                pool=animalPool,
                animalType=self.animal_type,
            )
            event_chrono.printTimeInS()

    def rebuild(self):
        """Rebuild events in the database from 'self.start' to 'self.end' using
        the specified modules."""
        if not self.list_BuildEvent:
            print("No events to process in this window.")
            return

        self.check_memory()
        chrono = Chronometer("ReBuild events")

        # update missing fields
        try:
            cursor = self.conn.cursor()
            query = "ALTER TABLE EVENT ADD METADATA TEXT"
            cursor.execute(query)
            self.conn.commit()
        except:
            print("METADATA field already exists")

        BuildDataBaseIndex.buildDataBaseIndex(self.conn, force=False)
        animalPool = AnimalPool()
        animalPool.loadAnimals(self.conn)

        try:
            self.flush_events()
            for window in self.binner.get_bin_iterator():

                window_chrono = Chronometer(
                    "File "
                    + self.file
                    + " from "
                    + str(window[0])
                    + " to "
                    + str(window[1])
                )
                self.rebuild_window(window)
                window_chrono.printTimeInS()

            print("Full file process time: ")
            chrono.printTimeInS()

        except:
            exc_type, exc_value, exc_traceback = sys.exc_info()
            lines = traceback.format_exception(
                exc_type, exc_value, exc_traceback
            )
            error = "".join("!! " + line for line in lines)

            t = TaskLogger(self.conn)
            t.addLog(error)
            flushEventTimeLineCache()

            print(error, file=sys.stderr)
            raise Exception()

        print("*** ALL JOBS DONE ***")
