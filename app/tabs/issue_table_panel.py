from __future__ import annotations

import csv
from typing import Optional

from PySide6.QtCore import QObject, QPoint, QSettings, QSortFilterProxyModel, Qt, Signal
from PySide6.QtGui import QColor, QFont, QIcon, QPainter, QPixmap, QStandardItem, QStandardItemModel
from PySide6.QtWidgets import (
    QAbstractItemView,
    QFileDialog,
    QMessageBox,
    QPushButton,
    QSizePolicy,
    QStyle,
    QTableView,
    QVBoxLayout,
    QWidget,
)

from models import Issue


class InboxSortProxyModel(QSortFilterProxyModel):
    def __init__(self, parent: Optional[QObject] = None) -> None:
        super().__init__(parent)

        self._severity_rank = {
            "HIGH": 3,
            "MEDIUM": 2,
            "LOW": 1,
        }
        self._status_rank = {
            "Open": 4,
            "Acknowledged": 3,
            "Snooze": 2,
            "Snoozed": 2,
            "Resolved": 1,
        }

    def lessThan(self, left, right) -> bool:  # type: ignore[override]
        column = left.column()
        if column == 0:
            left_text = str(left.data(Qt.DisplayRole) or "").strip().upper()
            right_text = str(right.data(Qt.DisplayRole) or "").strip().upper()
            return self._severity_rank.get(left_text, 0) < self._severity_rank.get(right_text, 0)

        if column == 6:
            left_text = str(left.data(Qt.DisplayRole) or "").strip()
            right_text = str(right.data(Qt.DisplayRole) or "").strip()
            return self._status_rank.get(left_text, 0) < self._status_rank.get(right_text, 0)

        return super().lessThan(left, right)


