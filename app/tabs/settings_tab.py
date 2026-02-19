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

from app.rule_settings import RuleSettings
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

        layout = QVBoxLayout(self)
        layout.addWidget(tamGroup)
        layout.addStretch(1)
