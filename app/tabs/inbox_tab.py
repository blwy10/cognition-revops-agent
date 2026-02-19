from __future__ import annotations

from typing import Optional

from PySide6.QtCore import QDateTime, QObject, QTimer, Qt
from PySide6.QtWidgets import (
    QHBoxLayout,
    QPushButton,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from app.state import AppState
from app.tabs.issue_detail_panel import IssueDetailPanel
from app.tabs.issue_table_panel import IssueTablePanel


class InboxTab(QWidget):
    def __init__(self, state: AppState, parent: Optional[QObject] = None) -> None:
        super().__init__(parent)
        self.state = state

        outer = QVBoxLayout(self)
        outer.setContentsMargins(16, 16, 16, 16)
        outer.setSpacing(12)

        self.splitter = QSplitter(Qt.Horizontal, self)
        outer.addWidget(self.splitter)

        # --- Left: issue table ---
        self.table_panel = IssueTablePanel(self)
        self.splitter.addWidget(self.table_panel)

        # --- Right: action buttons + detail form ---
        right_widget = QWidget(self)
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(10)

        action_row = QHBoxLayout()
        action_row.setContentsMargins(12, 12, 12, 12)
        action_row.setSpacing(10)
        self.snooze_button = QPushButton("Snooze")
        self.resolve_button = QPushButton("Resolve")
        self.reopen_button = QPushButton("Reopen")
        action_row.addWidget(self.snooze_button)
        action_row.addWidget(self.resolve_button)
        action_row.addWidget(self.reopen_button)
        right_layout.addLayout(action_row)

        self.detail_panel = IssueDetailPanel(self)
        right_layout.addWidget(self.detail_panel, 1)

        self.splitter.addWidget(right_widget)
        self.splitter.setSizes([480, 720])
        self.splitter.setStretchFactor(0, 1)
        self.splitter.setStretchFactor(1, 2)

        # --- Wiring ---
        self.table_panel.issueSelected.connect(self._on_issue_selected)
        self.table_panel.selectionCleared.connect(self._on_selection_cleared)
        self.table_panel.export_csv_button.clicked.connect(self._on_export_csv_clicked)

        self.snooze_button.clicked.connect(self._on_snooze_clicked)
        self.resolve_button.clicked.connect(self._on_resolve_clicked)
        self.reopen_button.clicked.connect(self._on_reopen_clicked)

        self.state.issuesChanged.connect(self._rebuild_model)

        self._snooze_timer = QTimer(self)
        self._snooze_timer.setInterval(60_000)
        self._snooze_timer.timeout.connect(self._apply_snooze_expirations)
        self._snooze_timer.start()

        self._rebuild_model()

    # ------------------------------------------------------------------
    # Public (called by MainWindow on startup)
    # ------------------------------------------------------------------

    def _rebuild_model(self) -> None:
        self._apply_snooze_expirations(emit_signals=False)
        self.table_panel.rebuild(self.state.issues)

    # ------------------------------------------------------------------
    # Selection handling
    # ------------------------------------------------------------------

    def _on_issue_selected(self, issue_index: int) -> None:
        if issue_index < 0 or issue_index >= len(self.state.issues):
            self.detail_panel.clear()
            return

        issue = self.state.issues[issue_index]
        self.detail_panel.set_issue(issue)

        source_row = self.table_panel.selected_source_row()

        if issue.status == "Open":
            issue.status = "Acknowledged"
            if source_row is not None:
                self.table_panel.update_status_cell(source_row, "Acknowledged")
            self.state.stateChanged.emit()

        if issue.is_unread:
            issue.is_unread = False
            if source_row is not None:
                self.table_panel.mark_row_read(source_row)
            self.state.stateChanged.emit()

    def _on_selection_cleared(self) -> None:
        self.detail_panel.clear()

    # ------------------------------------------------------------------
    # CSV export
    # ------------------------------------------------------------------

    def _on_export_csv_clicked(self) -> None:
        self.table_panel.export_csv(
            self.state.issues,
            default_run_id=getattr(self.state, "selected_run_id", None),
        )

    # ------------------------------------------------------------------
    # Issue actions (snooze / resolve / reopen)
    # ------------------------------------------------------------------

    def _on_snooze_clicked(self) -> None:
        issue_index = self.table_panel.selected_issue_index()
        if issue_index is None or issue_index >= len(self.state.issues):
            return
        row = self.table_panel.selected_source_row()
        if row is None:
            return
        issue = self.state.issues[issue_index]
        issue.status = "Snoozed"
        issue.snoozed_until = QDateTime.currentDateTime().addDays(1)
        self.table_panel.update_row_visuals(row=row, issue=issue)
        self.detail_panel.status_edit.setText(str(issue.status))
        self.state.stateChanged.emit()

    def _on_resolve_clicked(self) -> None:
        issue_index = self.table_panel.selected_issue_index()
        if issue_index is None or issue_index >= len(self.state.issues):
            return
        row = self.table_panel.selected_source_row()
        if row is None:
            return
        issue = self.state.issues[issue_index]
        issue.status = "Resolved"
        issue.snoozed_until = None
        issue.is_unread = False
        self.table_panel.update_row_visuals(row=row, issue=issue)
        self.detail_panel.status_edit.setText(str(issue.status))
        self.state.stateChanged.emit()

    def _on_reopen_clicked(self) -> None:
        issue_index = self.table_panel.selected_issue_index()
        if issue_index is None or issue_index >= len(self.state.issues):
            return
        row = self.table_panel.selected_source_row()
        if row is None:
            return
        issue = self.state.issues[issue_index]
        issue.status = "Open"
        issue.snoozed_until = None
        issue.is_unread = True
        self.table_panel.update_row_visuals(row=row, issue=issue)
        self.detail_panel.status_edit.setText(str(issue.status))
        self.state.stateChanged.emit()

    # ------------------------------------------------------------------
    # Snooze expiration
    # ------------------------------------------------------------------

    def _apply_snooze_expirations(self, *, emit_signals: bool = True) -> bool:
        now = None
        changed = False
        for issue in self.state.issues:
            if issue.status != "Snoozed":
                continue
            snoozed_until = issue.snoozed_until
            if snoozed_until is None:
                continue
            if now is None:
                now = QDateTime.currentDateTime()
            try:
                expired = bool(snoozed_until <= now)
            except Exception:
                expired = False
            if not expired:
                continue

            issue.status = "Open"
            issue.is_unread = True
            issue.snoozed_until = None
            changed = True

        if changed and emit_signals:
            self.state.issuesChanged.emit()
            self.state.stateChanged.emit()

        return changed
