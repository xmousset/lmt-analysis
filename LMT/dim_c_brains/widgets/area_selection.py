from PyQt6.QtGui import QPen, QBrush, QColor
from PyQt6.QtWidgets import (
    QDialog,
    QFrame,
    QGraphicsScene,
    QGraphicsView,
    QGraphicsRectItem,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from dim_c_brains.widgets.pyqt6_tools import get_btn_style


class AreaSelectionGraphicsView(QGraphicsView):
    """Custom graphics view for interactive area selection."""

    def __init__(self, parent, on_area_changed):
        super().__init__(parent)
        self.on_area_changed = on_area_changed
        self.scene_area = QGraphicsScene()
        self.setScene(self.scene_area)
        self.is_valid = True

        # Background rectangle (50x50)
        self.bg_rect = QGraphicsRectItem(0, 0, 250, 250)
        self.bg_rect.setPen(QPen(QColor("black"), 2))
        self.bg_rect.setBrush(QBrush(QColor(200, 200, 200)))
        self.scene_area.addItem(self.bg_rect)

        # Selection rectangle
        self.area = QGraphicsRectItem()
        self.area.setPen(QPen(QColor("green"), 2))
        self.area.setBrush(QBrush(QColor(0, 255, 0, 50)))
        self.scene_area.addItem(self.area)

        self.setSceneRect(-5, -5, 260, 260)
        self.setFixedSize(300, 300)
        self.dragging = False
        self.drag_start = None
        self.drag_offset = None

    def mousePressEvent(self, event):
        if event is None:
            return

        pos = self.mapToScene(event.pos())
        rect = self.area.rect()
        self.drag_offset = pos - rect.topLeft()
        self.dragging = True
        self.drag_start = pos
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if event is None:
            return

        if self.dragging and self.drag_offset is not None:
            pos = self.mapToScene(event.pos())
            w = self.area.rect().width()
            h = self.area.rect().height()
            x = pos.x() - self.drag_offset.x()
            y = pos.y() - self.drag_offset.y()
            x = max(0, min(x, 250 - w))
            y = max(0, min(y, 250 - h))
            self.area.setRect(x, y, w, h)
            self.on_area_changed()

        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        self.dragging = False
        self.drag_offset = None
        super().mouseReleaseEvent(event)

    def get_area(self):
        """Return the selected area as (x_min, y_min, x_max, y_max) in *cm*."""

        area = self.area.rect()

        if self.is_valid:
            x_min = int(area.x() / 5)
            y_min = int(area.y() / 5)
            coef = 1
        else:
            x_min = int((area.x() + area.width()) / 5)
            y_min = int((area.y() + area.height()) / 5)
            coef = -1

        w = int(coef * area.width() / 5)
        h = int(coef * area.height() / 5)
        x_max = x_min + w
        y_max = y_min + h

        return (x_min, y_min, x_max, y_max)

    def set_area(self, area: tuple[int, int, int, int]):
        """Set the area rectangle based on (x_min, y_min, x_max, y_max) in
        *cm*."""

        x_min, y_min, x_max, y_max = area
        x_min = x_min * 5
        y_min = y_min * 5
        x_max = x_max * 5
        y_max = y_max * 5
        w = x_max - x_min
        h = y_max - y_min

        self.area.setRect(x_min, y_min, w, h)

    def set_area_visibility(self, visible: bool):
        """Set the area rectangle to visible or hidden."""
        self.area.setVisible(visible)

    def is_area_visible(self) -> bool:
        """Return True if the area rectangle is visible, False if not."""
        return self.area.isVisible()


class AreaSelectionWindow(QDialog):
    """PyQt6 Dialog to select the area to be analyzed"""

    def __init__(
        self,
        parent: QWidget | None,
        area: tuple[int, int, int, int] | None = None,
    ):
        super().__init__(parent)
        self.selected_area = area
        """(x_min, y_min, x_max, y_max) in *cm*. If None, analyze all data."""
        self.setWindowTitle("LMT-EYE - Analysis Settings - Area Selection")
        self.setFixedSize(500, 400)
        self._init_ui()

    def _init_ui(self):
        """Initialize the UI with graphics view and controls."""
        main_layout = QHBoxLayout()

        # LEFT SIDE
        # ----------------
        # Graphics view
        self.graphics_view = AreaSelectionGraphicsView(
            self, self._on_graphic_changed
        )
        self.graphics_view.setToolTip(
            "Click and drag to adjust the selection area"
        )

        btn_style = get_btn_style(txt_color="white", bg_color="black")

        self.minus5_btn = QPushButton("-5")
        self.minus5_btn.setStyleSheet(btn_style)
        self.minus5_btn.setFixedSize(60, 60)
        self.minus5_btn.clicked.connect(self._on_minus5_pressed)

        self.plus5_btn = QPushButton("+5")
        self.plus5_btn.setStyleSheet(btn_style)
        self.plus5_btn.setFixedSize(60, 60)
        self.plus5_btn.clicked.connect(self._on_plus5_pressed)

        self.minus1_btn = QPushButton("-1")
        self.minus1_btn.setStyleSheet(btn_style)
        self.minus1_btn.setFixedSize(60, 60)
        self.minus1_btn.clicked.connect(self._on_minus1_pressed)

        self.plus1_btn = QPushButton("+1")
        self.plus1_btn.setStyleSheet(btn_style)
        self.plus1_btn.setFixedSize(60, 60)
        self.plus1_btn.clicked.connect(self._on_plus1_pressed)

        btn_row = QHBoxLayout()
        btn_row.addWidget(self.minus5_btn)
        btn_row.addWidget(self.minus1_btn)
        btn_row.addWidget(self.plus1_btn)
        btn_row.addWidget(self.plus5_btn)

        left_layout = QVBoxLayout()
        left_layout.addLayout(btn_row)
        left_layout.addWidget(self.graphics_view)

        # RIGHT SIDE
        # ----------------
        # Input fields and buttons
        self.spin_box_rows = []

        # X
        x_min_row = QHBoxLayout()
        self.x_min_spin = QSpinBox()
        self.x_min_spin.setFixedWidth(80)
        self.x_min_spin.setRange(0, 49)
        self.x_min_spin.setValue(15)
        self.x_min_spin.valueChanged.connect(self._on_x_min_changed)
        x_min_row.addStretch(1)
        x_min_row.addWidget(QLabel("X Min:"))
        x_min_row.addWidget(self.x_min_spin)
        x_min_row.addStretch(1)
        self.spin_box_rows.append(x_min_row)

        x_max_row = QHBoxLayout()
        self.x_max_spin = QSpinBox()
        self.x_max_spin.setFixedWidth(80)
        self.x_max_spin.setRange(1, 50)
        self.x_max_spin.setValue(35)
        self.x_max_spin.valueChanged.connect(self._on_x_max_changed)
        x_max_row.addStretch(1)
        x_max_row.addWidget(QLabel("X Max:"))
        x_max_row.addWidget(self.x_max_spin)
        x_max_row.addStretch(1)
        self.spin_box_rows.append(x_max_row)

        # Y
        y_min_row = QHBoxLayout()
        self.y_min_spin = QSpinBox()
        self.y_min_spin.setFixedWidth(80)
        self.y_min_spin.setRange(0, 49)
        self.y_min_spin.setValue(15)
        self.y_min_spin.valueChanged.connect(self._on_y_min_changed)
        y_min_row.addStretch(1)
        y_min_row.addWidget(QLabel("Y Min:"))
        y_min_row.addWidget(self.y_min_spin)
        y_min_row.addStretch(1)
        self.spin_box_rows.append(y_min_row)

        y_max_row = QHBoxLayout()
        self.y_max_spin = QSpinBox()
        self.y_max_spin.setFixedWidth(80)
        self.y_max_spin.setRange(1, 50)
        self.y_max_spin.setValue(35)
        self.y_max_spin.valueChanged.connect(self._on_y_max_changed)
        y_max_row.addStretch(1)
        y_max_row.addWidget(QLabel("Y Max:"))
        y_max_row.addWidget(self.y_max_spin)
        y_max_row.addStretch(1)
        self.spin_box_rows.append(y_max_row)

        # Width and Height
        width_row = QHBoxLayout()
        self.width_spin = QSpinBox()
        self.width_spin.setFixedWidth(80)
        self.width_spin.setRange(1, 50)
        self.width_spin.setValue(20)
        self.width_spin.valueChanged.connect(self._on_width_changed)
        width_row.addStretch(1)
        width_row.addWidget(QLabel("Width:"))
        width_row.addWidget(self.width_spin)
        width_row.addStretch(1)
        self.spin_box_rows.append(width_row)

        height_row = QHBoxLayout()
        self.height_spin = QSpinBox()
        self.height_spin.setFixedWidth(80)
        self.height_spin.setRange(1, 50)
        self.height_spin.setValue(20)
        self.height_spin.valueChanged.connect(self._on_height_changed)
        height_row.addStretch(1)
        height_row.addWidget(QLabel("Height:"))
        height_row.addWidget(self.height_spin)
        height_row.addStretch(1)
        self.spin_box_rows.append(height_row)

        # Set buttons
        btn_style = get_btn_style(txt_color="white", bg_color="black")
        self.set_filter_btn = QPushButton()
        self.set_filter_btn.setFixedWidth(120)
        self.set_filter_btn.setText("Set Filter")
        self.set_filter_btn.setToolTip("Add an area filter.")
        self.set_filter_btn.setStyleSheet(btn_style)
        self.set_filter_btn.clicked.connect(self._on_set_filter_pressed)

        set_row = QHBoxLayout()
        set_row.addStretch(1)
        set_row.addWidget(self.set_filter_btn)
        set_row.addStretch(1)
        self.spin_box_rows.append(set_row)

        # Reset button
        btn_style = get_btn_style(txt_color="white", bg_color="black")
        self.remove_filter_btn = QPushButton()
        self.remove_filter_btn.setFixedWidth(120)
        self.remove_filter_btn.setText("Remove Filter")
        self.remove_filter_btn.setToolTip(
            "Remove the area filter and set the selected area to None."
        )
        self.remove_filter_btn.setStyleSheet(btn_style)
        self.remove_filter_btn.clicked.connect(self._on_remove_filter_pressed)

        reset_row = QHBoxLayout()
        reset_row.addStretch(1)
        reset_row.addWidget(self.remove_filter_btn)
        reset_row.addStretch(1)
        self.spin_box_rows.append(reset_row)

        # OK and Cancel buttons
        btn_style = get_btn_style(txt_color="white", bg_color="green")
        ok_btn = QPushButton("OK")
        ok_btn.setFixedWidth(80)
        ok_btn.setStyleSheet(btn_style)
        ok_btn.clicked.connect(self.on_accept)

        btn_style = get_btn_style(txt_color="white", bg_color="red")
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setFixedWidth(80)
        cancel_btn.setStyleSheet(btn_style)
        cancel_btn.clicked.connect(self.reject)

        ok_cancel_row = QHBoxLayout()
        ok_cancel_row.addStretch(1)
        ok_cancel_row.addWidget(ok_btn)
        ok_cancel_row.addStretch(1)
        ok_cancel_row.addWidget(cancel_btn)
        ok_cancel_row.addStretch(1)
        self.spin_box_rows.append(ok_cancel_row)

        # Right layout assembly
        right_title = QHBoxLayout()
        right_title.addStretch(1)
        right_title.addWidget(QLabel("Area Filtering"))
        right_title.addStretch(1)

        right_layout = QVBoxLayout()
        right_layout.addLayout(right_title)
        right_layout.addWidget(self.Qhline())
        right_layout.addStretch(1)
        for i, row in enumerate(self.spin_box_rows):
            right_layout.addLayout(row)
            if i % 2 == 1:
                right_layout.addWidget(self.Qhline())
        right_layout.addStretch(1)

        # Combine layouts
        main_layout.addLayout(left_layout, 2)
        main_layout.addLayout(right_layout, 1)

        self.setLayout(main_layout)

        # Apply preselected area
        if self.selected_area is not None:
            self.graphics_view.set_area_visibility(True)
            self.graphics_view.set_area(self.selected_area)
            self.update_spin_boxes()
        else:
            self.graphics_view.set_area_visibility(False)
            self.update_graphic()

    # ================ UTILS ================

    def Qhline(self):
        """Utility function to create a horizontal line separator."""
        hline = QFrame()
        hline.setFrameShape(QFrame.Shape.HLine)
        hline.setFrameShadow(QFrame.Shadow.Sunken)
        hline.setFixedHeight(1)
        return hline

    def update_spin_boxes(self):
        """Update all spinbox values from graphics view."""
        x_min, y_min, x_max, y_max = self.graphics_view.get_area()

        w = x_max - x_min
        h = y_max - y_min

        self.x_min_spin.setValue(x_min)
        self.y_min_spin.setValue(y_min)
        self.x_max_spin.setValue(x_max)
        self.y_max_spin.setValue(y_max)
        self.width_spin.setValue(w)
        self.height_spin.setValue(h)

    def update_graphic(self):
        """Update graphic view when spinbox values change."""
        x_min = self.x_min_spin.value()
        y_min = self.y_min_spin.value()
        x_max = self.x_max_spin.value()
        y_max = self.y_max_spin.value()

        self.graphics_view.set_area((x_min, y_min, x_max, y_max))

    # ================ CALLBACKS ================

    def _on_graphic_changed(self):
        """Update spinboxes when area is changed via graphics view."""
        self.update_spin_boxes()

    def _on_x_min_changed(self):
        """Update graphics view when X Min changes."""
        x_min = self.x_min_spin.value()
        x_max = self.x_max_spin.value()
        self.width_spin.setValue(x_max - x_min)

        self.update_graphic()

    def _on_y_min_changed(self):
        """Update graphics view when Y Min changes."""
        y_min = self.y_min_spin.value()
        y_max = self.y_max_spin.value()
        self.height_spin.setValue(y_max - y_min)

        self.update_graphic()

    def _on_x_max_changed(self):
        """Update graphics view when X Max changes."""
        x_min = self.x_min_spin.value()
        x_max = self.x_max_spin.value()
        self.width_spin.setValue(x_max - x_min)

        self.update_graphic()

    def _on_y_max_changed(self):
        """Update graphics view when Y Max changes."""
        y_min = self.y_min_spin.value()
        y_max = self.y_max_spin.value()
        self.height_spin.setValue(y_max - y_min)

        self.update_graphic()

    def _on_width_changed(self):
        """Update graphics view when Width changes."""
        x_min = self.x_min_spin.value()
        w = self.width_spin.value()
        if x_min + w > 50:
            w = 50 - x_min
            self.width_spin.setValue(w)
        self.x_max_spin.setValue(x_min + w)

        self.update_graphic()

    def _on_height_changed(self):
        """Update graphics view when Height changes."""
        y_min = self.y_min_spin.value()
        h = self.height_spin.value()
        if y_min + h > 50:
            h = 50 - y_min
            self.height_spin.setValue(h)
        self.y_max_spin.setValue(y_min + h)

        self.update_graphic()

    def _plus_minus_changed(self, amount: int):
        """Decrease or increase width and height by a specified amount."""
        x_min = self.x_min_spin.value()
        w = self.width_spin.value()
        if x_min + w + amount > 50:
            w = 50 - x_min
        elif w + amount <= 0:
            w = 1
        else:
            w += amount
        self.width_spin.setValue(w)
        self.x_max_spin.setValue(x_min + w)

        h = self.height_spin.value()
        y_min = self.y_min_spin.value()
        if y_min + h + amount > 50:
            h = 50 - y_min
        elif h + amount <= 0:
            h = 1
        else:
            h += amount
        self.height_spin.setValue(h)
        self.y_max_spin.setValue(y_min + h)

        self.update_graphic()

    def _on_minus5_pressed(self):
        """Decrease width and height by 5."""
        self._plus_minus_changed(-5)

    def _on_minus1_pressed(self):
        """Decrease width and height by 1."""
        self._plus_minus_changed(-1)

    def _on_plus1_pressed(self):
        """Increase width and height by 1."""
        self._plus_minus_changed(1)

    def _on_plus5_pressed(self):
        """Increase width and height by 5."""
        self._plus_minus_changed(5)

    def _on_set_filter_pressed(self):
        """Create an area selection for filtering."""
        self.graphics_view.set_area_visibility(True)

    def _on_remove_filter_pressed(self):
        """Remove the area selection for filtering."""
        self.graphics_view.set_area_visibility(False)

    # ================ RESULTS ================

    def on_accept(self):
        """Store selected area and close dialog."""
        if self.graphics_view.is_area_visible():
            self.selected_area = self.graphics_view.get_area()
        else:
            self.selected_area = None
        self.accept()


def test_area_selection_dialog():
    import sys
    from PyQt6.QtWidgets import QApplication

    app = QApplication(sys.argv)
    dialog = AreaSelectionWindow(None)
    if dialog.exec() == QDialog.DialogCode.Accepted:
        print("Selected area:", dialog.selected_area)
