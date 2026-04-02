from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QCheckBox,
    QDialog,
    QGridLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from dim_c_brains.scripts.events_and_modules import ALL_EVENTS
from dim_c_brains.widgets.pyqt6_tools import get_btn_style


class EventSelectionDialog(QDialog):
    """PyQt6 Dialog to select which analysis to perform"""

    def __init__(
        self,
        parent: QWidget | None,
        preselected_events: set[str] | None = None,
    ):
        super().__init__(parent)
        if preselected_events is None:
            preselected_events = set()
        self.selected_events: set[str] = preselected_events
        self._init_ui()

    def _init_ui(self):
        self.setWindowTitle("Select all wanted events")
        self.setFixedSize(1000, 400)
        layout = QVBoxLayout()

        label = QLabel("Available events:")
        label.setStyleSheet("font-size: 15px; font-weight: bold;")
        layout.addWidget(
            label,
            alignment=Qt.AlignmentFlag.AlignHCenter
            | Qt.AlignmentFlag.AlignTop,
        )

        grid_layout = QGridLayout()
        self.analysis_options = []
        max_col = 4
        max_row = (len(ALL_EVENTS) + max_col - 1) // max_col
        row = 0
        col = 0
        for text in list(ALL_EVENTS.keys()):
            cb = QCheckBox(text)
            grid_layout.addWidget(cb, row, col)
            self.analysis_options.append(cb)
            if text in self.selected_events:
                cb.setChecked(True)
            row += 1
            if row >= max_row:
                col += 1
                row = 0

        grid_widget = QWidget()
        grid_widget.setLayout(grid_layout)
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setWidget(grid_widget)
        layout.addWidget(scroll_area)

        btn_style = get_btn_style(size=15, bold=True, bg_color="#1976D2")
        self.proceed_btn = QPushButton("Validate Selection")
        self.proceed_btn.setStyleSheet(btn_style)
        self.proceed_btn.clicked.connect(self.on_validation)
        layout.addWidget(
            self.proceed_btn, alignment=Qt.AlignmentFlag.AlignHCenter
        )

        self.setLayout(layout)

    def on_validation(self):
        """Get all selected events."""
        self.selected_events = self.get_selected_events()
        if self.selected_events:
            list_events = ", ".join(self.selected_events)
        else:
            list_events = "No event selected"
        print(f"Selected events: {list_events}.")
        self.accept()

    def get_selected_events(self) -> set[str]:
        """Return a set of event names for checked checkboxes."""
        return {cb.text() for cb in self.analysis_options if cb.isChecked()}


def test_event_selection_dialog():
    import sys
    from PyQt6.QtWidgets import QApplication

    app = QApplication(sys.argv)
    preselected = {"Flickering", "Stop"}
    dialog = EventSelectionDialog(None, preselected_events=preselected)
    if dialog.exec() == QDialog.DialogCode.Accepted:
        print("Selected events:", dialog.selected_events)
