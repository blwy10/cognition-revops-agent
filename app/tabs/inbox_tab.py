from __future__ import annotations

from typing import Optional

from PySide6.QtCore import QObject, QPoint, QTimer, Qt
from PySide6.QtGui import QColor, QFont, QIcon, QPainter, QPixmap, QStandardItem, QStandardItemModel
from PySide6.QtWidgets import (
    QAbstractItemView,
    QFormLayout,
    QLineEdit,
    QPushButton,
    QSplitter,
    QStyle,
    QTableView,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from app.state import AppState


class InboxTab(QWidget):
    COLUMNS = ["Severity", "Name", "Category", "Owner", "Status", "Timestamp"]

    def __init__(self, state: AppState, parent: Optional[QObject] = None) -> None:
        super().__init__(parent)
        self.state = state

        self._snooze_icon = self._make_flag_icon()

        outer = QVBoxLayout(self)
        outer.setContentsMargins(16, 16, 16, 16)
        outer.setSpacing(12)
        self.splitter = QSplitter(Qt.Horizontal, self)
        outer.addWidget(self.splitter)

        self.table = QTableView(self)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
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

        self.snooze_button = QPushButton("Snooze")
        self.resolve_button = QPushButton("Resolve")
        self.reopen_button = QPushButton("Reopen")

        self.details_form.addRow("Severity", self.severity_edit)
        self.details_form.addRow("", self.snooze_button)
        self.details_form.addRow("", self.resolve_button)
        self.details_form.addRow("", self.reopen_button)
        self.details_form.addRow("Category", self.category_edit)
        self.details_form.addRow("Owner", self.owner_edit)
        self.details_form.addRow("Status", self.status_edit)
        self.details_form.addRow("Timestamp", self.timestamp_edit)
        self.details_form.addRow("Notes", self.notes_edit)

        self.splitter.addWidget(self.details_widget)
        self.splitter.setSizes([480, 720])

        self.table.selectionModel().selectionChanged.connect(self._on_selection_changed)
        self.state.issuesChanged.connect(self._rebuild_model)

        self.snooze_button.clicked.connect(self._on_snooze_clicked)
        self.resolve_button.clicked.connect(self._on_resolve_clicked)
        self.reopen_button.clicked.connect(self._on_reopen_clicked)

        self._snooze_timer = QTimer(self)
        self._snooze_timer.setInterval(60_000)
        self._snooze_timer.timeout.connect(self._apply_snooze_expirations)
        self._snooze_timer.start()

        self._rebuild_model()

    def _rebuild_model(self) -> None:
        self._apply_snooze_expirations(emit_signals=False)
        self.model.removeRows(0, self.model.rowCount())

        for idx, issue in enumerate(self.state.issues):
            items = [
                QStandardItem(str(issue.get("severity", ""))),
                QStandardItem(str(issue.get("name", ""))),
                QStandardItem(str(issue.get("category", ""))),
                QStandardItem(str(issue.get("owner", ""))),
                QStandardItem(str(issue.get("status", ""))),
                QStandardItem(issue.get("timestamp").toString("yyyy-MM-dd") if issue.get("timestamp") else ""),
            ]

            for item in items:
                item.setData(idx, Qt.UserRole)

            if issue.get("is_unread", False):
                self._set_row_bold(items, True)

            status = str(issue.get("status", ""))
            status_item = items[4]
            if status == "Snoozed":
                status_item.setIcon(self._snooze_icon)
            elif status == "Resolved":
                status_item.setIcon(self.style().standardIcon(QStyle.SP_DialogApplyButton))

            self.model.appendRow(items)

    def _selected_issue_index(self) -> Optional[int]:
        selected = self.table.selectionModel().selectedRows()
        if not selected:
            return None
        row = selected[0].row()
        index_item = self.model.item(row, 0)
        if index_item is None:
            return None
        issue_index = int(index_item.data(Qt.UserRole))
        if issue_index < 0 or issue_index >= len(self.state.issues):
            return None
        return issue_index

    def _make_flag_icon(self) -> QIcon:
        size = 14
        pixmap = QPixmap(size, size)
        pixmap.fill(Qt.transparent)

        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing, True)

        pole_color = QColor(90, 90, 90)
        flag_color = QColor(220, 60, 60)

        painter.setPen(pole_color)
        painter.drawLine(4, 2, 4, size - 2)

        painter.setPen(Qt.NoPen)
        painter.setBrush(flag_color)
        points = [
            (5, 3),
            (12, 5),
            (5, 7),
        ]
        painter.drawPolygon([QPoint(x, y) for x, y in points])

        painter.end()
        return QIcon(pixmap)

    def _apply_snooze_expirations(self, *, emit_signals: bool = True) -> bool:
        now = None
        changed = False
        for issue in self.state.issues:
            if not isinstance(issue, dict):
                continue
            if issue.get("status") != "Snoozed":
                continue
            snoozed_until = issue.get("snoozed_until")
            if snoozed_until is None:
                continue
            if now is None:
                from PySide6.QtCore import QDateTime

                now = QDateTime.currentDateTime()
            try:
                expired = bool(snoozed_until <= now)
            except Exception:
                expired = False
            if not expired:
                continue

            issue["status"] = "Open"
            issue["is_unread"] = True
            issue.pop("snoozed_until", None)
            changed = True

        if changed and emit_signals:
            self.state.issuesChanged.emit()
            self.state.stateChanged.emit()

        return changed

    def _on_snooze_clicked(self) -> None:
        issue_index = self._selected_issue_index()
        if issue_index is None:
            return
        issue = self.state.issues[issue_index]
        from PySide6.QtCore import QDateTime

        issue["status"] = "Snoozed"
        issue["snoozed_until"] = QDateTime.currentDateTime().addDays(1)
        self.state.issuesChanged.emit()
        self.state.stateChanged.emit()

    def _on_resolve_clicked(self) -> None:
        issue_index = self._selected_issue_index()
        if issue_index is None:
            return
        issue = self.state.issues[issue_index]
        issue["status"] = "Resolved"
        issue.pop("snoozed_until", None)
        issue["is_unread"] = False
        self.state.issuesChanged.emit()
        self.state.stateChanged.emit()

    def _on_reopen_clicked(self) -> None:
        issue_index = self._selected_issue_index()
        if issue_index is None:
            return
        issue = self.state.issues[issue_index]
        issue["status"] = "Open"
        issue.pop("snoozed_until", None)
        issue["is_unread"] = True
        self.state.issuesChanged.emit()
        self.state.stateChanged.emit()

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

        if issue.get("status") == "Open":
            issue["status"] = "Acknowledged"
            status_item = self.model.item(row, 4)
            if status_item is not None:
                status_item.setText("Acknowledged")
                status_item.setIcon(QIcon())
            self.state.stateChanged.emit()

        if issue.get("is_unread", False):
            issue["is_unread"] = False
            row_items = [self.model.item(row, c) for c in range(self.model.columnCount())]
            self._set_row_bold([i for i in row_items if i is not None], False)
            self.state.stateChanged.emit()

    def _set_details(self, issue: dict) -> None:
        self.severity_edit.setText(str(issue.get("severity", "")))
        self.category_edit.setText(str(issue.get("category", "")))
        self.owner_edit.setText(str(issue.get("owner", "")))
        self.status_edit.setText(str(issue.get("status", "")))
        ts = issue.get("timestamp")
        self.timestamp_edit.setText(ts.toString("yyyy-MM-dd") if ts else "")
        self.notes_edit.setPlainText("Placeholder notes for selected issue.")

    def _clear_details(self) -> None:
        self.severity_edit.clear()
        self.category_edit.clear()
        self.owner_edit.clear()
        self.status_edit.clear()
        self.timestamp_edit.clear()
        self.notes_edit.setPlainText("Select an issue to see details.")
