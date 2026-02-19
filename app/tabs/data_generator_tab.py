from __future__ import annotations

import datetime
import json
import os
from typing import Optional

from PySide6.QtCore import QObject
from PySide6.QtWidgets import (
    QFileDialog,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from app.state import AppState
from generator import generate


class DataGeneratorTab(QWidget):
    def __init__(self, state: AppState, parent: Optional[QObject] = None) -> None:
        super().__init__(parent)
        self.state = state

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        generation_group = QGroupBox("Data Generation")
        generation_layout = QVBoxLayout(generation_group)
        generation_layout.setContentsMargins(12, 12, 12, 12)
        generation_layout.setSpacing(10)
        layout.addWidget(generation_group)

        generation_controls_row = QHBoxLayout()
        generation_controls_row.setSpacing(8)
        self.generate_button = QPushButton("Generate Dummy Data…")
        generation_controls_row.addWidget(self.generate_button)
        generation_controls_row.addStretch(1)
        generation_layout.addLayout(generation_controls_row)

        self.output_status_label = QLabel()
        self.output_status_label.setWordWrap(True)
        generation_layout.addWidget(self.output_status_label)

        loading_group = QGroupBox("Data Loading")
        loading_layout = QVBoxLayout(loading_group)
        loading_layout.setContentsMargins(12, 12, 12, 12)
        loading_layout.setSpacing(10)
        layout.addWidget(loading_group)

        loading_controls_row = QHBoxLayout()
        loading_controls_row.setSpacing(8)
        self.load_button = QPushButton("Load Existing Data…")
        loading_controls_row.addWidget(self.load_button)
        loading_controls_row.addStretch(1)
        loading_layout.addLayout(loading_controls_row)

        self.loaded_status_label = QLabel()
        self.loaded_status_label.setWordWrap(True)
        loading_layout.addWidget(self.loaded_status_label)
        layout.addStretch(1)

        self.load_button.clicked.connect(self._on_load_existing)
        self.generate_button.clicked.connect(self._on_generate)

        self.state.loadedDataChanged.connect(self._on_state_paths_changed)
        self.state.outputPathChanged.connect(self._on_state_paths_changed)

        self._sync_from_state()

    def _sync_from_state(self) -> None:
        self._update_status()

    def _update_status(self) -> None:
        loaded = self.state.loaded_data_path or "None"
        output = self.state.output_data_path or "None"
        self.loaded_status_label.setText(f"Loaded data: {loaded}")
        self.output_status_label.setText(f"Output file: {output}")

    def _on_state_paths_changed(self, _path: str) -> None:
        self._sync_from_state()

    def _on_load_existing(self) -> None:
        path, _filter = QFileDialog.getOpenFileName(
            self,
            "Load Existing JSON Data File",
            self.state.loaded_data_path or "",
            "JSON Files (*.json)",
        )
        if not path:
            return
        self.state.loaded_data_path = path
        self.state.load_json_data(path)

    def _on_generate(self) -> None:
        path, _filter = QFileDialog.getSaveFileName(
            self,
            "Select JSON Data File",
            self.state.output_data_path or "",
            "JSON Files (*.json)",
        )
        if not path:
            return
        self.state.output_data_path = path

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

        reps, accounts, opportunities, territories, opportunity_history = generate()
        payload = {
            "schema": "revops-agent-skeleton",
            "generated_at": datetime.datetime.now(tz=datetime.timezone.utc).isoformat(),
            "reps": reps,
            "accounts": accounts,
            "opportunities": opportunities,
            "territories": territories,
            "opportunity_history": opportunity_history,
        }
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)

        self.state.loaded_data_path = output_path
        self.state.load_json_data(output_path)
