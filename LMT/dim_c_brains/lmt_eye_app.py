"""
@author: xmousset
"""

print("Starting LMT-EYE...")

import sys
from pathlib import Path

################
#   APP INFO   #
################
# command for executable creation (run in terminal at project root):
# pyinstaller -p LMT --onefile --icon=LMT/dim_c_brains/res/lmt_eye_icon.png --add-data "LMT/dim_c_brains/res/lmt_eye_icon.png;dim_c_brains/res" --add-data "LMT/dim_c_brains/res/template;dim_c_brains/res/template" --add-data "LMT/dim_c_brains/res/assets;dim_c_brains/res/assets" --add-data "LMT/dim_c_brains/res/mouse_run.gif;dim_c_brains/res" LMT/dim_c_brains/lmt_eye_app.py

APP_VERSION = "1.4"
APP_RELEASE = "2026-04-08"

if hasattr(sys, "_MEIPASS"):
    # in app
    LMT_PATH = Path(__file__).parent
else:
    # in dev
    LMT_PATH = Path(__file__).parent.parent
    # add LMT folder to path for importing modules in dev
    sys.path.append(str(LMT_PATH))

ICON_PATH = LMT_PATH / "dim_c_brains" / "res" / "lmt_eye_icon.png"
GIF_PATH = LMT_PATH / "dim_c_brains" / "res" / "mouse_run.gif"


################
#   IMPORTS   #
################
import traceback
from typing import Literal
from datetime import datetime

import pandas as pd

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon, QMovie
from PyQt6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QFileDialog,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QSpinBox,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from PyQt6.QtCore import QObject, QRunnable, QThreadPool, pyqtSignal, pyqtSlot

from dim_c_brains.scripts.events_and_modules import ALL_EVENTS
from dim_c_brains.lmt_eye_data_analysis import LMTEYEDataAnalyzer
from dim_c_brains.lmt_eye_settings import LMTEYESettings
from dim_c_brains.widgets.pyqt6_tools import YesNoQuestion, get_btn_style
from dim_c_brains.widgets.area_selection import AreaSelectionDialog
from dim_c_brains.widgets.sql_modifications import UpdateDatabaseInfo
from dim_c_brains.widgets.event_selection import EventSelectionDialog

from lmtanalysis.Animal import AnimalType


class LMTEYEApp(QMainWindow):
    """Main application class for LMT-EYE."""

    def __init__(self):
        """Initialize the LMT-EYE application."""
        super().__init__()
        self.setWindowTitle("LMT-EYE - v" + APP_VERSION)
        self.setFixedSize(550, 400)
        self._init_ui()

    def _init_ui(self):
        self.database_analysis = DatabaseAnalysisWindow()
        # self.compare_analysis = CompareWidget()

        self.stacked = QStackedWidget()
        self.stacked.addWidget(self.database_analysis)
        # self.stacked.addWidget(self.compare_analysis)
        self.setCentralWidget(self.stacked)
        # Example: switch with a button

        menu = self.menuBar()
        if menu is None:
            raise RuntimeError("Menu bar error.")

        switch_menu = menu.addMenu("Options")
        if switch_menu is None:
            raise RuntimeError("Switch menu error.")
        switch_menu.addAction(
            "Analyse one database", lambda: self.change_ui(0)
        )
        switch_menu.addAction(
            "Merge Analysis (work in progress)", lambda: self.change_ui(1)
        )  # TODO: add compare widget and connect it here

        help_menu = menu.addMenu("Help")
        if help_menu is None:
            raise RuntimeError("Help menu error.")
        help_menu.addAction("About LMT-EYE", lambda: self.show_help("version"))
        help_menu.addAction("Resources", lambda: self.show_help("resources"))
        help_menu.addAction("Documentation", lambda: self.show_help("doc"))

    def change_ui(self, idx: int | None = None):
        if idx is not None:
            if idx >= 0 and idx < self.stacked.count():
                new_idx = idx
            else:
                print(f"Invalid index {idx} for stacked widget. Ignoring.")
                return
        else:
            new_idx = (self.stacked.currentIndex() + 1) % self.stacked.count()

        self.stacked.setCurrentIndex(new_idx)

    def show_help(
        self, option: Literal["full", "version", "resources", "doc"] = "full"
    ):
        help_dialog = HelpDialog(self)
        match option:
            case "version":
                help_dialog.init_ui(help_dialog.version_msg())
            case "resources":
                help_dialog.init_ui(help_dialog.resources_msg())
            case "doc":
                help_dialog.init_ui(help_dialog.doc_msg())
        help_dialog.exec()


