from __future__ import annotations

import json
import os
from typing import Optional

from PySide6.QtCore import QObject
from PySide6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from app.state import AppState


class DataGeneratorTab(QWidget):
    def __init__(self, state: AppState, parent: Optional[QObject] = None) -> None:
        super().__init__(parent)
        self.state = state

        layout = QVBoxLayout(self)

        controls_row = QHBoxLayout()
        self.generate_button = QPushButton("Generate Dummy Data…")
        self.load_button = QPushButton("Load Existing Data…")
        controls_row.addWidget(self.generate_button)
        controls_row.addWidget(self.load_button)
        controls_row.addStretch(1)
        layout.addLayout(controls_row)

        output_row = QHBoxLayout()
        self.select_output_button = QPushButton("Select Output File…")
        self.output_path_edit = QLineEdit()
        self.output_path_edit.setReadOnly(True)
        output_row.addWidget(self.select_output_button)
        output_row.addWidget(self.output_path_edit, 1)
        layout.addLayout(output_row)

        self.status_label = QLabel()
        layout.addWidget(self.status_label)
        layout.addStretch(1)

        self.select_output_button.clicked.connect(self._on_select_output)
        self.load_button.clicked.connect(self._on_load_existing)
        self.generate_button.clicked.connect(self._on_generate)

        self.state.loadedDataChanged.connect(self._on_state_paths_changed)
        self.state.outputPathChanged.connect(self._on_state_paths_changed)

        self._sync_from_state()

    def _sync_from_state(self) -> None:
        self.output_path_edit.setText(self.state.output_data_path or "")
        self._update_status()

    def _update_status(self) -> None:
        loaded = self.state.loaded_data_path or "None"
        output = self.state.output_data_path or "None"
        self.status_label.setText(f"Loaded: {loaded} | Output: {output}")

    def _on_state_paths_changed(self, _path: str) -> None:
        self._sync_from_state()

    def _on_select_output(self) -> None:
        path, _filter = QFileDialog.getSaveFileName(
            self,
            "Select Output JSON File",
            self.state.output_data_path or "",
            "JSON Files (*.json)",
        )
        if not path:
            return
        self.state.output_data_path = path
        self.state.outputPathChanged.emit(path)

    def _on_load_existing(self) -> None:
        path, _filter = QFileDialog.getOpenFileName(
            self,
            "Load Existing JSON Dataset",
            self.state.loaded_data_path or "",
            "JSON Files (*.json)",
        )
        if not path:
            return
        self.state.loaded_data_path = path
        self.state.loadedDataChanged.emit(path)

    def _on_generate(self) -> None:
        if not self.state.output_data_path:
            QMessageBox.warning(self, "Missing Output File", "Select an output file first.")
            return

        output_path = self.state.output_data_path
        if os.path.exists(output_path):
            result = QMessageBox.question(
                self,
                "Overwrite?",
                f"File already exists:\n{output_path}\n\nOverwrite?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No,
            )
            if result != QMessageBox.Yes:
                return

        payload = {
            "schema": "revops-agent-skeleton",
            "generated_at": "placeholder",
            "records": [{"id": 1, "name": "Example"}],
        }
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)

        self.state.loaded_data_path = output_path
        self.state.loadedDataChanged.emit(output_path)
