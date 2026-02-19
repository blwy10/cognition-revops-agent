from __future__ import annotations

from typing import Optional

from PySide6.QtCore import QObject, Qt
from PySide6.QtGui import QFont, QStandardItem, QStandardItemModel
from PySide6.QtWidgets import (
    QAbstractItemView,
    QFormLayout,
    QLineEdit,
    QSplitter,
    QTableView,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from app.state import AppState


class InboxTab(QWidget):
    COLUMNS = ["Severity", "Category", "Owner", "Status", "Timestamp"]

    def __init__(self, state: AppState, parent: Optional[QObject] = None) -> None:
        super().__init__(parent)
        self.state = state

        outer = QVBoxLayout(self)
        outer.setContentsMargins(16, 16, 16, 16)
        outer.setSpacing(12)
        self.splitter = QSplitter(Qt.Horizontal, self)
        outer.addWidget(self.splitter)

        self.table = QTableView(self)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.setShowGrid(False)
        self.table.verticalHeader().setVisible(False)
        self.table.setWordWrap(False)

        self.model = QStandardItemModel(self)
        self.model.setHorizontalHeaderLabels(self.COLUMNS)
        self.table.setModel(self.model)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.horizontalHeader().setDefaultAlignment(Qt.AlignLeft)

        self.splitter.addWidget(self.table)

        self.details_widget = QWidget(self)
        self.details_form = QFormLayout(self.details_widget)
        self.details_form.setContentsMargins(12, 12, 12, 12)
        self.details_form.setHorizontalSpacing(10)
        self.details_form.setVerticalSpacing(8)

        self.severity_edit = QLineEdit()
        self.severity_edit.setReadOnly(True)
        self.category_edit = QLineEdit()
        self.category_edit.setReadOnly(True)
        self.owner_edit = QLineEdit()
        self.owner_edit.setReadOnly(True)
        self.status_edit = QLineEdit()
        self.status_edit.setReadOnly(True)
        self.timestamp_edit = QLineEdit()
        self.timestamp_edit.setReadOnly(True)
        self.notes_edit = QTextEdit()
        self.notes_edit.setReadOnly(True)
        self.notes_edit.setPlainText("Select an issue to see details.")

        self.details_form.addRow("Severity", self.severity_edit)
        self.details_form.addRow("Category", self.category_edit)
        self.details_form.addRow("Owner", self.owner_edit)
        self.details_form.addRow("Status", self.status_edit)
        self.details_form.addRow("Timestamp", self.timestamp_edit)
        self.details_form.addRow("Notes", self.notes_edit)

        self.splitter.addWidget(self.details_widget)
        self.splitter.setSizes([480, 720])

        self.table.selectionModel().selectionChanged.connect(self._on_selection_changed)
        self.state.issuesChanged.connect(self._rebuild_model)

        self._rebuild_model()

    def _rebuild_model(self) -> None:
        self.model.removeRows(0, self.model.rowCount())

        for idx, issue in enumerate(self.state.issues):
            items = [
                QStandardItem(str(issue.get("severity", ""))),
                QStandardItem(str(issue.get("category", ""))),
                QStandardItem(str(issue.get("owner", ""))),
                QStandardItem(str(issue.get("status", ""))),
                QStandardItem(issue.get("timestamp").toString(Qt.ISODate) if issue.get("timestamp") else ""),
            ]

            for item in items:
                item.setData(idx, Qt.UserRole)

            if issue.get("is_unread", False):
                self._set_row_bold(items, True)

            self.model.appendRow(items)

    def _set_row_bold(self, row_items: list[QStandardItem], bold: bool) -> None:
        font = QFont()
        font.setBold(bold)
        for item in row_items:
            item.setFont(font)

    def _on_selection_changed(self) -> None:
        selected = self.table.selectionModel().selectedRows()
        if not selected:
            self._clear_details()
            return

        row = selected[0].row()
        index_item = self.model.item(row, 0)
        if index_item is None:
            self._clear_details()
            return

        issue_index = int(index_item.data(Qt.UserRole))
        if issue_index < 0 or issue_index >= len(self.state.issues):
            self._clear_details()
            return

        issue = self.state.issues[issue_index]
        self._set_details(issue)

        if issue.get("is_unread", False):
            issue["is_unread"] = False
            row_items = [self.model.item(row, c) for c in range(self.model.columnCount())]
            self._set_row_bold([i for i in row_items if i is not None], False)

    def _set_details(self, issue: dict) -> None:
        self.severity_edit.setText(str(issue.get("severity", "")))
        self.category_edit.setText(str(issue.get("category", "")))
        self.owner_edit.setText(str(issue.get("owner", "")))
        self.status_edit.setText(str(issue.get("status", "")))
        ts = issue.get("timestamp")
        self.timestamp_edit.setText(ts.toString(Qt.ISODate) if ts else "")
        self.notes_edit.setPlainText("Placeholder notes for selected issue.")

    def _clear_details(self) -> None:
        self.severity_edit.clear()
        self.category_edit.clear()
        self.owner_edit.clear()
        self.status_edit.clear()
        self.timestamp_edit.clear()
        self.notes_edit.setPlainText("Select an issue to see details.")
