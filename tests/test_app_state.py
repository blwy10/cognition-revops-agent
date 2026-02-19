"""Tests for app.state module."""
import json
import os
import tempfile

import pytest
from PySide6.QtCore import QDateTime, Qt

from app.state import AppState


@pytest.fixture()
def state(qtbot):
    """Create a fresh AppState for each test."""
    s = AppState()
    # AppState is a QObject (not QWidget), so we register it for cleanup manually
    qtbot.addWidget  # ensure qtbot is active (Qt app running)
    yield s
    s.deleteLater()


class TestAppStateInit:
    def test_initial_dataset_none(self, state):
        assert state.dataset is None

    def test_initial_lists_empty(self, state):
        assert state.reps == []
        assert state.accounts == []
        assert state.opportunities == []
        assert state.territories == []
        assert state.opportunity_history == []
        assert state.runs == []
        assert state.issues == []

    def test_initial_selected_run_none(self, state):
        assert state.selected_run_id is None


class TestLoadedDataPath:
    def test_set_and_get(self, state):
        state.loaded_data_path = "/tmp/test.json"
        assert state.loaded_data_path == "/tmp/test.json"

    def test_set_none(self, state):
        state.loaded_data_path = "/tmp/test.json"
        state.loaded_data_path = None
        assert state.loaded_data_path is None

    def test_set_empty_string_becomes_none(self, state):
        state.loaded_data_path = ""
        assert state.loaded_data_path is None

    def test_signal_emitted(self, state, qtbot):
        with qtbot.waitSignal(state.loadedDataChanged, timeout=500):
            state.loaded_data_path = "/tmp/new.json"

    def test_no_signal_on_same_value(self, state, qtbot):
        state.loaded_data_path = "/tmp/same.json"
        with qtbot.assertNotEmitted(state.loadedDataChanged, wait=100):
            state.loaded_data_path = "/tmp/same.json"


class TestOutputDataPath:
    def test_set_and_get(self, state):
        state.output_data_path = "/tmp/output.json"
        assert state.output_data_path == "/tmp/output.json"

    def test_signal_emitted(self, state, qtbot):
        with qtbot.waitSignal(state.outputPathChanged, timeout=500):
            state.output_data_path = "/tmp/new_output.json"


class TestRunJsonPath:
    def test_default_path_is_string(self, state):
        assert isinstance(state.run_json_path, str)
        assert len(state.run_json_path) > 0

    def test_set_path(self, state):
        state.run_json_path = "/tmp/custom_run.json"
        assert state.run_json_path == "/tmp/custom_run.json"

    def test_empty_resets_to_default(self, state):
        default = state.get_default_run_json_path()
        state.run_json_path = ""
        assert state.run_json_path == default

    def test_signal_emitted(self, state, qtbot):
        with qtbot.waitSignal(state.runJsonPathChanged, timeout=500):
            state.run_json_path = "/tmp/signal_test.json"


