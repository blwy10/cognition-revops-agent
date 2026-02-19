from __future__ import annotations

import random
from typing import Optional

from PySide6.QtCore import QDateTime, QObject, QTimer
from PySide6.QtWidgets import (
    QLabel,
    QMessageBox,
    QPushButton,
    QProgressBar,
    QVBoxLayout,
    QWidget,
)

from app.state import AppState


class RunTab(QWidget):
    def __init__(self, state: AppState, parent: Optional[QObject] = None) -> None:
        super().__init__(parent)
        self.state = state

        layout = QVBoxLayout(self)

        self.run_button = QPushButton("Run Analysis")
        layout.addWidget(self.run_button)

        self.status_label = QLabel("Idle.")
        layout.addWidget(self.status_label)

        self.progress = QProgressBar()
        self.progress.setRange(0, 1)
        self.progress.setVisible(False)
        layout.addWidget(self.progress)

        layout.addStretch(1)

        self.run_button.clicked.connect(self._on_run_clicked)

    def _on_run_clicked(self) -> None:
        if not self.state.loaded_data_path:
            QMessageBox.warning(self, "No Data Loaded", "Load a dataset first.")
            return

        self.run_button.setEnabled(False)
        self.status_label.setText("Run in progress…")
        self.progress.setRange(0, 0)
        self.progress.setVisible(True)

        QTimer.singleShot(1200, self._finish_run)

    def _finish_run(self) -> None:
        self.progress.setVisible(False)
        self.progress.setRange(0, 1)
        self.status_label.setText("Run completed.")
        self.run_button.setEnabled(True)

        next_id = 1
        if self.state.runs:
            next_id = max(r["run_id"] for r in self.state.runs) + 1

        issues_count = random.randint(1, 10)
        self.state.runs.append(
            {"run_id": next_id, "datetime": QDateTime.currentDateTime(), "issues_count": issues_count}
        )
        self.state.runsChanged.emit()

        now = QDateTime.currentDateTime()
        self.state.issues = [
            {
                "severity": "High" if issues_count >= 7 else "Medium",
                "category": "Pipeline",
                "owner": "Sales Ops",
                "status": "Open",
                "timestamp": now,
                "is_unread": True,
            },
            {
                "severity": "Low",
                "category": "CRM Hygiene",
                "owner": "RevOps",
                "status": "Backlog",
                "timestamp": now.addSecs(-300),
                "is_unread": True,
            },
        ]
        self.state.issuesChanged.emit()
