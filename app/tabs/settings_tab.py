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

        # Each group below corresponds to a “rule” or a feature area. The widgets here
        # only control thresholds/parameters; the actual analysis behavior lives in the
        # corresponding rule implementations under `rules/`.
        persistenceGroup = self._build_persistence_group()

        # Business assumptions used by the TAM-related rule.
        tamGroup = self._build_tam_group()

        # Thresholds for flagging stale opportunities.
        staleGroup = self._build_stale_group()

        # Thresholds for unusually large/small opportunity amounts.
        amountOutlierGroup = self._build_amount_outlier_group()

        # Rules around missing close dates by stage.
        missingCloseDateGroup = self._build_missing_close_date_group()

        # Portfolio-level concentration of early-stage pipeline.
        portfolioEarlyStageGroup = self._build_portfolio_early_stage_group()

        # Rep-level concentration of early-stage pipeline.
        repEarlyStageGroup = self._build_rep_early_stage_group()

        # Rep-level “pipeline imbalance” thresholds.
        repPipelineImbalanceGroup = self._build_pipeline_imbalance_group()

        # Rep ownership load thresholds (accounts per rep).
        acctPerRepGroup = self._build_acct_per_rep_group()

        # Thresholds for “slipping” opportunities (postponements at late stage).
        slippingGroup = self._build_slipping_group()

        contentWidget = QWidget()
        contentLayout = QVBoxLayout(contentWidget)
        contentLayout.addWidget(persistenceGroup)
        contentLayout.addWidget(tamGroup)
        contentLayout.addWidget(staleGroup)
        contentLayout.addWidget(amountOutlierGroup)
        contentLayout.addWidget(missingCloseDateGroup)
        contentLayout.addWidget(portfolioEarlyStageGroup)
        contentLayout.addWidget(repEarlyStageGroup)
        contentLayout.addWidget(repPipelineImbalanceGroup)
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
        # Namespace rule settings under this tab so QSettings keys don't collide.
        return f"{self._settings_group}/rule_settings/{key}"

    def _load_int_setting(self, key: str) -> Optional[int]:
        # Read persisted integer settings (if present). Any parsing errors fall back
        # to defaults (by returning None so callers can keep their initial values).
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
        # Persist user-chosen thresholds so the UI comes back with the same values.
        self._settings.setValue(self._rule_settings_key(key), int(value))

    def _bind_rule_spinbox(self, spinbox: QSpinBox, key: str) -> None:
        # Central binding helper:
        # - Initialize UI from persisted settings (if any)
        # - Update `RuleSettings` immediately so the next run uses the new values
        # - Persist edits back to QSettings
        stored = self._load_int_setting(key)
        if stored is not None:
            spinbox.setValue(int(stored))

        RuleSettings.set(key, int(spinbox.value()))

        def _on_changed(v: int) -> None:
            RuleSettings.set(key, int(v))
            self._persist_int_setting(key, int(v))

        spinbox.valueChanged.connect(_on_changed)

    def _build_persistence_group(self) -> QGroupBox:
        # Controls where the app reads/writes run state (the JSON file used to
        # persist the last run and allow resuming / reloading).
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
        # Parameters used for TAM computation/heuristics (e.g. revenue assumptions).
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

        tamCoverageLowPct = QSpinBox()
        tamCoverageLowPct.setRange(0, 100)
        tamCoverageLowPct.setValue(60)

        tamCoverageMediumPct = QSpinBox()
        tamCoverageMediumPct.setRange(0, 100)
        tamCoverageMediumPct.setValue(50)

        tamCoverageHighPct = QSpinBox()
        tamCoverageHighPct.setRange(0, 100)
        tamCoverageHighPct.setValue(40)

        self._bind_rule_spinbox(revPerDev, "tam.revenue_per_developer")
        self._bind_rule_spinbox(coveragePct, "tam.coverage_percentage")
        self._bind_rule_spinbox(tamCoverageLowPct, "tam.coverage_low_severity_pct")
        self._bind_rule_spinbox(tamCoverageMediumPct, "tam.coverage_medium_severity_pct")
        self._bind_rule_spinbox(tamCoverageHighPct, "tam.coverage_high_severity_pct")

        tamForm.addRow("Revenue per developer", revPerDev)
        tamForm.addRow("Coverage percentage", coveragePct)
        tamForm.addRow("TAM coverage threshold (LOW severity)", tamCoverageLowPct)
        tamForm.addRow("TAM coverage threshold (MEDIUM severity)", tamCoverageMediumPct)
        tamForm.addRow("TAM coverage threshold (HIGH severity)", tamCoverageHighPct)

        tamLayout.addLayout(tamForm)
        tamLayout.addStretch(1)
        return tamGroup

    def _build_stale_group(self) -> QGroupBox:
        # Days-since-last-activity thresholds used to classify “stale” pipeline.
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

    def _build_amount_outlier_group(self) -> QGroupBox:
        # Upper/lower amount thresholds that trigger outlier flags at different severities.
        amountOutlierGroup = QGroupBox("Amount Outlier Settings")
        amountOutlierLayout = QVBoxLayout(amountOutlierGroup)
        amountOutlierLayout.setContentsMargins(16, 16, 16, 16)
        amountOutlierLayout.setSpacing(12)

        amountOutlierForm = QFormLayout()
        amountOutlierForm.setHorizontalSpacing(10)
        amountOutlierForm.setVerticalSpacing(8)

        highLow = QSpinBox()
        highLow.setRange(0, 100000000)
        highLow.setValue(300000)

        highMedium = QSpinBox()
        highMedium.setRange(0, 100000000)
        highMedium.setValue(600000)

        highHigh = QSpinBox()
        highHigh.setRange(0, 100000000)
        highHigh.setValue(1000000)

        lowLow = QSpinBox()
        lowLow.setRange(0, 100000000)
        lowLow.setValue(60000)

        lowMedium = QSpinBox()
        lowMedium.setRange(0, 100000000)
        lowMedium.setValue(30000)

        lowHigh = QSpinBox()
        lowHigh.setRange(0, 100000000)
        lowHigh.setValue(20000)

        self._bind_rule_spinbox(highLow, "amount_outlier.high_low_threshold")
        self._bind_rule_spinbox(highMedium, "amount_outlier.high_medium_threshold")
        self._bind_rule_spinbox(highHigh, "amount_outlier.high_high_threshold")
        self._bind_rule_spinbox(lowLow, "amount_outlier.low_low_threshold")
        self._bind_rule_spinbox(lowMedium, "amount_outlier.low_medium_threshold")
        self._bind_rule_spinbox(lowHigh, "amount_outlier.low_high_threshold")

        amountOutlierForm.addRow("High outlier threshold (LOW severity)", highLow)
        amountOutlierForm.addRow("High outlier threshold (MEDIUM severity)", highMedium)
        amountOutlierForm.addRow("High outlier threshold (HIGH severity)", highHigh)
        amountOutlierForm.addRow("Low-end threshold (LOW severity)", lowLow)
        amountOutlierForm.addRow("Low-end threshold (MEDIUM severity)", lowMedium)
        amountOutlierForm.addRow("Low-end threshold (HIGH severity)", lowHigh)

        amountOutlierLayout.addLayout(amountOutlierForm)
        amountOutlierLayout.addStretch(1)
        return amountOutlierGroup

    def _build_missing_close_date_group(self) -> QGroupBox:
        # Controls when a missing close date becomes noteworthy, based on stage.
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
        # Portfolio-level percentage of pipeline in early stages.
        # Higher percentages can indicate over-weighting in early-stage deals.
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
        # Rep-level early-stage concentration plus a minimum opp count so the rule
        # doesn't overreact to tiny pipelines.
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

    def _build_pipeline_imbalance_group(self) -> QGroupBox:
        # Rep-level pipeline imbalance thresholds. Interpreted by the corresponding rule
        # to identify reps whose pipeline distribution is skewed beyond these limits.
        lowThreshold = QSpinBox()
        lowThreshold.setRange(0, 10000000)
        lowThreshold.setValue(500000)

        mediumThreshold = QSpinBox()
        mediumThreshold.setRange(0, 10000000)
        mediumThreshold.setValue(600000)

        highThreshold = QSpinBox()
        highThreshold.setRange(0, 10000000)
        highThreshold.setValue(800000)

        self._bind_rule_spinbox(lowThreshold, "rep_pipeline_imbalance.low_severity")
        self._bind_rule_spinbox(mediumThreshold, "rep_pipeline_imbalance.medium_severity")
        self._bind_rule_spinbox(highThreshold, "rep_pipeline_imbalance.high_severity")

        pipelineImbalanceForm = QFormLayout()
        pipelineImbalanceForm.setHorizontalSpacing(10)
        pipelineImbalanceForm.setVerticalSpacing(8)
        pipelineImbalanceForm.addRow(
            "Rep pipeline imbalance threshold (low severity)",
            lowThreshold,
        )
        pipelineImbalanceForm.addRow(
            "Rep pipeline imbalance threshold (medium severity)",
            mediumThreshold,
        )
        pipelineImbalanceForm.addRow(
            "Rep pipeline imbalance threshold (high severity)",
            highThreshold,
        )

        pipelineImbalanceGroup = QGroupBox("Rep pipeline imbalance")
        pipelineImbalanceLayout = QVBoxLayout(pipelineImbalanceGroup)
        pipelineImbalanceLayout.setContentsMargins(16, 16, 16, 16)
        pipelineImbalanceLayout.setSpacing(12)
        pipelineImbalanceLayout.addLayout(pipelineImbalanceForm)
        pipelineImbalanceLayout.addStretch(1)
        return pipelineImbalanceGroup

    def _build_acct_per_rep_group(self) -> QGroupBox:
        # Thresholds for flagging unusually high account ownership per rep.
        acctPerRepLow = QSpinBox()
        acctPerRepLow.setRange(0, 100)
        acctPerRepLow.setValue(6)

        acctPerRepMedium = QSpinBox()
        acctPerRepMedium.setRange(0, 100)
        acctPerRepMedium.setValue(10)

        acctPerRepHigh = QSpinBox()
        acctPerRepHigh.setRange(0, 100)
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
        # Thresholds for opportunities that keep getting pushed out (“slipping”).
        # The late-stage value gates when postponements become noteworthy.
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