class TestLoadJsonData:
    def test_loads_all_fields(self, state, tmp_path):
        data = {
            "reps": [{"id": 1, "name": "Alice"}],
            "accounts": [{"id": 1, "name": "Acme", "repId": 1}],
            "opportunities": [{"id": 1, "name": "Deal", "repId": 1, "accountId": 1, "created_date": "2026-01-01"}],
            "territories": [{"id": 1, "name": "West"}],
            "opportunity_history": [{"id": 1, "opportunity_id": 1, "field_name": "stage", "change_date": "2026-01-15"}],
        }
        f = tmp_path / "data.json"
        f.write_text(json.dumps(data))
        state.load_json_data(str(f))

        assert len(state.reps) == 1
        assert len(state.accounts) == 1
        assert len(state.opportunities) == 1
        assert len(state.territories) == 1
        assert len(state.opportunity_history) == 1
        assert state.dataset is not None

    def test_adds_owner_to_opportunities(self, state, tmp_path):
        data = {
            "reps": [{"id": 1, "name": "Alice"}],
            "accounts": [],
            "opportunities": [{"id": 1, "name": "Deal", "repId": 1, "accountId": 1}],
            "territories": [],
            "opportunity_history": [],
        }
        f = tmp_path / "data.json"
        f.write_text(json.dumps(data))
        state.load_json_data(str(f))
        assert state.opportunities[0].owner == "Alice"

    def test_adds_account_name_to_opportunities(self, state, tmp_path):
        data = {
            "reps": [{"id": 1, "name": "Alice"}],
            "accounts": [{"id": 1, "name": "Acme Corp", "repId": 1}],
            "opportunities": [{"id": 1, "name": "Deal", "repId": 1, "accountId": 1}],
            "territories": [],
            "opportunity_history": [],
        }
        f = tmp_path / "data.json"
        f.write_text(json.dumps(data))
        state.load_json_data(str(f))
        assert state.opportunities[0].account_name == "Acme Corp"

    def test_adds_owner_to_accounts(self, state, tmp_path):
        data = {
            "reps": [{"id": 1, "name": "Alice"}],
            "accounts": [{"id": 1, "name": "Acme", "repId": 1}],
            "opportunities": [],
            "territories": [],
            "opportunity_history": [],
        }
        f = tmp_path / "data.json"
        f.write_text(json.dumps(data))
        state.load_json_data(str(f))
        assert state.accounts[0].owner == "Alice"

    def test_signal_emitted(self, state, tmp_path, qtbot):
        data = {"reps": [], "accounts": [], "opportunities": [], "territories": [], "opportunity_history": []}
        f = tmp_path / "data.json"
        f.write_text(json.dumps(data))
        with qtbot.waitSignal(state.datasetChanged, timeout=500):
            state.load_json_data(str(f))

    def test_missing_file_raises(self, state):
        with pytest.raises(FileNotFoundError):
            state.load_json_data("/nonexistent/data.json")

    def test_missing_keys_default_to_empty(self, state, tmp_path):
        f = tmp_path / "data.json"
        f.write_text(json.dumps({}))
        state.load_json_data(str(f))
        assert state.reps == []
        assert state.accounts == []


class TestSaveAndLoadRunState:
    def test_round_trip(self, state, tmp_path):
        path = str(tmp_path / "run.json")
        state.runs = [
            {"run_id": 1, "datetime": QDateTime.currentDateTime(), "issues_count": 2, "issues": [
                {"severity": "HIGH", "name": "Test", "status": "Open",
                 "timestamp": QDateTime.currentDateTime()},
                {"severity": "LOW", "name": "Test2", "status": "Resolved",
                 "timestamp": QDateTime.currentDateTime()},
            ]},
        ]
        state.selected_run_id = 1
        state.save_run_state_to_disk(path)

        assert os.path.exists(path)

        state2 = AppState()
        loaded = state2.load_run_state_from_disk(path)
        assert loaded is True
        assert len(state2.runs) == 1
        assert state2.selected_run_id == 1
        assert len(state2.issues) == 2

    def test_load_nonexistent_returns_false(self, state):
        result = state.load_run_state_from_disk("/nonexistent/run.json")
        assert result is False

    def test_save_creates_file(self, state, tmp_path):
        path = str(tmp_path / "new_run.json")
        state.runs = []
        state.save_run_state_to_disk(path)
        assert os.path.exists(path)

    def test_saved_json_structure(self, state, tmp_path):
        path = str(tmp_path / "run.json")
        state.runs = [{"run_id": 1, "datetime": QDateTime.currentDateTime(), "issues_count": 0, "issues": []}]
        state.selected_run_id = 1
        state.save_run_state_to_disk(path)

        with open(path, "r") as f:
            payload = json.load(f)
        assert payload["schema"] == "revops-agent-run"
        assert "runs" in payload
        assert "selectedRun" in payload


class TestJsonFriendly:
    def test_qdatetime_converted(self, state):
        dt = QDateTime.currentDateTime()
        result = state._json_friendly(dt)
        assert isinstance(result, str)

    def test_dict_recursive(self, state):
        data = {"nested": {"dt": QDateTime.currentDateTime()}}
        result = state._json_friendly(data)
        assert isinstance(result["nested"]["dt"], str)

    def test_list_recursive(self, state):
        data = [QDateTime.currentDateTime()]
        result = state._json_friendly(data)
        assert isinstance(result[0], str)

    def test_plain_values_unchanged(self, state):
        assert state._json_friendly(42) == 42
        assert state._json_friendly("hello") == "hello"
