"""
@author: xmousset
"""

import sys
from pathlib import Path

################
#   APP INFO   #
################
# command for executable creation (run in terminal at project root):
# pyinstaller -p LMT --onefile --icon=LMT/dim_c_brains/res/lmt_eye_icon.png --add-data "LMT/dim_c_brains/res/lmt_eye_icon.png;dim_c_brains/res" --add-data "LMT/dim_c_brains/res/template;dim_c_brains/res/template" --add-data "LMT/dim_c_brains/res/assets;dim_c_brains/res/assets" --add-data "LMT/dim_c_brains/res/mouse_run.gif;dim_c_brains/res" LMT/dim_c_brains/lmt_eye_app.py

APP_VERSION = "1.4"
APP_RELEASE = "2026-04-13"

if hasattr(sys, "_MEIPASS"):
    # in app
    print("Starting LMT-EYE...")
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
from PyQt6.QtCore import QObject, QRunnable, QThreadPool, pyqtSignal, pyqtSlot
from PyQt6.QtWidgets import (
    QApplication,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QMainWindow,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from dim_c_brains.scripts.db_analyzer import DatabaseAnalyzer
from dim_c_brains.scripts.analyses_comparator import AnalysesComparator

from dim_c_brains.scripts.settings import ComparisonSettings
from dim_c_brains.widgets.settings_analysis_window import (
    AnalysisSettingsWindow,
)
from dim_c_brains.widgets.settings_comparison_window import (
    ComparisonSettingsWindow,
)

from dim_c_brains.widgets.pyqt6_tools import YesNoQuestion, get_btn_style
from dim_c_brains.widgets.sql_modifications import UpdateDatabaseInfo


class LMTEYEApp(QMainWindow):
    """Main application class for LMT-EYE."""

    def __init__(self):
        """Initialize the LMT-EYE application."""
        super().__init__()
        self.setWindowTitle("LMT-EYE - v" + APP_VERSION)
        self.setFixedSize(550, 400)
        self._init_ui()

    def _init_ui(self):
        self.database_analysis = DatabaseAnalysisWidget()
        self.compare_analysis = AnalysesComparisonWidget()

        self.stacked = QStackedWidget()
        self.stacked.addWidget(self.database_analysis)
        self.stacked.addWidget(self.compare_analysis)
        self.setCentralWidget(self.stacked)

        menu = self.menuBar()
        if menu is None:
            raise RuntimeError("Menu bar error.")

        switch_menu = menu.addMenu("Menu")
        if switch_menu is None:
            raise RuntimeError("Switch menu error.")
        switch_menu.addAction("Analysis creation", lambda: self.change_ui(0))
        switch_menu.addAction("Analysis comparison", lambda: self.change_ui(1))

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


class DatabaseAnalysisWidget(QWidget):
    """Database Analysis Widget for LMT-EYE.
    It allows to load a database, rebuild events and create reports.
    """

    def __init__(self):
        """Initialize the database analysis widget."""
        super().__init__()
        self.database_path: Path | None = None
        self.threadpool = QThreadPool()
        self.threadpool.setMaxThreadCount(1)
        self.first_load = True
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
            infos = DatabaseAnalyzer.get_informations(self.database_path)

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

    def modify_btns_after_first_load(self):
        """Modify buttons style after the first database is loaded."""
        if self.first_load:
            btn_style = get_btn_style(size=15, bold=True, bg_color="#1976D2")
            self.update_info_btn.setStyleSheet(btn_style)
            self.continue_btn.setStyleSheet(btn_style)
            self.first_load = False

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

        self.modify_btns_after_first_load()

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

        dlg = AnalysisSettingsWindow(self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            settings = dlg.settings
        else:
            print("Process cancelled.")
            return

        analyzer = DatabaseAnalyzer(self.database_path, settings)

        progress_bar = DbAnalysisProgressBar(
            self, database_name=self.database_path.stem
        )

        worker = AnalysisWorker(analyzer)
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

    def handle_open_analysis(self, analyzer: DatabaseAnalyzer | None):
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
                analyzer.open_results()
        else:
            QMessageBox.critical(self, "Error", "Analysis failed.")


class AnalysisWorkerSignals(QObject):
    """Manage signals from a running worker thread."""

    finished = pyqtSignal(bool)
    analyzer = pyqtSignal(DatabaseAnalyzer)
    rebuild_progress = pyqtSignal(int, int)  # current, max
    analyse_progress = pyqtSignal(int, int)  # current, max


class AnalysisWorker(QRunnable):
    def __init__(self, data_analyzer: DatabaseAnalyzer):
        super().__init__()
        self.data_analyzer = data_analyzer
        self.signals = AnalysisWorkerSignals()

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
            print(f"Error in AnalysisWorker: {e}")
            traceback.print_exc()
            self.signals.finished.emit(False)


class DbAnalysisProgressBar(QDialog):
    """Dialog to show progress during database analysis."""

    def __init__(
        self,
        parent: QWidget | None = None,
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
            label_text = f"{database_name}\nis being processed. Please wait."

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


class AnalysesComparisonWidget(QWidget):
    """Analysis Comparison Widget for LMT-EYE.
    It allows to select one or multiple database analyses, compare them
    according to set animal information and create comparison reports.
    """

    def __init__(self):
        """Initialize the analysis comparison widget."""
        super().__init__()
        self.analyses_path: list[Path] = []
        self.threadpool = QThreadPool()
        self.threadpool.setMaxThreadCount(1)
        self.first_load = True
        self._init_ui()

    def _init_ui(self):
        """Initialize the UI elements of the analysis comparison window."""
        main_layout = QVBoxLayout()

        #######################################
        #   Analyses informations   #
        #######################################
        self.info_label = QLabel()
        self.info_label.setTextFormat(Qt.TextFormat.RichText)
        self.info_label.setText("<b>No loaded analyses.</b>")

        analyses_info_row = QHBoxLayout()
        analyses_info_row.addWidget(self.info_label)
        main_layout.addLayout(analyses_info_row)

        #######################################
        #   Buttons row   #
        #######################################

        btn_style = get_btn_style(size=15, bold=True, bg_color="#1976D2")

        # add analysis button
        self.add_analysis_btn = QPushButton("Add")
        self.add_analysis_btn.setStyleSheet(btn_style)
        self.add_analysis_btn.setFixedSize(100, 50)
        self.add_analysis_btn.clicked.connect(self.on_load_single_analysis)

        btn_style = get_btn_style(size=15, bold=True)

        # remove analysis button
        self.remove_analyses_btn = QPushButton("Remove")
        self.remove_analyses_btn.setStyleSheet(btn_style)
        self.remove_analyses_btn.setFixedSize(100, 50)
        self.remove_analyses_btn.clicked.connect(self.on_remove_analysis)

        # continue button
        self.continue_btn = QPushButton("Continue")
        self.continue_btn.setStyleSheet(btn_style)
        self.continue_btn.setFixedSize(150, 50)
        self.continue_btn.clicked.connect(self.on_continue)

        # row layout
        buttons_row = QHBoxLayout()
        buttons_row.addStretch(1)
        buttons_row.addWidget(self.add_analysis_btn)
        buttons_row.addWidget(self.remove_analyses_btn)
        buttons_row.addWidget(self.continue_btn)
        buttons_row.addStretch(1)

        main_layout.addLayout(buttons_row)

        self.setLayout(main_layout)

    def update_analyses_info(self):
        """Update analyses information displayed in the main window."""

        common_columns = ComparisonSettings.get_common_columns_from_list(
            self.analyses_path
        )

        info_html = f"""
            <table style='font-size:13px;'>
            <tr>
                <td><b>Number of loaded analyses:</b></td>
                <td>{len(self.analyses_path)}</td>
            </tr>
            <br>
            <tr>
                <td><b>Available Comparators:</b></td>
                <td>{", ".join(sorted(common_columns))}</td>
            </tr>
            </table>
        """
        self.info_label.setText(info_html)

    def show_invalid_folder(
        self,
        path: Path,
        multiple_analyses: bool = False,
    ):
        """Show a warning message for an invalid analysis."""
        if multiple_analyses:
            msg = (
                "The selected folder <b>DOES NOT</b> contain at least one "
                "valid analysis."
            )
        else:
            msg = (
                f"The selected folder ({path.name}) <b>IS NOT</b> a valid "
                "analysis."
            )
        QMessageBox.warning(
            self,
            "Invalid Analysis",
            msg,
        )

    def modify_btns_after_first_load(self):
        """Modify buttons style after the first analysis is loaded."""
        if self.first_load:
            btn_style = get_btn_style(size=15, bold=True, bg_color="#1976D2")
            self.remove_analyses_btn.setStyleSheet(btn_style)
            self.continue_btn.setStyleSheet(btn_style)
            self.first_load = False

    def on_load_single_analysis(self):
        """Launches a file dialog for loading a single analysis."""
        dir_path = QFileDialog.getExistingDirectory(
            self,
            "Select Analyses Directory",
            str(Path.home()),
            QFileDialog.Option.ShowDirsOnly,
        )
        if not dir_path:
            return

        dir_path = Path(dir_path)
        if not (dir_path / ComparisonSettings.MAIN_TABLE).exists():
            self.show_invalid_folder(dir_path)
            return

        self.analyses_path.append(dir_path)
        self.update_analyses_info()

        self.modify_btns_after_first_load()

    def on_load_multiple_analyses(self):
        """Launches a file dialog for loading multiple analyses."""
        dir_path = QFileDialog.getExistingDirectory(
            self,
            "Select Analyses Directory",
            str(Path.home()),
            QFileDialog.Option.ShowDirsOnly,
        )
        if not dir_path:
            return

        dir_path = Path(dir_path)
        analyses_path = [
            dir
            for dir in dir_path.iterdir()
            if dir.is_dir() and (dir / ComparisonSettings.MAIN_TABLE).exists()
        ]
        if not analyses_path:
            self.show_invalid_folder(dir_path, multiple_analyses=True)
            return

        self.analyses_path.extend(analyses_path)
        self.update_analyses_info()

        self.modify_btns_after_first_load()

    def on_remove_analysis(self):
        """Remove the last loaded analysis."""
        if not self.analyses_path:
            QMessageBox.information(
                self,
                "No Analysis to Remove",
                "No analysis available for removal.",
            )
            return
        analysis_dict = {path.name: path for path in self.analyses_path}
        analysis_name, ok = QInputDialog.getItem(
            self,
            "Remove Analysis",
            "Select analysis to remove:",
            sorted(analysis_dict.keys()),
            0,
            False,
        )
        if not ok or not analysis_name:
            return
        self.analyses_path.remove(analysis_dict[analysis_name])
        print(f"Removed analysis: {analysis_name}")
        self.update_analyses_info()

    def warning_message_load_analyses(self):
        """Check if analyses are loaded, and show a warning if not."""
        QMessageBox.warning(
            self,
            "No Analyses",
            "You must load analyses before.",
        )

    def on_continue(self):
        """Rebuild analyses then analyse it."""
        if not self.analyses_path:
            self.warning_message_load_analyses()
            return

        settings_window = ComparisonSettingsWindow(self, self.analyses_path)
        if settings_window.exec() == QDialog.DialogCode.Accepted:
            settings = settings_window.settings
        else:
            print("Process cancelled.")
            return

        progress_bar = AnalysesComparisonProgressBar(
            self,
            report_color=settings.report_color,
            analyses_path=settings.analyses_path,
        )

        data_comparator = AnalysesComparator(settings)

        worker = ComparisonWorker(data_comparator)
        worker.signals.comparison_progress.connect(
            progress_bar.set_comparison_progress
        )
        worker.signals.comparator.connect(self.handle_open_analysis)
        worker.signals.finished.connect(progress_bar.progression_finished)

        progress_bar.show()
        self.threadpool.start(worker)

        print(
            f"Comparison process for {len(self.analyses_path)} "
            "analyses queued/started."
        )

    def handle_open_analysis(self, comparator: AnalysesComparator | None):
        """Ask user if they want to open the processed results when the
        analysis is finished.
        Automatically close the window after 5 minutes if the user does not
        answer."""
        if comparator is not None:
            print("*** PROCESS FINISHED ***")

            output = comparator.get_output_folder()
            text = f"""
            LMT-EYE has finished to compare the {len(self.analyses_path)}
            analyses. Results are saved in:\n
            {output}\n
            Do you want to open the results ?
            """
            dlg = YesNoQuestion(
                parent=self,
                question=text,
                timeout_s=300,  # 5 minutes
            )
            if dlg.exec():
                comparator.open_results()
        else:
            QMessageBox.critical(self, "Error", "Analysis failed.")


class ComparisonWorkerSignals(QObject):
    """Manage signals from a running worker thread."""

    finished = pyqtSignal(bool)
    comparator = pyqtSignal(AnalysesComparator)
    comparison_progress = pyqtSignal(int, int)  # current, max


class ComparisonWorker(QRunnable):
    def __init__(self, data_comparator: AnalysesComparator):
        super().__init__()
        self.data_comparator = data_comparator
        self.signals = ComparisonWorkerSignals()

    @pyqtSlot()
    def run(self):
        try:
            self.data_comparator.compare_analyses(
                progress_callback=self.signals.comparison_progress.emit
            )
            self.signals.finished.emit(True)
            self.signals.comparator.emit(self.data_comparator)

        except Exception as e:
            print(f"Error in ComparisonWorker: {e}")
            traceback.print_exc()
            self.signals.finished.emit(False)


class AnalysesComparisonProgressBar(QDialog):
    """Dialog to show progress during analyses comparison."""

    def __init__(
        self,
        parent: QWidget | None = None,
        title="Comparison progression",
        report_color: str = "RFID",
        analyses_path: list[Path] = [],
    ):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setModal(False)
        self.setFixedSize(350, 220)
        self._init_ui(report_color, analyses_path)

    def _init_ui(self, report_color: str, analyses_path: list[Path]):
        form = QFormLayout()

        if not analyses_path:
            label_text = f"Processing using {report_color}. Please wait."
        else:
            label_text = (
                f"{len(analyses_path)} analyses are being processed.\n"
                f"{report_color} is the comparator.\nPlease wait."
            )

        process_label = QLabel(label_text)
        process_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        process_label.setStyleSheet("font-size: 15px;")

        movie_label = QLabel()
        movie_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.movie = QMovie(str(GIF_PATH))
        if self.movie.isValid():
            movie_label.setMovie(self.movie)
            self.movie.start()

        self.comparison_progress = QProgressBar()
        self.comparison_progress.setMinimum(0)

        form.addRow(process_label)
        form.addRow(movie_label)
        form.addRow("<b>Comparison Progress</b>", self.comparison_progress)

        self.setLayout(form)

    def set_comparison_progress(self, value, maximum):
        self.comparison_progress.setMaximum(maximum)
        self.comparison_progress.setValue(value)

    def progression_finished(self, is_finished: bool):
        if is_finished:
            self.accept()
        else:
            self.reject()


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
