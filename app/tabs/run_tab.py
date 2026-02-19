from __future__ import annotations

import concurrent.futures
from concurrent.futures import InterpreterPoolExecutor
from typing import Any
from typing import Optional

from PySide6.QtCore import QDateTime, QObject, QTimer
from PySide6.QtWidgets import (
    QCheckBox,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QProgressBar,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from app.state import AppState
from models import Issue, Run
from rules.rule_settings import RuleSettings
from rules.default_rules import (
    MissingCloseDateRule,
    StalenessRule,
    AmountOutlierRule,
    PortfolioEarlyStageConcentrationRule,
    RepEarlyStageConcentrationRule,
    SlippingRule,
    AcctPerRepAboveThreshold,
    PipelinePerRepImbalance,
    DuplicateAcctRule,
    NoOpps,
    UndercoverTam,
)

opportunity_rules = [
    StalenessRule,
    MissingCloseDateRule,
    AmountOutlierRule,
    SlippingRule,
]

opportunity_portfolio_rules = [PortfolioEarlyStageConcentrationRule]

rep_rules = [RepEarlyStageConcentrationRule, AcctPerRepAboveThreshold, PipelinePerRepImbalance]

acct_rules = [NoOpps, UndercoverTam]

acct_portfolio_rules = [DuplicateAcctRule]


def _rule_enabled(rule) -> bool:
    settings_id = getattr(rule, "settings_id", "")
    if not isinstance(settings_id, str) or not settings_id.strip():
        return True
    key = f"rules.enabled.{settings_id.strip()}"
    value = RuleSettings.get(key, True)
    if isinstance(value, bool):
        return value
    s = str(value).strip().lower()
    if s in ("0", "false", "no", "off"):
        return False
    return True


def _run_rule_task(rule, obj, other_context):
    """Module-level function so it can be pickled by InterpreterPoolExecutor."""
    return rule.run(obj, other_context=other_context)


def _result_to_issue(result) -> Issue:
    return Issue(
        severity=str(result.severity),
        name=str(result.name),
        account_name=str(result.account_name),
        opportunity_name=str(result.opportunity_name),
        category=str(result.category),
        owner=str(result.responsible),
        fields=list(result.fields),
        metric_name=str(result.metric_name),
        metric_value=result.formatted_metric_value,
        explanation=str(result.explanation),
        resolution=str(result.resolution),
        status="Open",
        timestamp=QDateTime.currentDateTime(),
        is_unread=True,
    )

class RunTab(QWidget):
    def __init__(self, state: AppState, parent: Optional[QObject] = None) -> None:
        super().__init__(parent)
        self.state = state

        self._run_in_progress = False
        self._auto_timer = QTimer(self)
        self._auto_timer.setSingleShot(False)
        self._auto_timer.timeout.connect(self._on_auto_timer_timeout)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        self.run_button = QPushButton("Run Analysis")
        layout.addWidget(self.run_button)

        auto_row = QHBoxLayout()
        self.auto_run_checkbox = QCheckBox("Auto-run")
        auto_row.addWidget(self.auto_run_checkbox)

        auto_row.addWidget(QLabel("Every"))
        self.auto_run_interval_seconds = QSpinBox()
        self.auto_run_interval_seconds.setRange(1, 86400)
        self.auto_run_interval_seconds.setValue(60)
        auto_row.addWidget(self.auto_run_interval_seconds)
        auto_row.addWidget(QLabel("seconds"))
        auto_row.addStretch(1)
        layout.addLayout(auto_row)

        self.status_label = QLabel("Idle.")
        layout.addWidget(self.status_label)

        self.progress = QProgressBar()
        self.progress.setRange(0, 1)
        self.progress.setVisible(False)
        layout.addWidget(self.progress)

        layout.addStretch(1)

        self.run_button.clicked.connect(self._on_run_clicked)
        self.auto_run_checkbox.toggled.connect(self._on_auto_run_toggled)
        self.auto_run_interval_seconds.valueChanged.connect(self._on_auto_interval_changed)

    def closeEvent(self, event) -> None:
        self._stop_auto_timer()
        super().closeEvent(event)

    def _set_auto_timer_interval_from_ui(self) -> None:
        seconds = int(self.auto_run_interval_seconds.value())
        self._auto_timer.setInterval(max(1, seconds) * 1000)

    def _stop_auto_timer(self) -> None:
        if self._auto_timer.isActive():
            self._auto_timer.stop()

    def _on_auto_run_toggled(self, checked: bool) -> None:
        if not checked:
            self._stop_auto_timer()
            return

        if not self.state.loaded_data_path:
            QMessageBox.warning(self, "No Data Loaded", "Load a dataset first.")
            self.auto_run_checkbox.blockSignals(True)
            self.auto_run_checkbox.setChecked(False)
            self.auto_run_checkbox.blockSignals(False)
            return

        self._set_auto_timer_interval_from_ui()
        self._auto_timer.start()

    def _on_auto_interval_changed(self, _value: int) -> None:
        if not self._auto_timer.isActive():
            return
        self._set_auto_timer_interval_from_ui()
        self._auto_timer.start()

    def _on_auto_timer_timeout(self) -> None:
        if self._run_in_progress:
            return
        if not self.state.loaded_data_path:
            self._stop_auto_timer()
            self.auto_run_checkbox.blockSignals(True)
            self.auto_run_checkbox.setChecked(False)
            self.auto_run_checkbox.blockSignals(False)
            return
        self._on_run_clicked()

    def _on_run_clicked(self) -> None:
        if self._run_in_progress:
            return
        if not self.state.loaded_data_path:
            QMessageBox.warning(self, "No Data Loaded", "Load a dataset first.")
            return

        self._run_in_progress = True
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
            next_id = max(r.run_id for r in self.state.runs) + 1

        # Build a flat list of (rule, obj, other_context) tasks, pre-filtering enabled rules
        tasks: list[tuple] = []

        # Opportunity-level rules
        enabled_opp_rules = [r for r in opportunity_rules if _rule_enabled(r)]
        for opp in self.state.opportunities:
            for rule in enabled_opp_rules:
                tasks.append((rule, opp, self.state.opportunity_history))

        # Portfolio-level opportunity rules
        for rule in opportunity_portfolio_rules:
            if _rule_enabled(rule):
                tasks.append((rule, self.state.opportunities, None))

        # Rep-level rules
        enabled_rep_rules = [r for r in rep_rules if _rule_enabled(r)]
        for rep in self.state.reps:
            for rule in enabled_rep_rules:
                tasks.append((rule, rep, self.state.opportunities))

        # Account-level rules
        enabled_acct_rules = [r for r in acct_rules if _rule_enabled(r)]
        for account in self.state.accounts:
            for rule in enabled_acct_rules:
                tasks.append((rule, account, self.state.opportunities))

        # Global account rules
        for rule in acct_portfolio_rules:
            if _rule_enabled(rule):
                tasks.append((rule, self.state.accounts, self.state.opportunities))

        # Execute all rule tasks in parallel
        issues: list[Issue] = []
        with InterpreterPoolExecutor() as executor:
            futures = {
                executor.submit(_run_rule_task, rule, obj, ctx): (rule, obj, ctx)
                for rule, obj, ctx in tasks
            }
            for future in concurrent.futures.as_completed(futures):
                try:
                    result = future.result()
                except Exception as e:
                    print(e)
                    raise
                if result is not None:
                    issues.append(_result_to_issue(result))

        self.state.issues = issues
        self.state.selected_run_id = next_id
        self.state.issuesChanged.emit()

        self.state.stateChanged.emit()

        self.state.runs.append(Run(
            run_id=next_id,
            datetime=QDateTime.currentDateTime(),
            issues_count=len(issues),
            issues=list(issues),
        ))
        self.state.runsChanged.emit()

        self.state.stateChanged.emit()
        try:
            self.state.save_run_state_to_disk()
        except Exception:
            pass

        self._run_in_progress = False
