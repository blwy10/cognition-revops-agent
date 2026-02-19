from __future__ import annotations

from typing import Optional

from PySide6.QtCore import QObject, Qt
from PySide6.QtGui import QStandardItem, QStandardItemModel
from PySide6.QtWidgets import (
    QAbstractItemView,
    QHBoxLayout,
    QPushButton,
    QTableView,
    QVBoxLayout,
    QWidget,
)

from app.state import AppState


class PreviousRunsTab(QWidget):
    def __init__(self, state: AppState, parent: Optional[QObject] = None) -> None:
        super().__init__(parent)
        self.state = state

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        self.table = QTableView(self)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setShowGrid(False)
        self.table.verticalHeader().setVisible(False)
        self.table.setWordWrap(False)

        self.model = QStandardItemModel(self)
        self.model.setHorizontalHeaderLabels(["Run ID", "DateTime", "# Issues"])
        self.table.setModel(self.model)
        self.table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.table)

        bottom = QHBoxLayout()
        self.load_button = QPushButton("Load Selected Run into Inbox")
        self.load_button.setEnabled(False)
        bottom.addWidget(self.load_button)
        bottom.addStretch(1)
        layout.addLayout(bottom)

        self.table.selectionModel().selectionChanged.connect(self._on_selection_changed)
        self.load_button.clicked.connect(self._on_load_clicked)

        self.state.runsChanged.connect(self._rebuild_model)
        self._rebuild_model()

    def _rebuild_model(self) -> None:
        self.model.removeRows(0, self.model.rowCount())

        for run in self.state.runs:
            run_id_item = QStandardItem(str(run["run_id"]))
            run_id_item.setData(int(run["run_id"]), Qt.UserRole)

            dt = run["datetime"]
            dt_text = dt.toString(Qt.ISODate) if hasattr(dt, "toString") else str(dt)

            dt_item = QStandardItem(dt_text)
            issues_item = QStandardItem(str(run["issues_count"]))

            self.model.appendRow([run_id_item, dt_item, issues_item])

        self.load_button.setEnabled(False)

    def _on_selection_changed(self) -> None:
        has_selection = bool(self.table.selectionModel().selectedRows())
        self.load_button.setEnabled(has_selection)

    def _on_load_clicked(self) -> None:
        rows = self.table.selectionModel().selectedRows()
        if not rows:
            return

        row = rows[0].row()
        run_id_item = self.model.item(row, 0)
        run_id = int(run_id_item.data(Qt.UserRole))

        base = run_id * 100
        from PySide6.QtCore import QDateTime

        now = QDateTime.currentDateTime()
        self.state.issues = [
            {
                "severity": "High" if (base + 1) % 2 == 0 else "Medium",
                "category": "Pipeline",
                "owner": "Sales Ops",
                "status": "Open",
                "timestamp": now.addSecs(-60 * (base + 1)),
                "is_unread": True,
            },
            {
                "severity": "Low",
                "category": "CRM Hygiene",
                "owner": "RevOps",
                "status": "Backlog",
                "timestamp": now.addSecs(-60 * (base + 2)),
                "is_unread": True,
            },
            {
                "severity": "Medium",
                "category": "Attribution",
                "owner": "Marketing Ops",
                "status": "Investigating",
                "timestamp": now.addSecs(-60 * (base + 3)),
                "is_unread": True,
            },
        ]
        self.state.issuesChanged.emit()
        self.state.requestTabChange.emit("Inbox")
