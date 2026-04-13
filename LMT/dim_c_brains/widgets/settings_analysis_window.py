from pathlib import Path

import pandas as pd

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDoubleSpinBox,
    QFileDialog,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from dim_c_brains.scripts.events_and_modules import ALL_EVENTS
from dim_c_brains.scripts.settings import AnalysisSettings

from dim_c_brains.widgets.pyqt6_tools import get_btn_style
from dim_c_brains.widgets.area_selection import AreaSelectionWindow
from dim_c_brains.widgets.event_selection import EventSelectionWindow

from lmtanalysis.Animal import AnimalType


class AnalysisSettingsWindow(QDialog):
    """Dialog to edit LMT database analyzer settings."""

    SAVING_PATH = Path.home() / "documents" / "LMT-EYE_settings"
    SAVING_PATH.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def load_default_settings():
        """Load default settings if available."""

        settings = AnalysisSettings()

        default_path = (
            AnalysisSettingsWindow.SAVING_PATH / "default_settings.json"
        )

        if default_path.is_file():
            settings.load(default_path)
        else:
            print("Warning: 'default_settings.json' not found.")

        return settings

    def __init__(self, parent: QWidget | None):
        """Initialize the settings window by loading default settings."""
        super().__init__(parent)
        self.setWindowTitle("LMT-EYE - Analysis Settings")

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
        btn_style = get_btn_style(txt_color="white", bg_color="black")
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
        btn_style = get_btn_style(txt_color="white", bg_color="blue")
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
        btn_style = get_btn_style(txt_color="white", bg_color="blue")
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
        btn_style = get_btn_style(size=13, txt_color="white", bg_color="black")

        # load settings
        self.load_settings_btn = QPushButton("Load settings")
        self.load_settings_btn.setToolTip("Load settings from a JSON file.")
        self.load_settings_btn.setStyleSheet(btn_style)
        self.load_settings_btn.setFixedWidth(130)
        self.load_settings_btn.clicked.connect(self.on_load_settings)

        # save settings
        self.save_settings_btn = QPushButton("Save settings")
        self.save_settings_btn.setToolTip(
            "Save current settings to a JSON file."
        )
        self.save_settings_btn.setStyleSheet(btn_style)
        self.save_settings_btn.setFixedWidth(130)
        self.save_settings_btn.clicked.connect(self.on_save_settings)

        # set default settings
        self.default_settings_btn = QPushButton("Define as default")
        self.default_settings_btn.setToolTip(
            "Save current settings as default."
        )
        self.default_settings_btn.setStyleSheet(btn_style)
        self.default_settings_btn.setFixedWidth(130)
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
        self._update_ui_from_settings()

    #######################################
    #   UI x Settings   #
    #######################################

    def _update_ui_from_settings(self):
        """Update UI elements based on LMT-EYE settings."""
        settings = self.settings.as_str_dict()

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
        dlg = EventSelectionWindow(self, self.settings.events)
        if dlg.exec():
            self.settings.events = dlg.selected_events
            self._update_custom_events()

    def on_select_area(self):
        dlg = AreaSelectionWindow(self, self.settings.analysis_area)
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
            str(AnalysisSettingsWindow.SAVING_PATH),
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
            str(AnalysisSettingsWindow.SAVING_PATH),
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
        save_path = (
            AnalysisSettingsWindow.SAVING_PATH / "default_settings.json"
        )
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
