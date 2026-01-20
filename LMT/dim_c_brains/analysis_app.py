"""
@creation: 15-01-2026
@author: Xavier MD
"""

import sys
import sqlite3
from pathlib import Path
from typing import Literal

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import (
    QApplication,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
    QDialog,
)

lmt_analysis_path = Path(__file__).parent.parent
sys.path.append(lmt_analysis_path.as_posix())

from dim_c_brains.scripts.pyqt6_tools import YesNoQuestion, UserSelector
from dim_c_brains.scripts.data_extractor import DataFrameConstructor
from lmtanalysis.Measure import oneMinute


class GenericAnalysisApp(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

        self.user_answer: bool | None = None
        self.user_selected_path: Path | None = None

    def init_ui(self):
        app.setWindowIcon(QIcon("LMT/dim_c_brains/res/app_icon.png"))
        self.setWindowTitle("Generic LMT Analysis App using PyQt6")
        self.setFixedSize(500, 350)
        self.ask_selection("file")

    def ask_selection(self, type: Literal["file", "folder"]):
        self.hide()
        if type == "file":
            selector = UserSelector("file", self)
        elif type == "folder":
            selector = UserSelector("folder", self)
        else:
            raise ValueError("Invalid selection type. Use 'file' or 'folder'.")
        selector.exec()
        self.user_selected_path = selector.selected_path
        print(f"User selected path: {self.user_selected_path}")
        if self.user_selected_path is not None:
            self.display_experiment_info(self.user_selected_path)
        else:
            QMessageBox.warning(
                self,
                "No Selection",
                "No file or folder was selected.<br>Exiting application.",
            )
            sys.exit(0)

    def display_experiment_info(self, sqlite_path: Path):

        try:
            connection = sqlite3.connect(str(sqlite_path))
            df_creator = DataFrameConstructor(
                connection, time_window=oneMinute * 5
            )
            n_animals = len(df_creator.animal_pool.animalDictionary)
            start_time, end_time = df_creator.get_time_limits()
            duration = end_time - start_time
            start_text = start_time.strftime("%Y-%m-%d (%A) at %H:%M")

            info_text = f"<b>Experiment informations:</b><br><br>"
            info_text += f"File name: <b>{sqlite_path.stem}</b><br><br>"
            info_text += f"Number of animals: <b>{n_animals}</b><br><br>"
            info_text += f"Start time: <b>{start_text}</b><br><br>"
            info_text += (
                f"Duration: <b>"
                f"{duration.components.days} days, "
                f"{duration.components.hours} hours, "
                f"{duration.components.minutes} minutes</b>"
            )

        except Exception as e:
            info_text = (
                "<span style='color:red'><b>"
                f"Error loading experiment: {e}"
                "</b></span>"
            )

        # Main vertical layout
        main_layout = QVBoxLayout()

        # Experiment info label
        self.info_label = QLabel()
        self.info_label.setTextFormat(Qt.TextFormat.RichText)
        self.info_label.setText(info_text)
        main_layout.addWidget(self.info_label)

        # Rebuild info and button row
        rebuild_row = QHBoxLayout()
        # Left: rebuild info (placeholder for now)
        self.rebuild_info_label = QLabel("Database rebuilt: <b>Unknown</b>")
        rebuild_row.addWidget(
            self.rebuild_info_label, alignment=Qt.AlignmentFlag.AlignLeft
        )
        # Right: rebuild button
        self.rebuild_btn = QPushButton("Rebuild Database")
        self.rebuild_btn.clicked.connect(self.on_rebuild_clicked)
        rebuild_row.addWidget(
            self.rebuild_btn, alignment=Qt.AlignmentFlag.AlignRight
        )
        main_layout.addLayout(rebuild_row)

        # Continue button (below)
        self.continue_btn = QPushButton("Continue")
        self.continue_btn.setStyleSheet(
            "font-size: 15px; font-weight: bold; background-color: #388e3c; "
            "color: white; border-radius: 6px; padding: 8px 0;"
        )
        self.continue_btn.setFixedWidth(250)
        self.continue_btn.clicked.connect(self.on_continue_clicked)
        main_layout.addWidget(
            self.continue_btn, alignment=Qt.AlignmentFlag.AlignHCenter
        )

        self.setLayout(main_layout)
        self.show()

    def on_rebuild_clicked(self):
        # Placeholder for rebuild logic
        QMessageBox.information(
            self, "Rebuild", "Rebuild database logic goes here."
        )

    def on_continue_clicked(self):
        self.analysis_window = AnalysisSelectionDialog(self)
        self.analysis_window.show()


class AnalysisSelectionDialog(QDialog):
    """PyQt6 Dialog to select which analysis to perfom."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Select Analysis to Perform")
        self.setFixedSize(400, 250)
        layout = QVBoxLayout()

        label = QLabel("Select which analysis to perform:")
        label.setStyleSheet("font-size: 15px; font-weight: bold;")
        layout.addWidget(label)

        # Example: checkboxes for analysis options (customize as needed)
        from PyQt6.QtWidgets import QCheckBox

        self.analysis_options = []
        for text in ["Activity Analysis", "Event Analysis", "Custom Analysis"]:
            cb = QCheckBox(text)
            layout.addWidget(cb)
            self.analysis_options.append(cb)

        # Proceed button
        self.proceed_btn = QPushButton("Proceed")
        self.proceed_btn.setStyleSheet(
            "font-size: 15px; font-weight: bold; background-color: #1976D2; color: white; border-radius: 6px; padding: 8px 0;"
        )
        self.proceed_btn.clicked.connect(self.on_proceed_clicked)
        layout.addWidget(
            self.proceed_btn, alignment=Qt.AlignmentFlag.AlignHCenter
        )

        self.setLayout(layout)

    def on_proceed_clicked(self):
        # Show Yes/No confirmation dialog
        yn = YesNoQuestion(
            "Are you sure you want to proceed with the selected analysis?",
            self,
        )
        result = yn.exec()
        if result == QDialog.DialogCode.Accepted:
            QMessageBox.information(
                self, "Analysis", "Analysis will be performed."
            )
            self.accept()
        else:
            QMessageBox.information(self, "Analysis", "Analysis cancelled.")

    def ask_YN_question(self, question: str):
        self.user_answer = None
        result = YesNoQuestion(question, self).exec()
        if result == QDialog.DialogCode.Accepted:
            self.user_answer = True
            print("User answered YES")
        if result == QDialog.DialogCode.Rejected:
            self.user_answer = False
            print("User answered NO")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(True)
    window = GenericAnalysisApp()
    window.show()
    sys.exit(app.exec())
