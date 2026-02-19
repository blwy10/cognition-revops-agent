from __future__ import annotations

from typing import Optional

from PySide6.QtCore import QObject, QSettings
from PySide6.QtWidgets import (
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLineEdit,
    QPushButton,
    QScrollArea,
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
        self._settings = QSettings("cognition", "revops-analysis-agent")
        self._settings_group = "settings_tab"

        persistenceGroup = self._build_persistence_group()
        tamGroup = self._build_tam_group()
        staleGroup = self._build_stale_group()
        missingCloseDateGroup = self._build_missing_close_date_group()
        portfolioEarlyStageGroup = self._build_portfolio_early_stage_group()
        repEarlyStageGroup = self._build_rep_early_stage_group()
        acctPerRepGroup = self._build_acct_per_rep_group()
        slippingGroup = self._build_slipping_group()

        contentWidget = QWidget()
        contentLayout = QVBoxLayout(contentWidget)
        contentLayout.addWidget(persistenceGroup)
        contentLayout.addWidget(tamGroup)
        contentLayout.addWidget(staleGroup)
        contentLayout.addWidget(missingCloseDateGroup)
        contentLayout.addWidget(portfolioEarlyStageGroup)
        contentLayout.addWidget(repEarlyStageGroup)
        contentLayout.addWidget(acctPerRepGroup)
        contentLayout.addWidget(slippingGroup)
        contentLayout.addStretch(1)

        scrollArea = QScrollArea()
        scrollArea.setWidgetResizable(True)
        scrollArea.setWidget(contentWidget)

        layout = QVBoxLayout(self)
        layout.addWidget(scrollArea)

        self.run_json_browse.clicked.connect(self._on_browse_run_json)
        self.run_json_reset.clicked.connect(self._on_reset_run_json)
        self.run_json_path_edit.editingFinished.connect(self._on_run_json_editing_finished)
        self.state.runJsonPathChanged.connect(self._on_state_run_json_path_changed)

    def _rule_settings_key(self, key: str) -> str:
        return f"{self._settings_group}/rule_settings/{key}"

    def _load_int_setting(self, key: str) -> Optional[int]:
        qkey = self._rule_settings_key(key)
        if not self._settings.contains(qkey):
            return None
        value = self._settings.value(qkey, None)
        if value is None:
            return None
        try:
            return int(value)
        except Exception:
            return None

    def _persist_int_setting(self, key: str, value: int) -> None:
        self._settings.setValue(self._rule_settings_key(key), int(value))

    def _bind_rule_spinbox(self, spinbox: QSpinBox, key: str) -> None:
        stored = self._load_int_setting(key)
        if stored is not None:
            spinbox.setValue(int(stored))

        RuleSettings.set(key, int(spinbox.value()))

        def _on_changed(v: int) -> None:
            RuleSettings.set(key, int(v))
            self._persist_int_setting(key, int(v))

        spinbox.valueChanged.connect(_on_changed)

    def _build_persistence_group(self) -> QGroupBox:
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
        return persistenceGroup

    def _build_tam_group(self) -> QGroupBox:
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

        self._bind_rule_spinbox(revPerDev, "tam.revenue_per_developer")
        self._bind_rule_spinbox(coveragePct, "tam.coverage_percentage")

        tamForm.addRow("Revenue per developer", revPerDev)
        tamForm.addRow("Coverage percentage", coveragePct)

        tamLayout.addLayout(tamForm)
        tamLayout.addStretch(1)
        return tamGroup

    def _build_stale_group(self) -> QGroupBox:
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

        self._bind_rule_spinbox(staleLowDays, "stale_opportunity.low_days")
        self._bind_rule_spinbox(staleMediumDays, "stale_opportunity.medium_days")
        self._bind_rule_spinbox(staleHighDays, "stale_opportunity.high_days")

        staleForm.addRow("Stale days (low)", staleLowDays)
        staleForm.addRow("Stale days (medium)", staleMediumDays)
        staleForm.addRow("Stale days (high)", staleHighDays)

        staleLayout.addLayout(staleForm)
        staleLayout.addStretch(1)
        return staleGroup

    def _build_missing_close_date_group(self) -> QGroupBox:
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

        self._bind_rule_spinbox(
            missingCloseDateLowMaxStage, "missing_close_date.low_max_stage"
        )
        self._bind_rule_spinbox(
            missingCloseDateMediumMaxStage, "missing_close_date.medium_max_stage"
        )

        missingCloseDateForm.addRow(
            "Highest stage for LOW severity", missingCloseDateLowMaxStage
        )
        missingCloseDateForm.addRow(
            "Highest stage for MEDIUM severity", missingCloseDateMediumMaxStage
        )

        missingCloseDateLayout.addLayout(missingCloseDateForm)
        missingCloseDateLayout.addStretch(1)
        return missingCloseDateGroup

    def _build_portfolio_early_stage_group(self) -> QGroupBox:
        portfolioEarlyLowPct = QSpinBox()
        portfolioEarlyLowPct.setRange(0, 100)
        portfolioEarlyLowPct.setValue(35)

        portfolioEarlyMediumPct = QSpinBox()
        portfolioEarlyMediumPct.setRange(0, 100)
        portfolioEarlyMediumPct.setValue(45)

        portfolioEarlyHighPct = QSpinBox()
        portfolioEarlyHighPct.setRange(0, 100)
        portfolioEarlyHighPct.setValue(60)

        self._bind_rule_spinbox(
            portfolioEarlyLowPct, "portfolio_early_stage_concentration.low_pct"
        )
        self._bind_rule_spinbox(
            portfolioEarlyMediumPct, "portfolio_early_stage_concentration.medium_pct"
        )
        self._bind_rule_spinbox(
            portfolioEarlyHighPct, "portfolio_early_stage_concentration.high_pct"
        )

        portfolioEarlyStageForm = QFormLayout()
        portfolioEarlyStageForm.setHorizontalSpacing(10)
        portfolioEarlyStageForm.setVerticalSpacing(8)
        portfolioEarlyStageForm.addRow("Low pct", portfolioEarlyLowPct)
        portfolioEarlyStageForm.addRow("Medium pct", portfolioEarlyMediumPct)
        portfolioEarlyStageForm.addRow("High pct", portfolioEarlyHighPct)

        portfolioEarlyStageGroup = QGroupBox(
            "Portfolio Early Stage Concentration Settings"
        )
        portfolioEarlyStageLayout = QVBoxLayout(portfolioEarlyStageGroup)
        portfolioEarlyStageLayout.setContentsMargins(16, 16, 16, 16)
        portfolioEarlyStageLayout.setSpacing(12)
        portfolioEarlyStageLayout.addLayout(portfolioEarlyStageForm)
        portfolioEarlyStageLayout.addStretch(1)
        return portfolioEarlyStageGroup

    def _build_rep_early_stage_group(self) -> QGroupBox:
        repEarlyLowPct = QSpinBox()
        repEarlyLowPct.setRange(0, 100)
        repEarlyLowPct.setValue(35)

        repEarlyMediumPct = QSpinBox()
        repEarlyMediumPct.setRange(0, 100)
        repEarlyMediumPct.setValue(45)

        repEarlyHighPct = QSpinBox()
        repEarlyHighPct.setRange(0, 100)
        repEarlyHighPct.setValue(60)

        self._bind_rule_spinbox(repEarlyLowPct, "rep_early_stage_concentration.low_pct")
        self._bind_rule_spinbox(
            repEarlyMediumPct, "rep_early_stage_concentration.medium_pct"
        )
        self._bind_rule_spinbox(repEarlyHighPct, "rep_early_stage_concentration.high_pct")

        repEarlyMinOpps = QSpinBox()
        repEarlyMinOpps.setRange(0, 10000)
        repEarlyMinOpps.setValue(10)

        self._bind_rule_spinbox(repEarlyMinOpps, "rep_early_stage_concentration.min_opps")

        repEarlyStageForm = QFormLayout()
        repEarlyStageForm.setHorizontalSpacing(10)
        repEarlyStageForm.setVerticalSpacing(8)
        repEarlyStageForm.addRow("Low pct", repEarlyLowPct)
        repEarlyStageForm.addRow("Medium pct", repEarlyMediumPct)
        repEarlyStageForm.addRow("High pct", repEarlyHighPct)
        repEarlyStageForm.addRow("Minimum opportunities", repEarlyMinOpps)

        repEarlyStageGroup = QGroupBox("Rep Early Stage Concentration Settings")
        repEarlyStageLayout = QVBoxLayout(repEarlyStageGroup)
        repEarlyStageLayout.setContentsMargins(16, 16, 16, 16)
        repEarlyStageLayout.setSpacing(12)
        repEarlyStageLayout.addLayout(repEarlyStageForm)
        repEarlyStageLayout.addStretch(1)
        return repEarlyStageGroup

    def _build_acct_per_rep_group(self) -> QGroupBox:
        acctPerRepLow = QSpinBox()
        acctPerRepLow.setRange(0, 10000)
        acctPerRepLow.setValue(6)

        acctPerRepMedium = QSpinBox()
        acctPerRepMedium.setRange(0, 10000)
        acctPerRepMedium.setValue(10)

        acctPerRepHigh = QSpinBox()
        acctPerRepHigh.setRange(0, 10000)
        acctPerRepHigh.setValue(15)

        self._bind_rule_spinbox(acctPerRepLow, "acct_per_rep.low_severity")
        self._bind_rule_spinbox(acctPerRepMedium, "acct_per_rep.medium_severity")
        self._bind_rule_spinbox(acctPerRepHigh, "acct_per_rep.high_severity")

        acctPerRepForm = QFormLayout()
        acctPerRepForm.setHorizontalSpacing(10)
        acctPerRepForm.setVerticalSpacing(8)
        acctPerRepForm.addRow(
            "Accounts owned > (low severity)",
            acctPerRepLow,
        )
        acctPerRepForm.addRow(
            "Accounts owned > (medium severity)",
            acctPerRepMedium,
        )
        acctPerRepForm.addRow(
            "Accounts owned > (high severity)",
            acctPerRepHigh,
        )

        acctPerRepGroup = QGroupBox("Accounts Per Rep Settings")
        acctPerRepLayout = QVBoxLayout(acctPerRepGroup)
        acctPerRepLayout.setContentsMargins(16, 16, 16, 16)
        acctPerRepLayout.setSpacing(12)
        acctPerRepLayout.addLayout(acctPerRepForm)
        acctPerRepLayout.addStretch(1)
        return acctPerRepGroup
    
    def _build_slipping_group(self) -> QGroupBox:
        slippingLateStage = QSpinBox()
        slippingLateStage.setRange(0, 6)
        slippingLateStage.setValue(5)

        self._bind_rule_spinbox(slippingLateStage, "slipping.late_stage")

        slippingLowSeverity = QSpinBox()
        slippingLowSeverity.setRange(0, 10)
        slippingLowSeverity.setValue(1)

        self._bind_rule_spinbox(slippingLowSeverity, "slipping.low_severity")

        slippingMediumSeverity = QSpinBox()
        slippingMediumSeverity.setRange(0, 10)
        slippingMediumSeverity.setValue(2)

        self._bind_rule_spinbox(slippingMediumSeverity, "slipping.medium_severity")

        slippingHighSeverity = QSpinBox()
        slippingHighSeverity.setRange(0, 10)
        slippingHighSeverity.setValue(3)

        self._bind_rule_spinbox(slippingHighSeverity, "slipping.high_severity")

        slippingGroup = QGroupBox("Slipping Opportunity Settings")
        slippingLayout = QVBoxLayout(slippingGroup)
        slippingLayout.setContentsMargins(16, 16, 16, 16)
        slippingLayout.setSpacing(12)
        slippingForm = QFormLayout()
        slippingForm.setHorizontalSpacing(10)
        slippingForm.setVerticalSpacing(8)
        slippingForm.addRow("Late stage threshold", slippingLateStage)
        slippingForm.addRow("Number of times postponed (low severity)", slippingLowSeverity)
        slippingForm.addRow("Number of times postponed (medium severity)", slippingMediumSeverity)
        slippingForm.addRow("Number of times postponed (high severity)", slippingHighSeverity)

        slippingLayout.addLayout(slippingForm)
        slippingLayout.addStretch(1)
        return slippingGroup
    
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
