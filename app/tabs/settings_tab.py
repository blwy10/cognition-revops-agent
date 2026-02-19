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
from rules.rule_setting_field import RuleSettingField
from app.state import AppState
from rules.default_rules import (
    acct_per_rep as acct_per_rep_rule,
    amount_outlier as amount_outlier_rule,
    missing_close_date as missing_close_date_rule,
    pipeline_imbalance as pipeline_imbalance_rule,
    portfolio_early_stage_concentration as portfolio_early_stage_concentration_rule,
    rep_early_stage_concentration as rep_early_stage_concentration_rule,
    slipping as slipping_rule,
    stale as stale_rule,
    undercover_tam as undercover_tam_rule,
)


class SettingsTab(QWidget):
    def __init__(self, state: AppState, parent: Optional[QObject] = None) -> None:
        super().__init__(parent)
        self.state = state
        self._settings = QSettings("cognition", "revops-analysis-agent")
        self._settings_group = "settings_tab"

        persistenceGroup = self._build_persistence_group()

        contentWidget = QWidget()
        contentLayout = QVBoxLayout(contentWidget)
        contentLayout.addWidget(persistenceGroup)

        for group in self._build_rule_settings_groups(
            rule_modules=[
                undercover_tam_rule,
                stale_rule,
                amount_outlier_rule,
                missing_close_date_rule,
                portfolio_early_stage_concentration_rule,
                rep_early_stage_concentration_rule,
                pipeline_imbalance_rule,
                acct_per_rep_rule,
                slipping_rule,
            ]
        ):
            contentLayout.addWidget(group)

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

    def _build_rule_settings_group(self, title: str, fields: list[RuleSettingField]) -> QGroupBox:
        group = QGroupBox(title)
        layout = QVBoxLayout(group)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        form = QFormLayout()
        form.setHorizontalSpacing(10)
        form.setVerticalSpacing(8)

        for field in fields:
            spinbox = QSpinBox()
            spinbox.setRange(int(field.minimum), int(field.maximum))
            spinbox.setValue(int(field.default))
            self._bind_rule_spinbox(spinbox, field.key)
            form.addRow(field.label, spinbox)

        layout.addLayout(form)
        layout.addStretch(1)
        return group

    def _build_rule_settings_groups(self, rule_modules: list[object]) -> list[QGroupBox]:
        groups: list[QGroupBox] = []
        for module in rule_modules:
            title = getattr(module, "RULE_SETTINGS_GROUP", None)
            fields = getattr(module, "RULE_SETTINGS_FIELDS", None)
            if not isinstance(title, str) or not isinstance(fields, list) or not fields:
                continue
            groups.append(self._build_rule_settings_group(title, fields))
        return groups

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
