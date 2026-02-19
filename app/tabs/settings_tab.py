from __future__ import annotations

from typing import Optional

from PySide6.QtCore import QObject
from PySide6.QtWidgets import (
    QFormLayout,
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

        layout = QVBoxLayout(self)
        layout.addWidget(tamGroup)
        layout.addWidget(staleGroup)
        layout.addStretch(1)
