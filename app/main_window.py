from __future__ import annotations

from typing import Optional

from PySide6.QtWidgets import QMainWindow, QTabWidget

from app.state import AppState
from app.tabs.data_generator_tab import DataGeneratorTab
from app.tabs.inbox_tab import InboxTab
from app.tabs.previous_runs_tab import PreviousRunsTab
from app.tabs.run_tab import RunTab
from app.tabs.settings_tab import SettingsTab


class MainWindow(QMainWindow):
    def __init__(self, parent: Optional[QMainWindow] = None) -> None:
        super().__init__(parent)

        self.setWindowTitle("RevOps Analysis Agent (Skeleton)")
        self.resize(1200, 800)

        self.state = AppState(self)
        self.state.seed_demo_data()

        self.tabs = QTabWidget(self)
        self.setCentralWidget(self.tabs)

        self.data_generator_tab = DataGeneratorTab(self.state, self)
        self.run_tab = RunTab(self.state, self)
        self.settings_tab = SettingsTab(self.state, self)
        self.previous_runs_tab = PreviousRunsTab(self.state, self)
        self.inbox_tab = InboxTab(self.state, self)

        self._tab_name_to_index: dict[str, int] = {}
        self._add_tab(self.data_generator_tab, "Data Generator")
        self._add_tab(self.run_tab, "Run")
        self._add_tab(self.settings_tab, "Settings")
        self._add_tab(self.previous_runs_tab, "Previous Runs")
        self._add_tab(self.inbox_tab, "Inbox")

        self.state.requestTabChange.connect(self._on_request_tab_change)

    def _add_tab(self, widget, name: str) -> None:
        index = self.tabs.addTab(widget, name)
        self._tab_name_to_index[name] = index

    def _on_request_tab_change(self, tab_name: str) -> None:
        index = self._tab_name_to_index.get(tab_name)
        if index is None:
            return
        self.tabs.setCurrentIndex(index)