class HelpDialog(QDialog):

    def __init__(self, parent: QWidget | None) -> None:
        super().__init__(parent)

        self.setWindowTitle("Help")
        self.setFixedWidth(300)
        # self.init_ui(self.full_msg())

    def init_ui(self, msg: str):
        label = QLabel()
        label.setTextFormat(Qt.TextFormat.RichText)
        label.setText(msg)
        label.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
            | Qt.TextInteractionFlag.LinksAccessibleByMouse
        )
        label.setOpenExternalLinks(True)
        label.setWordWrap(True)

        btn_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok)
        btn_box.accepted.connect(self.accept)

        layout = QVBoxLayout(self)
        layout.addWidget(label)
        layout.addWidget(btn_box)

    def version_msg(self):
        msg = f"""
            <b>LMT-EYE</b> - <i>Explore Your Experiments !</i><br>
            <br>
            Version: {APP_VERSION}<br>
            Release date: {APP_RELEASE}<br>
        """
        return msg

    def resources_msg(self):
        msg = f"""
            You can find the source code of LMT-EYE on the following link:<br>
            Github: <a href='https://github.com/xmousset/lmt-analysis'>
            LMT-EYE repository</a><br>
            <br>
            To seek for help, visit LMT website:<br>
            <a href='https://micecraft.org/lmt/'>
            https://micecraft.org/lmt/</a><br>
            <br>
            You can also go on the LMT Discord server to ask LMT creators and
            other users about your problems to have a quick answer:<br>
            <a href='https://discord.com/invite/zWDHNf9eHM'>
            Join LMT Discord server</a>
        """
        return msg

    def doc_msg(self):
        msg = f"""
            <b>LMT Documentation</b><br>
            <br>
            Here are some documentation resources to help you understand LMT
            and LMT-EYE better:<br>
            <br>
            - <a href='https://drive.google.com/file/d/1UHNGL4BUCNpipz1y25DdsF0rw2LvPh8g/view?usp=sharing'>
            MEMO LMT Assembly</a><br>
            <br>
            - <a href='https://drive.google.com/file/d/12u-4uoQW96lL5BojxxcKDYHrrWUD99CK/view?usp=sharing'>
            MEMO LMT Database</a><br>
            <br>
            - <a href='https://docs.google.com/document/d/1Wn0yfELiKF1Vydvoe-_4qiQ44q61_3xg85r0I6be33Y/edit?usp=sharing'>
            RFID Tags informations</a><br>
        """
        return msg

    def full_msg(self):
        return (
            self.version_msg()
            + "<br><br>"
            + self.resources_msg()
            + "<br><br>"
            + self.doc_msg()
        )


