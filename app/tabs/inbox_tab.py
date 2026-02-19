from __future__ import annotations

from typing import Optional

from PySide6.QtCore import QObject, QPoint, QSettings, QSortFilterProxyModel, QTimer, Qt
from PySide6.QtGui import QColor, QFont, QIcon, QPainter, QPixmap, QStandardItem, QStandardItemModel
from PySide6.QtWidgets import (
    QAbstractItemView,
    QFormLayout,
    QHBoxLayout,
    QLineEdit,
    QPushButton,
    QSizePolicy,
    QSplitter,
    QStyle,
    QTableView,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from app.state import AppState


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


class InboxTab(QWidget):
    COLUMNS = ["Severity", "Name", "Account", "Opportunity", "Category", "Owner", "Status", "Timestamp"]
    _SORT_SETTINGS_GROUP = "inbox_table"
    _SORT_COLUMN_KEY = "sort_column"
    _SORT_ORDER_KEY = "sort_order"

    def __init__(self, state: AppState, parent: Optional[QObject] = None) -> None:
        super().__init__(parent)
        self.state = state
        self._settings = QSettings("cognition", "revops-analysis-agent")

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

        self.splitter.addWidget(self.table)

        self.details_widget = QWidget(self)
        self.details_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self.details_layout = QVBoxLayout(self.details_widget)
        self.details_layout.setContentsMargins(12, 12, 12, 12)
        self.details_layout.setSpacing(10)

        self.actionButtonLayout = QHBoxLayout()
        self.actionButtonLayout.setContentsMargins(12, 12, 12, 12)
        self.actionButtonLayout.setSpacing(10)

        self.snooze_button = QPushButton("Snooze")
        self.resolve_button = QPushButton("Resolve")
        self.reopen_button = QPushButton("Reopen")

        self.actionButtonLayout.addWidget(self.snooze_button)
        self.actionButtonLayout.addWidget(self.resolve_button)
        self.actionButtonLayout.addWidget(self.reopen_button)

        self.details_form = QFormLayout()
        self.details_form.setContentsMargins(12, 12, 12, 12)
        self.details_form.setHorizontalSpacing(10)
        self.details_form.setVerticalSpacing(8)
        self.details_form.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)

        self.severity_edit = QLineEdit()
        self.severity_edit.setReadOnly(True)
        self.name_edit = QLineEdit()
        self.name_edit.setReadOnly(True)
        self.account_name_edit = QLineEdit()
        self.account_name_edit.setReadOnly(True)
        self.opportunity_name_edit = QLineEdit()
        self.opportunity_name_edit.setReadOnly(True)
        self.category_edit = QLineEdit()
        self.category_edit.setReadOnly(True)
        self.owner_edit = QLineEdit()
        self.owner_edit.setReadOnly(True)
        self.status_edit = QLineEdit()
        self.status_edit.setReadOnly(True)
        self.timestamp_edit = QLineEdit()
        self.timestamp_edit.setReadOnly(True)
        self.fields_edit = QLineEdit()
        self.fields_edit.setReadOnly(True)
        self.metric_name_edit = QLineEdit()
        self.metric_name_edit.setReadOnly(True)
        self.metric_value_edit = QTextEdit()
        self.metric_value_edit.setReadOnly(True)
        self.explanation_edit = QTextEdit()
        self.explanation_edit.setReadOnly(True)
        self.resolution_edit = QTextEdit()
        self.resolution_edit.setReadOnly(True)

        for w in (
            self.severity_edit,
            self.name_edit,
            self.account_name_edit,
            self.opportunity_name_edit,
            self.category_edit,
            self.owner_edit,
            self.status_edit,
            self.timestamp_edit,
            self.fields_edit,
            self.metric_name_edit,
        ):
            w.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        for w in (self.metric_value_edit, self.explanation_edit, self.resolution_edit):
            w.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self.details_form.addRow("Severity", self.severity_edit)
        self.details_form.addRow("Name", self.name_edit)
        self.details_form.addRow("Account", self.account_name_edit)
        self.details_form.addRow("Opportunity", self.opportunity_name_edit)
        self.details_form.addRow("Category", self.category_edit)
        self.details_form.addRow("Owner", self.owner_edit)
        self.details_form.addRow("Status", self.status_edit)
        self.details_form.addRow("Timestamp", self.timestamp_edit)
        self.details_form.addRow("Fields", self.fields_edit)
        self.details_form.addRow("Metric Name", self.metric_name_edit)
        self.details_form.addRow("Metric Value", self.metric_value_edit)
        self.details_form.addRow("Explanation", self.explanation_edit)
        self.details_form.addRow("Resolution", self.resolution_edit)

        self.details_layout.addLayout(self.actionButtonLayout)
        self.details_layout.addLayout(self.details_form, 1)

        self.splitter.addWidget(self.details_widget)
        self.splitter.setSizes([480, 720])
        self.splitter.setStretchFactor(0, 1)
        self.splitter.setStretchFactor(1, 2)

        self.table.selectionModel().selectionChanged.connect(self._on_selection_changed)
        self.state.issuesChanged.connect(self._rebuild_model)

        self.snooze_button.clicked.connect(self._on_snooze_clicked)
        self.resolve_button.clicked.connect(self._on_resolve_clicked)
        self.reopen_button.clicked.connect(self._on_reopen_clicked)

        self._snooze_timer = QTimer(self)
        self._snooze_timer.setInterval(60_000)
        self._snooze_timer.timeout.connect(self._apply_snooze_expirations)
        self._snooze_timer.start()

        self._restore_sort_settings()
        self._rebuild_model()

    def _rebuild_model(self) -> None:
        self._apply_snooze_expirations(emit_signals=False)
        self.model.removeRows(0, self.model.rowCount())

        for idx, issue in enumerate(self.state.issues):
            items = [
                QStandardItem(str(issue.get("severity", ""))),
                QStandardItem(str(issue.get("name", ""))),
                QStandardItem(str(issue.get("account_name", ""))),
                QStandardItem(str(issue.get("opportunity_name", ""))),
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
            status_item = items[6]
            if status == "Snoozed":
                status_item.setIcon(self._snooze_icon)
            elif status == "Resolved":
                status_item.setIcon(self.style().standardIcon(QStyle.SP_DialogApplyButton))

            self.model.appendRow(items)

        self._apply_current_sort()

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

    def _selected_issue_index(self) -> Optional[int]:
        selected = self.table.selectionModel().selectedRows()
        if not selected:
            return None

        source_row = self.proxy_model.mapToSource(selected[0]).row()
        index_item = self.model.item(source_row, 0)
        if index_item is None:
            return None
        issue_index = int(index_item.data(Qt.UserRole))
        if issue_index < 0 or issue_index >= len(self.state.issues):
            return None
        return issue_index

    def _selected_row(self) -> Optional[int]:
        selected = self.table.selectionModel().selectedRows()
        if not selected:
            return None
        return self.proxy_model.mapToSource(selected[0]).row()

    def _update_row_visuals(self, *, row: int, issue: dict) -> None:
        status_item = self.model.item(row, 6)
        if status_item is not None:
            status_text = str(issue.get("status", ""))
            status_item.setText(status_text)
            if status_text == "Snoozed":
                status_item.setIcon(self._snooze_icon)
            elif status_text == "Resolved":
                status_item.setIcon(self.style().standardIcon(QStyle.SP_DialogApplyButton))
            else:
                status_item.setIcon(QIcon())

        if issue.get("is_unread", False):
            row_items = [self.model.item(row, c) for c in range(self.model.columnCount())]
            self._set_row_bold([i for i in row_items if i is not None], True)
        else:
            row_items = [self.model.item(row, c) for c in range(self.model.columnCount())]
            self._set_row_bold([i for i in row_items if i is not None], False)

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
        row = self._selected_row()
        if row is None:
            return
        issue = self.state.issues[issue_index]
        from PySide6.QtCore import QDateTime

        issue["status"] = "Snoozed"
        issue["snoozed_until"] = QDateTime.currentDateTime().addDays(1)
        self._update_row_visuals(row=row, issue=issue)
        self.status_edit.setText(str(issue.get("status", "")))
        self.state.stateChanged.emit()

    def _on_resolve_clicked(self) -> None:
        issue_index = self._selected_issue_index()
        if issue_index is None:
            return
        row = self._selected_row()
        if row is None:
            return
        issue = self.state.issues[issue_index]
        issue["status"] = "Resolved"
        issue.pop("snoozed_until", None)
        issue["is_unread"] = False
        self._update_row_visuals(row=row, issue=issue)
        self.status_edit.setText(str(issue.get("status", "")))
        self.state.stateChanged.emit()

    def _on_reopen_clicked(self) -> None:
        issue_index = self._selected_issue_index()
        if issue_index is None:
            return
        row = self._selected_row()
        if row is None:
            return
        issue = self.state.issues[issue_index]
        issue["status"] = "Open"
        issue.pop("snoozed_until", None)
        issue["is_unread"] = True
        self._update_row_visuals(row=row, issue=issue)
        self.status_edit.setText(str(issue.get("status", "")))
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

        source_row = self.proxy_model.mapToSource(selected[0]).row()
        index_item = self.model.item(source_row, 0)
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
            status_item = self.model.item(source_row, 6)
            if status_item is not None:
                status_item.setText("Acknowledged")
                status_item.setIcon(QIcon())
            self.state.stateChanged.emit()

        if issue.get("is_unread", False):
            issue["is_unread"] = False
            row_items = [self.model.item(source_row, c) for c in range(self.model.columnCount())]
            self._set_row_bold([i for i in row_items if i is not None], False)
            self.state.stateChanged.emit()

    def _set_details(self, issue: dict) -> None:
        self.severity_edit.setText(str(issue.get("severity", "")))
        self.name_edit.setText(str(issue.get("name", "")))
        self.account_name_edit.setText(str(issue.get("account_name", "")))
        self.opportunity_name_edit.setText(str(issue.get("opportunity_name", "")))
        self.category_edit.setText(str(issue.get("category", "")))
        self.owner_edit.setText(str(issue.get("owner", "")))
        self.status_edit.setText(str(issue.get("status", "")))
        ts = issue.get("timestamp")
        self.timestamp_edit.setText(ts.toString("yyyy-MM-dd") if ts else "")
        fields = issue.get("fields")
        if isinstance(fields, (list, tuple)):
            self.fields_edit.setText(", ".join(str(f) for f in fields))
        elif fields is None:
            self.fields_edit.setText("")
        else:
            self.fields_edit.setText(str(fields))
        self.metric_name_edit.setText(str(issue.get("metric_name", "")))
        metric_value = issue.get("metric_value")
        self.metric_value_edit.setText("" if metric_value is None else str(metric_value))
        self.explanation_edit.setPlainText(str(issue.get("explanation", "")))
        self.resolution_edit.setPlainText(str(issue.get("resolution", "")))

    def _clear_details(self) -> None:
        self.severity_edit.clear()
        self.name_edit.clear()
        self.account_name_edit.clear()
        self.opportunity_name_edit.clear()
        self.category_edit.clear()
        self.owner_edit.clear()
        self.status_edit.clear()
        self.timestamp_edit.clear()
        self.fields_edit.clear()
        self.metric_name_edit.clear()
        self.metric_value_edit.clear()
        self.explanation_edit.clear()
        self.resolution_edit.clear()
