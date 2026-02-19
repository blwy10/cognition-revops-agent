from __future__ import annotations

from typing import Optional

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QMainWindow, QMessageBox, QTabWidget

from app.state import AppState
from app.tabs.data_generator_tab import DataGeneratorTab
from app.tabs.inbox_tab import InboxTab
from app.tabs.previous_runs_tab import PreviousRunsTab
from app.tabs.run_tab import RunTab
from app.tabs.settings_tab import SettingsTab

import os


class MainWindow(QMainWindow):
    def __init__(self, parent: Optional[QMainWindow] = None) -> None:
        super().__init__(parent)

        self.setWindowTitle("RevOps Analysis Agent (Skeleton)")
        self.resize(1200, 800)

        self.state = AppState(self)

        self.tabs = QTabWidget(self)
        self.setCentralWidget(self.tabs)

        self.data_generator_tab = DataGeneratorTab(self.state, self)
        self.run_tab = RunTab(self.state, self)
        self.settings_tab = SettingsTab(self.state, self)
        self.previous_runs_tab = PreviousRunsTab(self.state, self)
        self.inbox_tab = InboxTab(self.state, self)

        self._persist_timer = QTimer(self)
        self._persist_timer.setSingleShot(True)
        self._persist_timer.setInterval(250)
        self._persist_timer.timeout.connect(self._persist_run_state)

        self._tab_name_to_index: dict[str, int] = {}
        self._add_tab(self.data_generator_tab, "Data Generator")
        self._add_tab(self.run_tab, "Run")
        self._add_tab(self.settings_tab, "Settings")
        self._add_tab(self.previous_runs_tab, "Previous Runs")
        self._add_tab(self.inbox_tab, "Inbox")

        self.state.requestTabChange.connect(self._on_request_tab_change)

        self.state.issuesChanged.connect(self._schedule_persist)
        self.state.runsChanged.connect(self._schedule_persist)
        self.state.stateChanged.connect(self._schedule_persist)

        self._load_run_state_on_startup()
        self._load_data_on_startup()

    def _load_data_on_startup(self) -> None:
        path = self.state.loaded_data_path
        if not path:
            return
        if not os.path.exists(path):
            self.state.loaded_data_path = None
            return

        try:
            self.state.load_json_data(path)
        except Exception as e:
            QMessageBox.warning(
                self,
                "Invalid Data JSON",
                f"Could not load data from:\n{path}\n\nError: {e}\n\nThe saved path will be cleared.",
            )
            self.state.loaded_data_path = None
            return

    def _load_run_state_on_startup(self) -> None:
        try:
            loaded = self.state.load_run_state_from_disk()
        except Exception as e:
            QMessageBox.warning(
                self,
                "Invalid Run JSON",
                f"Could not load run state from:\n{self.state.run_json_path}\n\nError: {e}\n\nThe path will be reset to the default.",
            )
            self.state.run_json_path = self.state.get_default_run_json_path()
            return

        if not loaded:
            return

        self.state.runsChanged.emit()
        self.state.issuesChanged.emit()
        self.previous_runs_tab._rebuild_model()
        self.inbox_tab._rebuild_model()

    def _schedule_persist(self) -> None:
        if self._persist_timer.isActive():
            self._persist_timer.stop()
        self._persist_timer.start()

    def _persist_run_state(self) -> None:
        try:
            self.state.save_run_state_to_disk()
        except Exception:
            return

    def _add_tab(self, widget, name: str) -> None:
        index = self.tabs.addTab(widget, name)
        self._tab_name_to_index[name] = index

    def _on_request_tab_change(self, tab_name: str) -> None:
        index = self._tab_name_to_index.get(tab_name)
        if index is None:
            return
        self.tabs.setCurrentIndex(index)

    def closeEvent(self, event) -> None:
        try:
            self.state.save_run_state_to_disk()
        except Exception:
            pass
        super().closeEvent(event)