class DatabaseAnalysisWindow(QWidget):
    """Database Analysis Widget for LMT-EYE.
    It allows to load a database, rebuild events and create reports.
    """

    def __init__(self):
        """Initialize the database analysis widget."""
        super().__init__()
        self.database_path = None
        self.threadpool = QThreadPool()
        self.threadpool.setMaxThreadCount(1)
        # TODO: add option for multiple threads in app menu
        self._init_ui()

    def _init_ui(self):
        """Initialize the UI elements of the database analysis window."""
        main_layout = QVBoxLayout()

        #######################################
        #   Database informations   #
        #######################################
        self.info_label = QLabel()
        self.info_label.setTextFormat(Qt.TextFormat.RichText)
        self.info_label.setText("<b>No loaded database.</b>")

        db_info_row = QHBoxLayout()
        db_info_row.addWidget(self.info_label)
        main_layout.addLayout(db_info_row)

        #######################################
        #   Buttons row   #
        #######################################

        # database button
        btn_style = get_btn_style(size=15, bold=True, bg_color="#1976D2")
        self.load_db_btn = QPushButton("Load Database")
        self.load_db_btn.setStyleSheet(btn_style)
        self.load_db_btn.setFixedSize(150, 50)
        self.load_db_btn.clicked.connect(self.on_load_db)

        btn_style = get_btn_style(size=15, bold=True)

        # update animals information button
        self.update_info_btn = QPushButton("Animals Infos")
        self.update_info_btn.setStyleSheet(btn_style)
        self.update_info_btn.setFixedSize(150, 50)
        self.update_info_btn.clicked.connect(self.on_update_info)

        # continue button
        self.continue_btn = QPushButton("Continue")
        self.continue_btn.setStyleSheet(btn_style)
        self.continue_btn.setFixedSize(150, 50)
        self.continue_btn.clicked.connect(self.on_continue)

        # row layout
        buttons_row = QHBoxLayout()
        buttons_row.addStretch(1)
        buttons_row.addWidget(self.load_db_btn)
        buttons_row.addWidget(self.update_info_btn)
        buttons_row.addWidget(self.continue_btn)
        buttons_row.addStretch(1)

        main_layout.addLayout(buttons_row)

        self.setLayout(main_layout)

    def update_database_info(self):
        """Update database information displayed in the main window."""
        infos = {}
        if self.database_path is not None:
            t_format = "%Y %B - %A %d - %H:%M"
            infos = LMTEYEDataAnalyzer.get_informations(self.database_path)

            local_time = datetime.now().astimezone()
            utc_offset = local_time.utcoffset()
            utc_offset_name = local_time.tzname()
            if utc_offset is None:
                print("Warning: UTC offset is None, setting to 0.")
                utc_offset = pd.Timedelta(0)
                utc_offset_str = "?"
            else:
                utc_hours = utc_offset.total_seconds() / 3600
                if utc_hours == int(utc_hours):
                    utc_offset_str = f"{int(utc_hours):+.0f}"
                elif (utc_hours * 10) == int(utc_hours * 10):
                    utc_offset_str = f"{utc_hours:+.1f}"
                else:
                    utc_offset_str = f"{utc_hours:+.2f}"

            start_time = (infos["start_time"] + utc_offset).strftime(t_format)
            end_time = (infos["end_time"] + utc_offset).strftime(t_format)
            d = infos["duration"].days
            h = infos["duration"].seconds // 3600
            m = (infos["duration"].seconds // 60) % 60
            info_html = f"""
                <table style='font-size:13px;'>
                <tr>
                    <td><b>Database:</b></td>
                    <td>{infos["database_name"]}</td>
                </tr>
                <tr>
                    <td><b>Animals:</b></td>
                    <td>{infos["n_animals"]}</td>
                </tr>
                <tr>
                    <td><b>Start:</b></td>
                    <td>{start_time}</td>
                </tr>
                <tr>
                    <td><b>End:</b></td>
                    <td>{end_time}</td>
                </tr>
                <tr>
                    <td colspan="2" style="color: gray; font-family: Calibri;">
                        <center><i>
                            <span>&#11169;</span>&nbsp;
                            your time zone: UTC{utc_offset_str} - {utc_offset_name}
                        </i></center>
                    </td>
                </tr>
                <tr>
                    <td><b>Duration:</b></td>
                    <td>{d} days, {h} hours and {m} minutes</td>
                </tr>
                <tr>
                    <td><b>FPS:</b></td>
                    <td>{infos["fps"]:.1f}</td>
                </tr>
                </table>
            """
            self.info_label.setText(info_html)
        else:
            info_html = f"""
                <table style='font-size:13px;'>
                <tr><td><b>Database:</b></td><td>No loaded database.</td></tr>
                </table>
            """

        self.info_label.setText(info_html)

    def on_load_db(self):
        """Launches a file dialog for loading database."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select SQLite file",
            "",
            "SQLite files (*.sqlite);;All files (*)",
        )
        if not file_path:
            return
        self.database_path = Path(file_path)
        self.update_database_info()

        btn_style = get_btn_style(size=15, bold=True)
        self.load_db_btn.setStyleSheet(btn_style)

        btn_style = get_btn_style(size=15, bold=True, bg_color="#1976D2")
        self.continue_btn.setStyleSheet(btn_style)
        self.update_info_btn.setStyleSheet(btn_style)

    def warning_message_load_database(self):
        """Check if a database is loaded, and show a warning if not."""
        QMessageBox.warning(
            self,
            "No Database",
            "You must load a database before.",
        )

    def on_update_info(self):
        """Update animals information in database."""
        if self.database_path is None:
            self.warning_message_load_database()
            return

        UpdateDatabaseInfo(self, self.database_path).exec()

    def on_continue(self):
        """Rebuild database then analyse it."""
        if self.database_path is None:
            self.warning_message_load_database()
            return

        dlg = SettingsWindow(self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            settings = dlg.settings
        else:
            print("Process cancelled.")
            return

        analyzer = LMTEYEDataAnalyzer(self.database_path, settings)

        progress_bar = DatabaseAnalysisProgressBar(
            self, database_name=self.database_path.stem
        )

        worker = LMTEYEWorker(analyzer)
        worker.signals.rebuild_progress.connect(
            progress_bar.set_rebuild_progress
        )
        worker.signals.analyse_progress.connect(
            progress_bar.set_analyse_progress
        )
        worker.signals.analyzer.connect(self.handle_open_analysis)
        worker.signals.finished.connect(progress_bar.progression_finished)

        progress_bar.show()
        self.threadpool.start(worker)

        print(f"Process for {self.database_path.stem} queued/started.")

    def handle_open_analysis(self, analyzer: LMTEYEDataAnalyzer):
        """Ask user if they want to open the processed results when the
        analysis is finished.
        Automatically close the window after 5 minutes if the user does not
        answer."""
        if analyzer is not None:
            print("*** PROCESS FINISHED ***")

            if analyzer.database_path is None:
                print("Error: Analyzer has no database path.")
                return

            name = analyzer.database_path.stem
            output = analyzer.get_output_folder()
            text = f"""
            LMT-EYE has finished to analyse the following database:
            {name}\n
            Results are saved in:
            {output}\n
            Do you want to open the results ?
            """
            dlg = YesNoQuestion(
                parent=self,
                question=text,
                timeout_s=300,  # 5 minutes
            )
            if dlg.exec():
                analyzer.open_analysis_output()
        else:
            QMessageBox.critical(self, "Error", "Analysis failed.")


class LMTEYEWorkerSignals(QObject):
    """Manage signals from a running worker thread."""

    finished = pyqtSignal(bool)
    analyzer = pyqtSignal(LMTEYEDataAnalyzer)
    rebuild_progress = pyqtSignal(int, int)  # current, max
    analyse_progress = pyqtSignal(int, int)  # current, max


class LMTEYEWorker(QRunnable):
    def __init__(self, data_analyzer: LMTEYEDataAnalyzer):
        super().__init__()
        self.data_analyzer = data_analyzer
        self.signals = LMTEYEWorkerSignals()

    @pyqtSlot()
    def run(self):
        try:
            self.data_analyzer.rebuild_database(
                progress_callback=self.signals.rebuild_progress.emit
            )
            self.data_analyzer.run_analysis(
                progress_callback=self.signals.analyse_progress.emit
            )

            self.signals.finished.emit(True)
            self.signals.analyzer.emit(self.data_analyzer)

        except Exception as e:
            print(f"Error in LMTEYEWorker: {e}")
            traceback.print_exc()
            self.signals.finished.emit(False)


class DatabaseAnalysisProgressBar(QDialog):
    """Dialog to show progress during database analysis."""

    def __init__(
        self,
        parent=None,
        title="Analysis progression",
        database_name: str | None = None,
    ):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setModal(False)
        self.setFixedSize(350, 220)
        self._init_ui(database_name)

    def _init_ui(self, database_name: str | None):
        form = QFormLayout()

        if database_name is None:
            label_text = "Processing. Please wait."
        else:
            label_text = f"{database_name}\nis being processed, please wait."

        process_label = QLabel(label_text)
        process_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        process_label.setStyleSheet("font-size: 15px;")

        movie_label = QLabel()
        movie_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.movie = QMovie(str(GIF_PATH))
        if self.movie.isValid():
            movie_label.setMovie(self.movie)
            self.movie.start()

        self.rebuild_progress = QProgressBar()
        self.rebuild_progress.setMinimum(0)
        self.analyse_progress = QProgressBar()
        self.analyse_progress.setMinimum(0)

        form.addRow(process_label)
        form.addRow(movie_label)
        form.addRow("Rebuild Progress", self.rebuild_progress)
        form.addRow("Analyse Progress", self.analyse_progress)

        self.setLayout(form)

    def set_rebuild_progress(self, value, maximum):
        self.rebuild_progress.setMaximum(maximum)
        self.rebuild_progress.setValue(value)

    def set_analyse_progress(self, value, maximum):
        self.analyse_progress.setMaximum(maximum)
        self.analyse_progress.setValue(value)

    def progression_finished(self, is_finished: bool):
        if is_finished:
            self.accept()
        else:
            self.reject()


class SettingsWindow(QDialog):
    """Dialog to edit LMT-EYE settings."""

    SAVING_PATH = Path.home() / "documents" / "LMT-EYE_settings"
    SAVING_PATH.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def load_default_settings():
        """Load default settings if available."""

        settings = LMTEYESettings()

        default_path = SettingsWindow.SAVING_PATH / "default_settings.json"

        if default_path.is_file():
            settings.load(default_path)
        else:
            print("Warning: 'default_settings.json' not found.")

        return settings

    def __init__(self, parent: QWidget | None):
        """Initialize the settings window by loading default settings."""
        super().__init__(parent)
        self.setWindowTitle("LMT-EYE - Settings")

        self.settings = self.load_default_settings()
        self._init_ui()

    def _init_ui(self):
        form = QFormLayout()

        #######################################
        #   Output folder   #
        #######################################

        # output_folder
        if self.settings.output_folder is None:
            output_text = ""
        else:
            output_text = str(self.settings.output_folder)

        self.output_folder_edit = QLineEdit(output_text)
        self.output_folder_edit.setReadOnly(True)
        self.output_folder_edit.setPlaceholderText(
            "same folder as database by default"
        )
        self.output_folder_edit.setToolTip(
            "Folder where analysis results will be saved."
        )
        out_btn = QPushButton("Browse")
        btn_style = get_btn_style()
        out_btn.setStyleSheet(btn_style)
        out_btn.setFixedWidth(80)
        out_btn.clicked.connect(self.select_output_folder)

        out_row = QHBoxLayout()
        out_row.addWidget(self.output_folder_edit)
        out_row.addWidget(out_btn)

        form.addRow("<b>Output Folder</b>", out_row)

        #######################################
        #   Animal Type   #
        #######################################

        # animal_type
        self.animal_type_box = QComboBox()
        self.animal_type_box.setToolTip(
            "Type of animals used in the experiment."
        )
        options = [animal_type.name for animal_type in AnimalType]
        self.animal_type_box.addItems(options)
        current_type = self.settings.animal_type.name
        if current_type in options:
            self.animal_type_box.setCurrentText(current_type)
        else:
            print(f"Animal type '{current_type}' is not available.")
            self.animal_type_box.setCurrentText("ERROR")

        # row layout
        animal_type_row = QHBoxLayout()
        animal_type_row.addWidget(self.animal_type_box)
        animal_type_row.addStretch(1)

        form.addRow("<b>Animal type</b>", animal_type_row)
        form.addRow(self.Qhline())

        #######################################
        #   EVENTS   #
        #######################################

        # events (known)
        btn_style = get_btn_style(size=15, bold=True, bg_color="#1976D2")
        self.select_events_btn = QPushButton("Select Events")
        self.select_events_btn.setToolTip(
            "Select events to rebuild and analyse in the analysis process."
        )
        self.select_events_btn.setStyleSheet(btn_style)
        self.select_events_btn.setFixedWidth(150)
        self.select_events_btn.clicked.connect(self.on_select_events)

        # events (custom)
        self.custom_event_edit = QLineEdit()
        self.custom_event_edit.setPlaceholderText("no custom events")
        self.custom_event_edit.setToolTip(
            "Enter custom event names to be included in the analysis. "
            "Separate multiple events with commas.\n"
            "(e.g.: Event1, Event2, Event3)"
        )

        # rebuild_events
        self.rebuild_box = QCheckBox()
        self.rebuild_box.setToolTip(
            "Wether to rebuild all selected events in the database before "
            "analysis (Checked)\n or to rebuild only the events that does not "
            "exists in the database (Unchecked).\n Unchecked is faster."
        )
        self.rebuild_box.setChecked(self.settings.rebuild_events)

        # rows layout
        events_row = QHBoxLayout()
        events_row.addStretch(4)
        events_row.addWidget(self.select_events_btn)
        events_row.addStretch(3)
        events_row.addWidget(QLabel("Rebuild:"))
        events_row.addWidget(self.rebuild_box)

        custom_row = QHBoxLayout()
        custom_row.addWidget(self.custom_event_edit)

        form.addRow("<b>Events</b>", events_row)
        form.addRow("<b>Custom events</b>", custom_row)
        form.addRow(self.Qhline())

        #######################################
        #   ANALYSIS FILTERS   #
        #######################################

        # filter_flickering
        self.flickering_cb = QCheckBox()
        self.flickering_cb.setToolTip(
            "Whether to filter the 'Flickering' event for animal activity.\n"
            "If enabled, all frames containing a 'Flickering' event will be "
            "excluded from the activity analysis."
        )
        self.flickering_cb.setChecked(self.settings.filter_flickering)

        # filter_stop
        self.stop_cb = QCheckBox()
        self.stop_cb.setToolTip(
            "Whether to filter the 'Stop' event for animal activity.\n"
            "If enabled, all frames containing a 'Stop' event will be "
            "excluded from the activity analysis."
        )
        self.stop_cb.setChecked(self.settings.filter_stop)

        # row layout
        filters_row = QHBoxLayout()
        filters_row.addWidget(QLabel("Flickering:"))
        filters_row.addWidget(self.flickering_cb)
        filters_row.addStretch(1)
        filters_row.addWidget(QLabel("Stop:"))
        filters_row.addWidget(self.stop_cb)
        filters_row.addStretch(1)

        form.addRow("<b>Filters</b>", filters_row)
        form.addRow(self.Qhline())

        #######################################
        #   ANALYZED AREA   #
        #######################################
        btn_style = get_btn_style(size=15, bold=True, bg_color="#1976D2")
        self.select_area_btn = QPushButton("Select Area")
        self.select_area_btn.setToolTip(
            "Select the area to be analyzed in the analysis process."
        )
        self.select_area_btn.setStyleSheet(btn_style)
        self.select_area_btn.setFixedWidth(150)
        self.select_area_btn.clicked.connect(self.on_select_area)

        self.selected_area_label = QLabel()
        self._update_area_label()

        area_row = QVBoxLayout()
        area_row.addWidget(
            self.select_area_btn, alignment=Qt.AlignmentFlag.AlignCenter
        )
        area_row.addWidget(
            self.selected_area_label, alignment=Qt.AlignmentFlag.AlignCenter
        )

        form.addRow("<b>Area filtering</b>", area_row)
        form.addRow(self.Qhline())

        #######################################
        #   TIME, PROCESSING and FPS   #
        #######################################

        # time_window (frames and minutes)
        self.time_window_frames = QSpinBox()
        self.time_window_frames.setToolTip(
            "Defines the binning of datas for the analysis (in frames)."
        )
        self.time_window_frames.setRange(1, 100_000_000)
        self.time_window_frames.setValue(self.settings.time_window)

        self.time_window_minutes = QDoubleSpinBox()
        self.time_window_minutes.setToolTip(
            "Defines the binning of datas for the analysis (in minutes)."
        )
        self.time_window_minutes.setDecimals(0)
        self.time_window_minutes.setRange(0, 100_000)
        self.time_window_minutes.setValue(
            int(self.settings.time_window / (self.settings.fps * 60))
        )

        # processing_window (frames and minutes)
        self.process_window_frames = QSpinBox()
        self.process_window_frames.setToolTip(
            "Defines the time window to consider for each processing step "
            "(in frames). Useful if the analysis is very long and needs to "
            "be processed in chunks.\n"
            "Do not impact analysis results."
        )
        self.process_window_frames.setRange(1, 100_000_000)
        self.process_window_frames.setValue(self.settings.processing_window)

        self.process_window_hours = QDoubleSpinBox()
        self.process_window_hours.setToolTip(
            "Defines the time window to consider for each processing step "
            "(in hours). Useful if the analysis is very long and needs to "
            "be processed in chunks.\n"
            "Do not impact analysis results."
        )
        self.process_window_hours.setDecimals(0)
        self.process_window_hours.setRange(0, 10_000)
        self.process_window_hours.setValue(
            int(
                self.settings.processing_window / (self.settings.fps * 60 * 60)
            )
        )

        # bin_rounding
        self.bin_rounding_cb = QCheckBox()
        self.bin_rounding_cb.setToolTip(
            "Whether to round bins in order to match round hours for the "
            "analysis.\n"
            "Example with 15 minutes bins and an experiment start at 12h07: \n"
            "- ENABLED: bins will be 12h00, 12h15, 12h30, 12h45, etc\n"
            "- DISABLED: bins will be 12h07, 12h22, 12h37, 12h52, etc.\n"
            "Rounding bins can make analysis results easier to read and "
            "compare between experiments.\n"
            "Note: if enabled, the first bin will start before the start of "
            "the experiment\n (e.g. 12h00 in the previous example), and not "
            "at the experiment start (e.g. 12h07 in the previous example).\n"
            "This leads to a first bin with less data than the others."
        )
        self.bin_rounding_cb.setChecked(self.settings.bin_rounding)

        # fps
        self.fps_spin = QSpinBox()
        self.fps_spin.setToolTip(
            "Frames per second of the recording.\n"
            "DO NOT MODIFY UNLESS YOU KNOW WHAT YOU ARE DOING."
        )
        self.fps_spin.setRange(1, 60)
        self.fps_spin.setValue(self.settings.fps)
        self.fps_spin.setMinimumWidth(75)

        # updates frames when times are changed, and vice versa
        self.time_window_frames.valueChanged.connect(
            self._on_time_frames_changed
        )
        self.time_window_minutes.valueChanged.connect(
            self._on_time_minutes_changed
        )
        self.process_window_frames.valueChanged.connect(
            self._on_process_frames_changed
        )
        self.process_window_hours.valueChanged.connect(
            self._on_process_hours_changed
        )
        self.fps_spin.valueChanged.connect(self._on_fps_changed)

        # layout for time, processing and fps
        time_row = QHBoxLayout()
        time_row.addStretch(1)
        time_row.addWidget(QLabel("Frames:"))
        time_row.addWidget(self.time_window_frames)
        time_row.addStretch(1)
        time_row.addWidget(QLabel("Minutes:"))
        time_row.addWidget(self.time_window_minutes)
        time_row.addStretch(1)
        form.addRow("<b>Binning</b>", time_row)

        proc_row = QHBoxLayout()
        proc_row.addStretch(1)
        proc_row.addWidget(QLabel("Frames:"))
        proc_row.addWidget(self.process_window_frames)
        proc_row.addStretch(1)
        proc_row.addWidget(QLabel("Hours:"))
        proc_row.addWidget(self.process_window_hours)
        proc_row.addStretch(1)
        form.addRow("<b>Processing</b>", proc_row)

        fps_row = QHBoxLayout()
        fps_row.addStretch(1)
        fps_row.addWidget(QLabel("Round hour bins:"))
        fps_row.addWidget(self.bin_rounding_cb)
        fps_row.addStretch(1)
        fps_row.addWidget(QLabel("FPS:"))
        fps_row.addWidget(self.fps_spin)
        fps_row.addStretch(1)
        form.addRow("<b>FPS</b>", fps_row)

        form.addRow(self.Qhline())

        #######################################
        #   NIGHT TIME   #
        #######################################
        # night_begin
        self.night_begin_spin = QSpinBox()
        self.night_begin_spin.setToolTip(
            "Define when the night cycle began (in hours, 0-23).\n"
            "Only used to display a shadow on graphs during night hours."
        )
        self.night_begin_spin.setRange(0, 23)
        self.night_begin_spin.setValue(self.settings.night_begin)
        self.night_begin_spin.setMinimumWidth(75)

        # night_duration
        self.night_duration_spin = QSpinBox()
        self.night_duration_spin.setToolTip(
            "Define the night cycle duration (in hours, 0-24).\n"
            "Only used to display a shadow on graphs during night hours."
        )
        self.night_duration_spin.setRange(0, 24)
        self.night_duration_spin.setValue(self.settings.night_duration)
        self.night_duration_spin.setMinimumWidth(75)

        # night end (calculated)
        self.night_end_label = QLabel()

        # connect signals to update night end
        self.night_begin_spin.valueChanged.connect(self._evaluate_night_end)
        self.night_duration_spin.valueChanged.connect(self._evaluate_night_end)
        self._evaluate_night_end()

        # row layout
        night_row = QHBoxLayout()
        night_row.addStretch(1)
        night_row.addWidget(QLabel("Begin (h):"))
        night_row.addWidget(self.night_begin_spin)
        night_row.addStretch(1)
        night_row.addWidget(QLabel("Duration (h):"))
        night_row.addWidget(self.night_duration_spin)
        night_row.addStretch(1)
        night_row.addWidget(self.night_end_label)
        night_row.addStretch(1)

        form.addRow("<b>Nights</b>", night_row)

        #######################################
        #   UTC TIME ZONE   #
        #######################################
        # utc_offset
        self.utc_offset_spin = QDoubleSpinBox()
        self.utc_offset_spin.setToolTip(
            "Define the UTC offset in hours for correct timezone conversion.\n"
            "For example, +1 for Paris, +9 for Tokyo or +5.75 for Kathmandu."
        )
        self.utc_offset_spin.setRange(-12.0, 14.0)
        self.utc_offset_spin.setValue(self.settings.utc_offset)
        self.utc_offset_spin.setMinimumWidth(75)

        utc_row = QHBoxLayout()
        utc_row.addStretch(1)
        utc_row.addWidget(QLabel("UTC offset (h):"))
        utc_row.addWidget(self.utc_offset_spin)
        utc_row.addStretch(1)

        form.addRow("<b>Time Zone</b>", utc_row)
        form.addRow(self.Qhline())

        #######################################
        #   ANALYSIS LIMITS (start, end)   #
        #######################################

        # processing_limits (start)
        if self.settings.processing_limits[0] is None:
            start = None
        elif isinstance(self.settings.processing_limits[0], pd.Timestamp):
            start = self.settings.processing_limits[0].isoformat(
                sep=" ", timespec="seconds"
            )
        else:
            start = str(self.settings.processing_limits[0])
        self.start_edit = QLineEdit(start)
        self.start_edit.setToolTip(
            "Can be either a FRAMENUMBER (integer) "
            "or a TIMESTAMP (YYYY-MM-DD HH:MM:SS)"
        )
        self.start_edit.setPlaceholderText("first frame")
        self.start_edit.setMinimumHeight(30)

        # processing_limits (end)
        if self.settings.processing_limits[1] is None:
            end = None
        elif isinstance(self.settings.processing_limits[1], pd.Timestamp):
            end = self.settings.processing_limits[1].isoformat(
                sep=" ", timespec="seconds"
            )
        else:
            end = str(self.settings.processing_limits[1])
        self.end_edit = QLineEdit(end)
        self.end_edit.setToolTip(
            "Can be either a FRAMENUMBER (integer) "
            "or a TIMESTAMP (YYYY-MM-DD HH:MM:SS)"
        )
        self.end_edit.setPlaceholderText("last frame")
        self.end_edit.setMinimumHeight(30)

        # row layout
        limits_row = QHBoxLayout()
        limits_row.addWidget(QLabel("Start:"))
        limits_row.addWidget(self.start_edit)
        limits_row.addWidget(QLabel("End:"))
        limits_row.addWidget(self.end_edit)

        # timestamp format example
        example_label = QLabel(
            "either a FRAMENUMBER or a TIMESTAMP (e.g. YYYY-MM-DD HH:MM:SS)"
        )
        example_label.setStyleSheet(
            "font-size: 12px; color: #666; font-style: italic;"
        )

        limits_infos_row = QHBoxLayout()
        limits_infos_row.addWidget(
            example_label, alignment=Qt.AlignmentFlag.AlignHCenter
        )

        # row layout
        form.addRow("<b>Time limits</b>", limits_row)
        form.addRow(limits_infos_row)
        form.addRow(self.Qhline())

        #######################################
        #   SETTINGS BUTTONS   #
        #######################################
        btn_style = get_btn_style(size=13)

        # load settings
        self.load_settings_btn = QPushButton("Load settings")
        self.load_settings_btn.setToolTip("Load settings from a JSON file.")
        self.load_settings_btn.setStyleSheet(btn_style)
        self.load_settings_btn.setFixedWidth(120)
        self.load_settings_btn.clicked.connect(self.on_load_settings)

        # save settings
        self.save_settings_btn = QPushButton("Save settings")
        self.save_settings_btn.setToolTip(
            "Save current settings to a JSON file."
        )
        self.save_settings_btn.setStyleSheet(btn_style)
        self.save_settings_btn.setFixedWidth(120)
        self.save_settings_btn.clicked.connect(self.on_save_settings)

        # set default settings
        self.default_settings_btn = QPushButton("Define as default")
        self.default_settings_btn.setToolTip(
            "Save current settings as default."
        )
        self.default_settings_btn.setStyleSheet(btn_style)
        self.default_settings_btn.setFixedWidth(120)
        self.default_settings_btn.clicked.connect(self.on_default_settings)

        # row layout
        settings_row = QHBoxLayout()
        settings_row.addStretch(1)
        settings_row.addWidget(self.load_settings_btn)
        settings_row.addWidget(self.save_settings_btn)
        settings_row.addWidget(self.default_settings_btn)
        settings_row.addStretch(1)

        form.addRow(settings_row)
        form.addRow(self.Qhline())

        #######################################
        #   VALIDATION BUTTONS   #
        #######################################
        # process
        btn_style = get_btn_style(size=15, bold=True, bg_color="#1976D2")
        ok_btn = QPushButton("Process")
        ok_btn.setFixedWidth(100)
        ok_btn.setStyleSheet(btn_style)
        ok_btn.clicked.connect(self.on_accept)

        # cancel
        btn_style = get_btn_style(size=15, bold=True)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setFixedWidth(100)
        cancel_btn.setStyleSheet(btn_style)
        cancel_btn.clicked.connect(self.on_reject)

        # row layout
        validation_row = QHBoxLayout()
        validation_row.addStretch(1)
        validation_row.addWidget(ok_btn)
        validation_row.addWidget(cancel_btn)
        validation_row.addStretch(1)

        form.addRow(validation_row)

        self.setLayout(form)
        ok_btn.setFocus()
        self._update_ui_from_settings()

    #######################################
    #   UI x Settings   #
    #######################################

    def _update_ui_from_settings(self):
        """Update UI elements based on LMT-EYE settings."""
        settings = self.settings.get_as_str_dict()

        self.start_edit.setText(settings["processing_limits"][0])
        self.end_edit.setText(settings["processing_limits"][1])
        self.output_folder_edit.setText(settings["output_folder"])

        selected_known_events = self.get_selected_known_events()
        custom_events = self.settings.events - selected_known_events
        self.custom_event_edit.setText(", ".join(custom_events))

        self.animal_type_box.setCurrentText(self.settings.animal_type.name)
        self.flickering_cb.setChecked(self.settings.filter_flickering)
        self.stop_cb.setChecked(self.settings.filter_stop)
        self.time_window_frames.setValue(self.settings.time_window)
        self._on_time_frames_changed()  # to update minutes accordingly
        self.process_window_frames.setValue(self.settings.processing_window)
        self._on_process_frames_changed()  # to update hours accordingly
        self.bin_rounding_cb.setChecked(self.settings.bin_rounding)
        self.fps_spin.setValue(self.settings.fps)
        self.night_begin_spin.setValue(self.settings.night_begin)
        self.night_duration_spin.setValue(self.settings.night_duration)
        self.rebuild_box.setChecked(self.settings.rebuild_events)
        self.utc_offset_spin.setValue(self.settings.utc_offset)

    def _update_settings_from_ui(self):
        """Update LMT-EYE settings based on current UI values."""
        self.settings.output_folder = (
            Path(self.output_folder_edit.text())
            if self.output_folder_edit.text()
            else None
        )
        self.settings.animal_type = AnimalType[
            self.animal_type_box.currentText()
        ]
        self.settings.filter_flickering = self.flickering_cb.isChecked()
        self.settings.filter_stop = self.stop_cb.isChecked()
        self.settings.time_window = self.time_window_frames.value()
        self.settings.processing_window = self.process_window_frames.value()
        self.settings.fps = self.fps_spin.value()
        self.settings.night_begin = self.night_begin_spin.value()
        self.settings.night_duration = self.night_duration_spin.value()
        self.settings.rebuild_events = self.rebuild_box.isChecked()
        self.settings.bin_rounding = self.bin_rounding_cb.isChecked()
        self.settings.utc_offset = self.utc_offset_spin.value()
        self._update_custom_events()

        start_text = self.start_edit.text().strip()
        if not start_text:
            start = None
        elif start_text.isdigit():
            start = int(start_text)
        else:
            try:
                start = pd.Timestamp(start_text)
            except:
                print("Invalid timestamp format. Setting start to None.")
                start = None

        end_text = self.end_edit.text()
        if not end_text:
            end = None
        elif end_text.isdigit():
            end = int(end_text)
        else:
            try:
                end = pd.Timestamp(end_text)
            except:
                print("Invalid timestamp format. Setting end to None.")
                end = None

        limits = (start, end)

        self.settings.processing_limits = limits

    #######################################
    #   UPDATE FUNCTIONS   #
    #######################################

    def _clamp_time_window_values(self, frames: int):
        """Clamp time window frames and update minutes accordingly."""
        fpm = self.fps_spin.value() * 60  # frames per minute
        minutes = frames / fpm

        min_frames = 1  # 1 frame
        max_frames = 7 * 24 * 60 * fpm  # 7 days

        if frames < min_frames:
            frames = min_frames
            minutes = frames / fpm

        if frames > max_frames:
            frames = max_frames
            minutes = frames / fpm

        self.time_window_frames.setValue(frames)
        self.time_window_minutes.setValue(minutes)

    def _on_time_frames_changed(self):
        """Handle changes in time window frames spinbox."""
        self.time_window_frames.blockSignals(True)
        self.time_window_minutes.blockSignals(True)

        frames = self.time_window_frames.value()
        self._clamp_time_window_values(frames)

        self.time_window_frames.blockSignals(False)
        self.time_window_minutes.blockSignals(False)

    def _on_time_minutes_changed(self):
        """Handle changes in time window minutes spinbox."""
        self.time_window_frames.blockSignals(True)
        self.time_window_minutes.blockSignals(True)

        fpm = self.fps_spin.value() * 60  # frames per minute
        minutes = self.time_window_minutes.value()
        frames = int(minutes * fpm)
        self._clamp_time_window_values(frames)

        self.time_window_frames.blockSignals(False)
        self.time_window_minutes.blockSignals(False)

    def _clamp_process_window_values(self, frames: int):
        """Clamp processing window frames and update minutes accordingly."""
        fph = self.fps_spin.value() * 60 * 60  # frames per hour
        hours = frames / fph

        min_frames = fph  # 1 hour
        max_frames = 7 * 24 * fph  # 7 days

        if frames < min_frames:
            frames = min_frames
            hours = frames / fph

        if frames > max_frames:
            frames = max_frames
            hours = frames / fph

        self.process_window_frames.setValue(frames)
        self.process_window_hours.setValue(hours)

    def _on_process_frames_changed(self):
        self.process_window_frames.blockSignals(True)
        self.process_window_hours.blockSignals(True)

        frames = self.process_window_frames.value()
        self._clamp_process_window_values(frames)

        self.process_window_frames.blockSignals(False)
        self.process_window_hours.blockSignals(False)

    def _on_process_hours_changed(self):
        self.process_window_frames.blockSignals(True)
        self.process_window_hours.blockSignals(True)

        fph = self.fps_spin.value() * 60 * 60  # frames per hour
        hours = self.process_window_hours.value()
        frames = int(round(hours * fph))
        self._clamp_process_window_values(frames)

        self.process_window_frames.setValue(frames)
        self.process_window_frames.blockSignals(False)
        self.process_window_hours.blockSignals(False)

    def _on_fps_changed(self):
        # When FPS changes, update both minutes <-> frames for both windows
        self._on_time_frames_changed()
        self._on_process_frames_changed()

    def _evaluate_night_end(self):
        begin = self.night_begin_spin.value()
        duration = self.night_duration_spin.value()
        end = (begin + duration) % 24
        self.night_end_label.setText(f"End: {end} h")

    def _update_custom_events(self):
        """Update settings.events from the UI by keeping only known events and
        current custom events."""
        selected_known_events = self.get_selected_known_events()
        custom_events = self.get_custom_events_from_ui()
        self.settings.events = selected_known_events | custom_events

    #######################################
    #   UTILS FUNCTIONS   #
    #######################################

    def get_custom_events_from_ui(self):
        """Get the custom events from UI as a set."""
        custom_list = self.custom_event_edit.text().split(",")
        custom_set = {event.strip() for event in custom_list if event.strip()}
        return custom_set

    def get_selected_known_events(self):
        """Get all events present in both settings.events and ALL_EVENTS.
        It corresponds to the events that are selected in the UI (through
        EventSelectionDialog) and are known by the app (i.e. for which the
        app has a specific analysis implemented).
        """
        known_events = set(ALL_EVENTS.keys())
        selected_events = self.settings.events & known_events
        return selected_events

    def on_select_events(self):
        dlg = EventSelectionDialog(self, self.settings.events)
        if dlg.exec():
            self.settings.events = dlg.selected_events
            self._update_custom_events()

    def on_select_area(self):
        dlg = AreaSelectionDialog(self, self.settings.analysis_area)
        if dlg.exec():
            self.settings.analysis_area = dlg.selected_area
            self._update_area_label()

    def _update_area_label(self):
        area = self.settings.analysis_area
        if area is None:
            text = "No area filtering."
        else:
            x_min, y_min, x_max, y_max = area
            text = (
                f"Area from ({x_min}, {y_min}) "
                f"to ({x_max}, {y_max}) in <i>cm</i>."
            )
        self.selected_area_label.setText(text)

    def select_output_folder(self):
        """Open a dialog to choose output folder."""
        folder_str = QFileDialog.getExistingDirectory(
            self, "Select Output Folder"
        )
        if folder_str:
            self.output_folder_edit.setText(folder_str)
        else:
            self.output_folder_edit.setText(None)

    def on_save_settings(self):
        """Save current settings from UI to a JSON file."""
        save_str, _ = QFileDialog.getSaveFileName(
            self,
            "Select Settings File",
            str(SettingsWindow.SAVING_PATH),
            "JSON Files (*.json)",
        )
        save_path = Path(save_str) if save_str else None
        if save_path is None:
            print("No file selected.")
            return
        self._update_settings_from_ui()
        self.settings.save(save_path)

    def on_load_settings(self):
        """Load settings from a JSON file and update UI."""
        load_str, _ = QFileDialog.getOpenFileName(
            self,
            "Select Settings File",
            str(SettingsWindow.SAVING_PATH),
            "JSON Files (*.json)",
        )
        load_path = Path(load_str) if load_str else None
        if load_path is None:
            print("No file selected.")
            return
        self.settings.load(load_path)
        self._update_ui_from_settings()

    def on_default_settings(self):
        """Save current settings as the default settings
        (default_settings.json in the same directory)."""
        save_path = SettingsWindow.SAVING_PATH / "default_settings.json"
        self._update_settings_from_ui()
        self.settings.save(save_path)

    def on_accept(self):
        """Update settings and accept dialog."""
        self._update_settings_from_ui()
        self.accept()

    def on_reject(self):
        """Update settings and reject dialog."""
        self._update_settings_from_ui()
        self.reject()

    def Qhline(self):
        """Utility function to create a horizontal line separator."""
        hline = QFrame()
        hline.setFrameShape(QFrame.Shape.HLine)
        hline.setFrameShadow(QFrame.Shadow.Sunken)
        hline.setFixedHeight(1)
        return hline


def exception_hook(type_, value, tb):
    """Global exception hook to catch unhandled exceptions and display them in
    a message box."""
    traceback.print_exception(type_, value, tb)
    msg = QMessageBox()
    msg.setIcon(QMessageBox.Icon.Critical)
    msg.setWindowTitle("Application Error")
    msg.setText("An unexpected error occurred.")
    msg.setDetailedText("".join(traceback.format_exception(type_, value, tb)))
    msg.exec()


if __name__ == "__main__":

    try:
        # set windows taskbar icon (must be before QApplication)
        from ctypes import windll

        windll.shell32.SetCurrentProcessExplicitAppUserModelID(
            "lmt.lmt-eye.app"
        )
    except ImportError:
        # not on windows, do nothing
        pass

    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(True)
    app.setApplicationVersion(APP_VERSION)
    app.setWindowIcon(QIcon(str(ICON_PATH)))
    app.setApplicationName("LMT-EYE")

    sys.excepthook = exception_hook

    main_window = LMTEYEApp()

    main_window.show()
    sys.exit(app.exec())
