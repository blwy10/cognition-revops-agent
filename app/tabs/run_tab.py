from __future__ import annotations

from typing import Any
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
from rules.default_rules import (
    MissingCloseDateRule,
    StalenessRule,
    PortfolioEarlyStageConcentrationRule,
    RepEarlyStageConcentrationRule,
    SlippingRule
)

opportunity_rules = [
    StalenessRule,
    MissingCloseDateRule,
    SlippingRule,
]

opportunity_portfollio_rules = [PortfolioEarlyStageConcentrationRule]

rep_rules = [RepEarlyStageConcentrationRule]


class RunTab(QWidget):
    def __init__(self, state: AppState, parent: Optional[QObject] = None) -> None:
        super().__init__(parent)
        self.state = state

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

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

        issues: list[dict[str, Any]] = []

        # Run opportunity-level rules
        for opp in self.state.opportunities:
            for rule in opportunity_rules:
                try:
                    result = rule.run(opp, other_context=self.state.opportunity_history)
                except Exception as e:
                    print(e)
                    raise

                if result is None:
                    continue

                issues.append(
                    {
                        "severity": str(result.severity),
                        "name": str(result.name),
                        "account_name": str(result.account_name),
                        "opportunity_name": str(result.opportunity_name),
                        "category": str(result.category),
                        "owner": str(result.responsible),
                        "fields": list(result.fields),
                        "metric_name": str(result.metric_name),
                        "metric_value": result.formatted_metric_value,
                        "explanation": str(result.explanation),
                        "resolution": str(result.resolution),
                        "status": "Open",
                        "timestamp": QDateTime.currentDateTime(),
                        "is_unread": True,
                    }
                )

        # Run portfolio-level rules
        for rule in opportunity_portfollio_rules:
            try:
                result = rule.run(self.state.opportunities)
            except Exception as e:
                print(e)
                raise

            if result is None:
                continue

            issues.append(
                {
                    "severity": str(result.severity),
                    "name": str(result.name),
                    "account_name": str(result.account_name),
                    "opportunity_name": str(result.opportunity_name),
                    "category": str(result.category),
                    "owner": str(result.responsible),
                    "fields": list(result.fields),
                    "metric_name": str(result.metric_name),
                    "metric_value": result.formatted_metric_value,
                    "explanation": str(result.explanation),
                    "resolution": str(result.resolution),
                    "status": "Open",
                    "timestamp": QDateTime.currentDateTime(),
                    "is_unread": True,
                }
            )
        
        # Run rep-level rules
        for rep in self.state.reps:
            for rule in rep_rules:
                try:
                    result = rule.run(rep, other_context=self.state.opportunities)
                except Exception as e:
                    print(e)
                    raise

                if result is None:
                    continue

                issues.append(
                    {
                        "severity": str(result.severity),
                        "name": str(result.name),
                        "account_name": str(result.account_name),
                        "opportunity_name": str(result.opportunity_name),
                        "category": str(result.category),
                        "owner": str(result.responsible),
                        "fields": list(result.fields),
                        "metric_name": str(result.metric_name),
                        "metric_value": result.formatted_metric_value,
                        "explanation": str(result.explanation),
                        "resolution": str(result.resolution),
                        "status": "Open",
                        "timestamp": QDateTime.currentDateTime(),
                        "is_unread": True,
                    }
                )

        self.state.issues = issues
        self.state.selected_run_id = next_id
        self.state.issuesChanged.emit()

        self.state.stateChanged.emit()

        self.state.runs.append(
            {
                "run_id": next_id,
                "datetime": QDateTime.currentDateTime(),
                "issues_count": len(issues),
                "issues": list(issues),
            }
        )
        self.state.runsChanged.emit()

        self.state.stateChanged.emit()
        try:
            self.state.save_run_state_to_disk()
        except Exception:
            pass
