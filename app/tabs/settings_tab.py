from __future__ import annotations

from typing import Optional

from PySide6.QtCore import QObject
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFormLayout,
    QLineEdit,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from app.state import AppState


class SettingsTab(QWidget):
    def __init__(self, state: AppState, parent: Optional[QObject] = None) -> None:
        super().__init__(parent)
        self.state = state

        outer = QVBoxLayout(self)
        outer.setContentsMargins(16, 16, 16, 16)
        outer.setSpacing(12)
        form = QFormLayout()
        form.setHorizontalSpacing(10)
        form.setVerticalSpacing(8)

        workspace = QLineEdit("Default Workspace")
        model = QComboBox()
        model.addItems(["Fast", "Balanced", "Thorough"])
        max_records = QSpinBox()
        max_records.setRange(1, 1_000_000)
        max_records.setValue(5000)
        notify = QCheckBox("Enable notifications")
        notify.setChecked(True)

        form.addRow("Workspace", workspace)
        form.addRow("Mode", model)
        form.addRow("Max records", max_records)
        form.addRow("Notifications", notify)

        outer.addLayout(form)
        outer.addStretch(1)
