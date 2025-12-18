import sys
import sqlite3
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QPushButton, QFileDialog,
    QComboBox, QLineEdit, QLabel, QMessageBox
)

import importlib.util
import os
from pathlib import Path

folder = Path("myfolder")  # Replace with your folder path

rebuild_functions = []

for file in folder.glob("*.py"):
    module_name = file.stem
    if module_name == "__init__":
        continue
    spec = importlib.util.spec_from_file_location(module_name, file)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    if hasattr(module, "rebuildevent"):
        rebuild_functions.append(getattr(module, "rebuildevent"))

# Now rebuild_functions is a list of all rebuildevent functions found

class SQLiteColumnAdder(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SQLite Column Adder")
        self.conn = None
        self.db_path = None

        layout = QVBoxLayout()

        self.load_btn = QPushButton("Load SQLite Database")
        self.load_btn.clicked.connect(self.load_db)
        layout.addWidget(self.load_btn)

        self.table_label = QLabel("Select Table:")
        layout.addWidget(self.table_label)
        self.table_combo = QComboBox()
        layout.addWidget(self.table_combo)

        self.col_label = QLabel("New Column Name:")
        layout.addWidget(self.col_label)
        self.col_input = QLineEdit()
        layout.addWidget(self.col_input)

        self.add_btn = QPushButton("Add Column")
        self.add_btn.clicked.connect(self.add_column)
        layout.addWidget(self.add_btn)

        self.setLayout(layout)

    def load_db(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Open SQLite Database", "", "SQLite Files (*.sqlite *.db)")
        if file_path:
            try:
                self.conn = sqlite3.connect(file_path)
                self.db_path = file_path
                self.refresh_tables()
                QMessageBox.information(self, "Success", f"Loaded database: {file_path}")
            except Exception as e:
                QMessageBox.critical(self, "Error", str(e))

    def refresh_tables(self):
        if self.conn:
            cursor = self.conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = [row[0] for row in cursor.fetchall()]
            self.table_combo.clear()
            self.table_combo.addItems(tables)

    def add_column(self):
        table = self.table_combo.currentText()
        col_name = self.col_input.text().strip()
        if not table or not col_name:
            QMessageBox.warning(self, "Input Error", "Please select a table and enter a column name.")
            return
        try:
            cursor = self.conn.cursor()
            cursor.execute(f"ALTER TABLE {table} ADD COLUMN {col_name} TEXT;")
            self.conn.commit()
            QMessageBox.information(self, "Success", f"Added column '{col_name}' to table '{table}'.")

            # Ask if user wants to define a value for each row
            reply = QMessageBox.question(
                self,
                "Set Value for New Column",
                f"Do you want to set a value for all rows in the new column '{col_name}'?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.Yes:
                value, ok = QInputDialog.getText(
                    self,
                    "Set Value",
                    f"Enter value for all rows in column '{col_name}':"
                )
                if ok:
                    try:
                        cursor.execute(f"UPDATE {table} SET {col_name} = ?", (value,))
                        self.conn.commit()
                        QMessageBox.information(self, "Success", f"Set value for all rows in '{col_name}'.")
                    except Exception as e:
                        QMessageBox.critical(self, "Error", f"Failed to set value: {e}")
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SQLiteColumnAdder()
    window.show()
    sys.exit(app.exec())