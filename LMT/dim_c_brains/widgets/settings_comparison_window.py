from pathlib import Path

from PyQt6.QtWidgets import (
    QComboBox,
    QDialog,
    QFileDialog,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSpinBox,
    QWidget,
)

from dim_c_brains.scripts.settings import ComparisonSettings
from dim_c_brains.widgets.pyqt6_tools import get_btn_style


class ComparisonSettingsWindow(QDialog):
    """Dialog to edit LMT database analyzer settings."""

    def __init__(self, parent: QWidget | None, analyses_path: list[Path]):
        """Initialize the settings window by loading default settings."""
        super().__init__(parent)
        self.setWindowTitle("LMT-EYE - Comparison Settings")
        self.settings = ComparisonSettings(analyses_path)
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
            "same folder as first selected analysis by default"
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
        #   Comparator Selection   #
        #######################################

        # select comparison parameter button
        cc = self.settings.get_common_columns()
        self.comparator_box = QComboBox()
        self.comparator_box.setToolTip("Select a comparator for the analysis.")
        self.comparator_box.addItems(cc)
        self.comparator_box.setCurrentText("RFID")

        # row layout
        comparator_row = QHBoxLayout()
        comparator_row.addWidget(self.comparator_box)
        comparator_row.addStretch(1)

        form.addRow("<b>Comparator</b>", comparator_row)
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

    #######################################
    #   UTILS FUNCTIONS   #
    #######################################

    def select_output_folder(self):
        """Open a dialog to choose output folder."""
        folder_str = QFileDialog.getExistingDirectory(
            self, "Select Output Folder"
        )
        if folder_str:
            self.output_folder_edit.setText(folder_str)
        else:
            self.output_folder_edit.setText(None)

    def _evaluate_night_end(self):
        begin = self.night_begin_spin.value()
        duration = self.night_duration_spin.value()
        end = (begin + duration) % 24
        self.night_end_label.setText(f"End: {end} h")

    def _update_settings_from_ui(self):
        """Update LMT-EYE settings based on current UI values."""
        self.settings.report_color = self.comparator_box.currentText()
        self.settings.night_begin = self.night_begin_spin.value()
        self.settings.night_duration = self.night_duration_spin.value()
        self.settings.output_folder = (
            Path(self.output_folder_edit.text())
            if self.output_folder_edit.text()
            else None
        )

    def on_accept(self):
        """Update settings and accept dialog."""
        self._update_settings_from_ui()
        self.accept()

    def on_reject(self):
        """Update settings and reject dialog."""
        self.reject()

    def Qhline(self):
        """Utility function to create a horizontal line separator."""
        hline = QFrame()
        hline.setFrameShape(QFrame.Shape.HLine)
        hline.setFrameShadow(QFrame.Shadow.Sunken)
        hline.setFixedHeight(1)
        return hline
