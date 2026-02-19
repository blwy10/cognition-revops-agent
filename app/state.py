from __future__ import annotations

from typing import Optional

from PySide6.QtCore import QDateTime, QObject, Signal


class AppState(QObject):
    loadedDataChanged = Signal(str)
    outputPathChanged = Signal(str)
    runsChanged = Signal()
    issuesChanged = Signal()
    requestTabChange = Signal(str)

    def __init__(self, parent: Optional[QObject] = None) -> None:
        super().__init__(parent)
        self.loaded_data_path: Optional[str] = None
        self.output_data_path: Optional[str] = None
        self.runs: list[dict] = []
        self.issues: list[dict] = []

    def seed_demo_data(self) -> None:
        now = QDateTime.currentDateTime()
        self.runs = [
            {"run_id": 1, "datetime": now.addSecs(-3600 * 5), "issues_count": 3},
            {"run_id": 2, "datetime": now.addSecs(-3600 * 2), "issues_count": 5},
        ]

        self.issues = [
            {
                "severity": "High",
                "category": "Pipeline",
                "owner": "Sales Ops",
                "status": "Open",
                "timestamp": now.addSecs(-1800),
                "is_unread": True,
            },
            {
                "severity": "Medium",
                "category": "Attribution",
                "owner": "Marketing Ops",
                "status": "Investigating",
                "timestamp": now.addSecs(-1200),
                "is_unread": True,
            },
            {
                "severity": "Low",
                "category": "CRM Hygiene",
                "owner": "RevOps",
                "status": "Backlog",
                "timestamp": now.addSecs(-600),
                "is_unread": False,
            },
        ]

        self.runsChanged.emit()
        self.issuesChanged.emit()
