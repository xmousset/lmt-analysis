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

        # ================ OUTPUT FOLDER ================
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
        btn_style = get_btn_style(txt_color="white", bg_color="black")
        out_btn.setStyleSheet(btn_style)
        out_btn.setFixedWidth(80)
        out_btn.clicked.connect(self.select_output_folder)

        out_row = QHBoxLayout()
        out_row.addWidget(self.output_folder_edit)
        out_row.addWidget(out_btn)

        form.addRow("<b>Output Folder</b>", out_row)

        # ================ COMPARATOR ================
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

        # ================ NIGHT TIME ================

        # night_begin
        h, m = self.settings.night_begin
        self.night_begin_edit = QLineEdit(f"{h:02d}:{m:02d}")
        self.night_begin_edit.setToolTip(
            "Define when the night cycle begins (HH:MM, e.g. 20:00).\n"
            "Only used to display a shadow on graphs during night hours."
        )
        self.night_begin_edit.setFixedWidth(45)

        # night_duration
        h, m = self.settings.night_duration
        self.night_duration_edit = QLineEdit(f"{h:02d}:{m:02d}")
        self.night_duration_edit.setToolTip(
            "Define the night cycle duration (HH:MM, e.g. 12:00).\n"
            "Only used to display a shadow on graphs during night hours."
        )
        self.night_duration_edit.setFixedWidth(45)

        # night_end
        end_total_min = (
            self.settings.night_begin[0] * 60
            + self.settings.night_begin[1]
            + self.settings.night_duration[0] * 60
            + self.settings.night_duration[1]
        ) % (24 * 60)
        h, m = end_total_min // 60, end_total_min % 60
        self.night_end_edit = QLineEdit(f"{h:02d}:{m:02d}")
        self.night_end_edit.setToolTip(
            "Define when the night cycle ends (HH:MM, e.g. 08:00).\n"
            "Only used to display a shadow on graphs during night hours."
        )
        self.night_end_edit.setFixedWidth(45)

        # connect signals to update night end
        self.night_begin_edit.textChanged.connect(self._on_night_begin_changed)
        self.night_duration_edit.textChanged.connect(
            self._on_night_duration_changed
        )
        self.night_end_edit.textChanged.connect(self._on_night_end_changed)

        # row layout
        night_row = QHBoxLayout()
        night_row.addStretch(1)
        night_row.addWidget(QLabel("Begin:"))
        night_row.addWidget(self.night_begin_edit)
        night_row.addStretch(1)
        night_row.addWidget(QLabel("End:"))
        night_row.addWidget(self.night_end_edit)
        night_row.addStretch(1)
        night_row.addWidget(QLabel("Duration:"))
        night_row.addWidget(self.night_duration_edit)
        night_row.addStretch(1)

        form.addRow("<b>Night time</b>", night_row)

        # ================ VALIDATION BUTTONS ================
        # process
        btn_style = get_btn_style(txt_color="white", bg_color="green")
        ok_btn = QPushButton("Process")
        ok_btn.setFixedWidth(100)
        ok_btn.setStyleSheet(btn_style)
        ok_btn.clicked.connect(self.on_accept)

        # cancel
        btn_style = get_btn_style(txt_color="white", bg_color="red")
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

    # ================ UTILS FUNCTIONS ================

    def select_output_folder(self):
        """Open a dialog to choose output folder."""
        folder_str = QFileDialog.getExistingDirectory(
            self, "Select Output Folder"
        )
        if folder_str:
            self.output_folder_edit.setText(folder_str)
        else:
            self.output_folder_edit.setText(None)

    @staticmethod
    def _parse_time_text(text: str) -> tuple[int, int] | None:
        """Parse a time string like '18:00' or '18h00' into (int, int) for
        (hours, minutes)."""
        text = text.strip()
        if len(text) < 4:
            return None
        hours_str = text[:2]
        minutes_str = text[-2:]
        if not hours_str.isdigit() or not minutes_str.isdigit():
            return None
        h, m = int(hours_str), int(minutes_str)
        if not (0 <= h <= 23 and 0 <= m <= 59):
            return None
        return (h, m)

    def _get_night_times(self):
        """Validate night time inputs and return True if valid, False otherwise."""
        begin = self._parse_time_text(self.night_begin_edit.text())
        duration = self._parse_time_text(self.night_duration_edit.text())
        end = self._parse_time_text(self.night_end_edit.text())

        if begin is None:
            self.night_begin_edit.setStyleSheet("border: 1px solid red;")
        else:
            self.night_begin_edit.setStyleSheet(None)

        if duration is None:
            self.night_duration_edit.setStyleSheet("border: 1px solid red;")
        else:
            self.night_duration_edit.setStyleSheet(None)

        if end is None:
            self.night_end_edit.setStyleSheet("border: 1px solid red;")
        else:
            self.night_end_edit.setStyleSheet(None)

        return begin, duration, end

    def _on_night_begin_changed(self):
        begin, _, end = self._get_night_times()
        if begin is None or end is None:
            return

        begin_total_min = begin[0] * 60 + begin[1]
        end_total_min = end[0] * 60 + end[1]
        duration_total_min = (end_total_min - begin_total_min) % (24 * 60)
        duration = (duration_total_min // 60, duration_total_min % 60)
        self.night_duration_edit.blockSignals(True)
        self.night_duration_edit.setText(
            f"{duration[0]:02d}:{duration[1]:02d}"
        )
        self.night_duration_edit.blockSignals(False)

    def _on_night_duration_changed(self):
        begin, duration, _ = self._get_night_times()
        if begin is None or duration is None:
            return

        duration_total_min = duration[0] * 60 + duration[1]
        end_total_min = (begin[0] * 60 + begin[1] + duration_total_min) % (
            24 * 60
        )
        end = (end_total_min // 60, end_total_min % 60)
        self.night_end_edit.blockSignals(True)
        self.night_end_edit.setText(f"{end[0]:02d}:{end[1]:02d}")
        self.night_end_edit.blockSignals(False)

    def _on_night_end_changed(self):
        begin, _, end = self._get_night_times()
        if begin is None or end is None:
            return

        begin_total_min = begin[0] * 60 + begin[1]
        end_total_min = end[0] * 60 + end[1]
        duration_total_min = (end_total_min - begin_total_min) % (24 * 60)
        duration = (duration_total_min // 60, duration_total_min % 60)
        self.night_duration_edit.blockSignals(True)
        self.night_duration_edit.setText(
            f"{duration[0]:02d}:{duration[1]:02d}"
        )
        self.night_duration_edit.blockSignals(False)

    def _update_settings_from_ui(self):
        """Update LMT-EYE settings based on current UI values."""
        self.settings.report_color = self.comparator_box.currentText()
        begin, duration, _ = self._get_night_times()
        if begin is not None:
            self.settings.night_begin = begin
        if duration is not None:
            self.settings.night_duration = duration
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
