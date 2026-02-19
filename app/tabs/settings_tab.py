from __future__ import annotations

from typing import Optional

from PySide6.QtCore import QObject
from PySide6.QtWidgets import (
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLineEdit,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
    QGroupBox,
)

from rules.rule_settings import RuleSettings
from app.state import AppState


class SettingsTab(QWidget):
    def __init__(self, state: AppState, parent: Optional[QObject] = None) -> None:
        super().__init__(parent)
        self.state = state

        persistenceGroup = QGroupBox("Run State Persistence")
        persistenceLayout = QVBoxLayout(persistenceGroup)
        persistenceLayout.setContentsMargins(16, 16, 16, 16)
        persistenceLayout.setSpacing(12)

        persistenceForm = QFormLayout()
        persistenceForm.setHorizontalSpacing(10)
        persistenceForm.setVerticalSpacing(8)

        path_row = QHBoxLayout()
        self.run_json_path_edit = QLineEdit()
        self.run_json_path_edit.setText(self.state.run_json_path)
        self.run_json_browse = QPushButton("Browse…")
        self.run_json_reset = QPushButton("Reset to default")
        path_row.addWidget(self.run_json_path_edit, 1)
        path_row.addWidget(self.run_json_browse)
        path_row.addWidget(self.run_json_reset)

        persistenceForm.addRow("Run JSON file", path_row)
        persistenceLayout.addLayout(persistenceForm)
        persistenceLayout.addStretch(1)

        tamGroup = QGroupBox("TAM Settings")

        tamLayout = QVBoxLayout(tamGroup)
        tamLayout.setContentsMargins(16, 16, 16, 16)
        tamLayout.setSpacing(12)
        tamForm = QFormLayout()
        tamForm.setHorizontalSpacing(10)
        tamForm.setVerticalSpacing(8)

        revPerDev = QSpinBox()
        revPerDev.setRange(0, 2000)
        revPerDev.setValue(1000)
        coveragePct = QSpinBox()
        coveragePct.setRange(0, 100)
        coveragePct.setValue(50)

        RuleSettings.set("tam.revenue_per_developer", revPerDev.value())
        RuleSettings.set("tam.coverage_percentage", coveragePct.value())

        revPerDev.valueChanged.connect(
            lambda v: RuleSettings.set("tam.revenue_per_developer", int(v))
        )
        coveragePct.valueChanged.connect(
            lambda v: RuleSettings.set("tam.coverage_percentage", int(v))
        )

        tamForm.addRow("Revenue per developer", revPerDev)
        tamForm.addRow("Coverage percentage", coveragePct)

        tamLayout.addLayout(tamForm)
        tamLayout.addStretch(1)

        staleGroup = QGroupBox("Stale Opportunity Settings")

        staleLayout = QVBoxLayout(staleGroup)
        staleLayout.setContentsMargins(16, 16, 16, 16)
        staleLayout.setSpacing(12)
        staleForm = QFormLayout()
        staleForm.setHorizontalSpacing(10)
        staleForm.setVerticalSpacing(8)

        staleLowDays = QSpinBox()
        staleLowDays.setRange(0, 365)
        staleLowDays.setValue(30)

        staleMediumDays = QSpinBox()
        staleMediumDays.setRange(0, 365)
        staleMediumDays.setValue(60)

        staleHighDays = QSpinBox()
        staleHighDays.setRange(0, 365)
        staleHighDays.setValue(90)

        RuleSettings.set("stale_opportunity.low_days", staleLowDays.value())
        RuleSettings.set("stale_opportunity.medium_days", staleMediumDays.value())
        RuleSettings.set("stale_opportunity.high_days", staleHighDays.value())

        staleLowDays.valueChanged.connect(
            lambda v: RuleSettings.set("stale_opportunity.low_days", int(v))
        )

        staleMediumDays.valueChanged.connect(
            lambda v: RuleSettings.set("stale_opportunity.medium_days", int(v))
        )

        staleHighDays.valueChanged.connect(
            lambda v: RuleSettings.set("stale_opportunity.high_days", int(v))
        )

        staleForm.addRow("Stale days (low)", staleLowDays)
        staleForm.addRow("Stale days (medium)", staleMediumDays)
        staleForm.addRow("Stale days (high)", staleHighDays)

        staleLayout.addLayout(staleForm)
        staleLayout.addStretch(1)

        missingCloseDateGroup = QGroupBox("Missing Close Date Settings")

        missingCloseDateLayout = QVBoxLayout(missingCloseDateGroup)
        missingCloseDateLayout.setContentsMargins(16, 16, 16, 16)
        missingCloseDateLayout.setSpacing(12)
        missingCloseDateForm = QFormLayout()
        missingCloseDateForm.setHorizontalSpacing(10)
        missingCloseDateForm.setVerticalSpacing(8)

        missingCloseDateLowMaxStage = QSpinBox()
        missingCloseDateLowMaxStage.setRange(0, 6)
        missingCloseDateLowMaxStage.setValue(1)

        missingCloseDateMediumMaxStage = QSpinBox()
        missingCloseDateMediumMaxStage.setRange(0, 6)
        missingCloseDateMediumMaxStage.setValue(2)

        RuleSettings.set("missing_close_date.low_max_stage", missingCloseDateLowMaxStage.value())
        RuleSettings.set(
            "missing_close_date.medium_max_stage", missingCloseDateMediumMaxStage.value()
        )

        missingCloseDateLowMaxStage.valueChanged.connect(
            lambda v: RuleSettings.set("missing_close_date.low_max_stage", int(v))
        )
        missingCloseDateMediumMaxStage.valueChanged.connect(
            lambda v: RuleSettings.set("missing_close_date.medium_max_stage", int(v))
        )

        missingCloseDateForm.addRow(
            "Highest stage for LOW severity", missingCloseDateLowMaxStage
        )
        missingCloseDateForm.addRow(
            "Highest stage for MEDIUM severity", missingCloseDateMediumMaxStage
        )

        missingCloseDateLayout.addLayout(missingCloseDateForm)
        missingCloseDateLayout.addStretch(1)

        portfolioEarlyLowPct = QSpinBox()
        portfolioEarlyLowPct.setRange(0, 100)
        portfolioEarlyLowPct.setValue(35)

        portfolioEarlyMediumPct = QSpinBox()
        portfolioEarlyMediumPct.setRange(0, 100)
        portfolioEarlyMediumPct.setValue(45)

        portfolioEarlyHighPct = QSpinBox()
        portfolioEarlyHighPct.setRange(0, 100)
        portfolioEarlyHighPct.setValue(60)

        RuleSettings.set(
            "portfolio_early_stage_concentration.low_pct",
            portfolioEarlyLowPct.value(),
        )
        RuleSettings.set(
            "portfolio_early_stage_concentration.medium_pct",
            portfolioEarlyMediumPct.value(),
        )
        RuleSettings.set(
            "portfolio_early_stage_concentration.high_pct",
            portfolioEarlyHighPct.value(),
        )

        portfolioEarlyLowPct.valueChanged.connect(
            lambda v: RuleSettings.set(
                "portfolio_early_stage_concentration.low_pct", int(v)
            )
        )
        portfolioEarlyMediumPct.valueChanged.connect(
            lambda v: RuleSettings.set(
                "portfolio_early_stage_concentration.medium_pct", int(v)
            )
        )
        portfolioEarlyHighPct.valueChanged.connect(
            lambda v: RuleSettings.set(
                "portfolio_early_stage_concentration.high_pct", int(v)
            )
        )

        portfolioEarlyStageForm = QFormLayout()
        portfolioEarlyStageForm.setHorizontalSpacing(10)
        portfolioEarlyStageForm.setVerticalSpacing(8)
        portfolioEarlyStageForm.addRow("Low pct", portfolioEarlyLowPct)
        portfolioEarlyStageForm.addRow("Medium pct", portfolioEarlyMediumPct)
        portfolioEarlyStageForm.addRow("High pct", portfolioEarlyHighPct)

        portfolioEarlyStageGroup = QGroupBox("Portfolio Early Stage Concentration Settings")
        portfolioEarlyStageLayout = QVBoxLayout(portfolioEarlyStageGroup)
        portfolioEarlyStageLayout.setContentsMargins(16, 16, 16, 16)
        portfolioEarlyStageLayout.setSpacing(12)
        portfolioEarlyStageLayout.addLayout(portfolioEarlyStageForm)
        portfolioEarlyStageLayout.addStretch(1)

        layout = QVBoxLayout(self)
        layout.addWidget(persistenceGroup)
        layout.addWidget(tamGroup)
        layout.addWidget(staleGroup)
        layout.addWidget(missingCloseDateGroup)
        layout.addWidget(portfolioEarlyStageGroup)
        layout.addStretch(1)

        self.run_json_browse.clicked.connect(self._on_browse_run_json)
        self.run_json_reset.clicked.connect(self._on_reset_run_json)
        self.run_json_path_edit.editingFinished.connect(self._on_run_json_editing_finished)
        self.state.runJsonPathChanged.connect(self._on_state_run_json_path_changed)

    def _on_browse_run_json(self) -> None:
        path, _filter = QFileDialog.getSaveFileName(
            self,
            "Select Run JSON File",
            self.run_json_path_edit.text().strip() or self.state.run_json_path,
            "JSON Files (*.json)",
        )
        if not path:
            return
        self.state.run_json_path = path

    def _on_reset_run_json(self) -> None:
        self.state.run_json_path = self.state.get_default_run_json_path()

    def _on_run_json_editing_finished(self) -> None:
        self.state.run_json_path = self.run_json_path_edit.text().strip()

    def _on_state_run_json_path_changed(self, path: str) -> None:
        if self.run_json_path_edit.text().strip() != path:
            self.run_json_path_edit.setText(path)