class IssueTablePanel(QWidget):
    COLUMNS = ["Severity", "Name", "Account", "Opportunity", "Category", "Owner", "Status", "Timestamp"]
    _SORT_SETTINGS_GROUP = "inbox_table"
    _SORT_COLUMN_KEY = "sort_column"
    _SORT_ORDER_KEY = "sort_order"

    issueSelected = Signal(int)
    selectionCleared = Signal()

    def __init__(self, parent: Optional[QObject] = None) -> None:
        super().__init__(parent)
        self._settings = QSettings("cognition", "revops-analysis-agent")
        self._snooze_icon = self._make_flag_icon()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        self.table = QTableView(self)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setShowGrid(False)
        self.table.verticalHeader().setVisible(False)
        self.table.setWordWrap(False)
        self.table.setSortingEnabled(True)

        self.model = QStandardItemModel(self)
        self.model.setHorizontalHeaderLabels(self.COLUMNS)

        self.proxy_model = InboxSortProxyModel(self)
        self.proxy_model.setSourceModel(self.model)
        self.proxy_model.setDynamicSortFilter(True)

        self.table.setModel(self.proxy_model)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.horizontalHeader().setDefaultAlignment(Qt.AlignLeft)
        self.table.horizontalHeader().sortIndicatorChanged.connect(self._on_sort_indicator_changed)

        self.table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        layout.addWidget(self.table, 1)

        self.export_csv_button = QPushButton("Export Issues to CSV…")
        self.export_csv_button.setEnabled(False)
        layout.addWidget(self.export_csv_button)

        self.table.selectionModel().selectionChanged.connect(self._on_selection_changed)
        self._restore_sort_settings()

    # ------------------------------------------------------------------
    # Public helpers
    # ------------------------------------------------------------------

    def rebuild(self, issues: list[Issue]) -> None:
        self.model.removeRows(0, self.model.rowCount())
        self.export_csv_button.setEnabled(bool(issues))

        for idx, issue in enumerate(issues):
            items = [
                QStandardItem(str(issue.severity)),
                QStandardItem(str(issue.name)),
                QStandardItem(str(issue.account_name)),
                QStandardItem(str(issue.opportunity_name)),
                QStandardItem(str(issue.category)),
                QStandardItem(str(issue.owner)),
                QStandardItem(str(issue.status)),
                QStandardItem(issue.timestamp.toString("yyyy-MM-dd") if issue.timestamp else ""),
            ]

            for item in items:
                item.setData(idx, Qt.UserRole)

            if issue.is_unread:
                self._set_row_bold(items, True)

            status = str(issue.status)
            status_item = items[6]
            if status == "Snoozed":
                status_item.setIcon(self._snooze_icon)
            elif status == "Resolved":
                status_item.setIcon(self.style().standardIcon(QStyle.SP_DialogApplyButton))

            self.model.appendRow(items)

        self._apply_current_sort()

    def selected_issue_index(self) -> Optional[int]:
        selected = self.table.selectionModel().selectedRows()
        if not selected:
            return None

        source_row = self.proxy_model.mapToSource(selected[0]).row()
        index_item = self.model.item(source_row, 0)
        if index_item is None:
            return None
        return int(index_item.data(Qt.UserRole))

    def selected_source_row(self) -> Optional[int]:
        selected = self.table.selectionModel().selectedRows()
        if not selected:
            return None
        return self.proxy_model.mapToSource(selected[0]).row()

    def update_row_visuals(self, *, row: int, issue: Issue) -> None:
        status_item = self.model.item(row, 6)
        if status_item is not None:
            status_text = str(issue.status)
            status_item.setText(status_text)
            if status_text == "Snoozed":
                status_item.setIcon(self._snooze_icon)
            elif status_text == "Resolved":
                status_item.setIcon(self.style().standardIcon(QStyle.SP_DialogApplyButton))
            else:
                status_item.setIcon(QIcon())

        if issue.is_unread:
            row_items = [self.model.item(row, c) for c in range(self.model.columnCount())]
            self._set_row_bold([i for i in row_items if i is not None], True)
        else:
            row_items = [self.model.item(row, c) for c in range(self.model.columnCount())]
            self._set_row_bold([i for i in row_items if i is not None], False)

    def update_status_cell(self, source_row: int, text: str) -> None:
        status_item = self.model.item(source_row, 6)
        if status_item is not None:
            status_item.setText(text)
            status_item.setIcon(QIcon())

    def mark_row_read(self, source_row: int) -> None:
        row_items = [self.model.item(source_row, c) for c in range(self.model.columnCount())]
        self._set_row_bold([i for i in row_items if i is not None], False)

    def export_csv(self, issues: list[Issue], default_run_id: Optional[int] = None) -> None:
        if not issues:
            return

        default_name = f"run-{default_run_id}-issues.csv" if default_run_id is not None else "issues.csv"
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Issues to CSV",
            default_name,
            "CSV Files (*.csv)",
        )
        if not path:
            return
        if not path.lower().endswith(".csv"):
            path = f"{path}.csv"

        import dataclasses as _dc

        columns = [f.name for f in _dc.fields(Issue)]

        def _cell(value) -> str:
            if value is None:
                return ""
            if hasattr(value, "toString"):
                try:
                    return value.toString(Qt.ISODate)
                except Exception:
                    return str(value)
            if isinstance(value, (list, tuple)):
                return ", ".join(str(v) for v in value)
            text = str(value)
            text = text.replace("\r\n", "\n").replace("\r", "\n")
            return text.replace("\n", "\\n")

        try:
            with open(path, "w", encoding="utf-8", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=columns)
                writer.writeheader()
                for issue in issues:
                    row = {k: _cell(getattr(issue, k, None)) for k in columns}
                    writer.writerow(row)
        except Exception as e:
            QMessageBox.critical(self, "Export Failed", f"Could not export CSV:\n{e}")
            return

        QMessageBox.information(self, "Export Complete", f"Exported issues to:\n{path}")

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _apply_current_sort(self) -> None:
        header = self.table.horizontalHeader()
        column = int(header.sortIndicatorSection())
        order = header.sortIndicatorOrder()
        self.proxy_model.sort(column, order)

    def _restore_sort_settings(self) -> None:
        self._settings.beginGroup(self._SORT_SETTINGS_GROUP)
        stored_column = self._settings.value(self._SORT_COLUMN_KEY, None)
        stored_order = self._settings.value(self._SORT_ORDER_KEY, None)
        self._settings.endGroup()

        if stored_column is None or stored_order is None:
            self.table.sortByColumn(0, Qt.SortOrder.DescendingOrder)
            return

        try:
            column = int(stored_column)
        except Exception:
            column = 0

        try:
            order_int = int(stored_order)
            order = Qt.SortOrder(order_int)
        except Exception:
            order = Qt.SortOrder.DescendingOrder

        if column < 0 or column >= len(self.COLUMNS):
            column = 0

        self.table.sortByColumn(column, order)

    def _persist_sort_settings(self, *, column: int, order: Qt.SortOrder) -> None:
        self._settings.beginGroup(self._SORT_SETTINGS_GROUP)
        self._settings.setValue(self._SORT_COLUMN_KEY, int(column))
        self._settings.setValue(self._SORT_ORDER_KEY, int(order.value))
        self._settings.endGroup()

    def _on_sort_indicator_changed(self, column: int, order: Qt.SortOrder) -> None:
        self._persist_sort_settings(column=column, order=order)

    def _on_selection_changed(self) -> None:
        idx = self.selected_issue_index()
        if idx is None:
            self.selectionCleared.emit()
        else:
            self.issueSelected.emit(idx)

    def _set_row_bold(self, row_items: list[QStandardItem], bold: bool) -> None:
        font = QFont()
        font.setBold(bold)
        for item in row_items:
            item.setFont(font)

    @staticmethod
    def _make_flag_icon() -> QIcon:
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
