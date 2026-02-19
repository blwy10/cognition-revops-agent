from __future__ import annotations

import json
import os
from pathlib import Path
from datetime import datetime, timezone
from typing import Any, Optional

from PySide6.QtCore import QDateTime, QObject, Qt, Signal, QSettings


class AppState(QObject):
    loadedDataChanged = Signal(str)
    outputPathChanged = Signal(str)
    datasetChanged = Signal()
    runsChanged = Signal()
    issuesChanged = Signal()
    stateChanged = Signal()
    runJsonPathChanged = Signal(str)
    requestTabChange = Signal(str)

    def __init__(self, parent: Optional[QObject] = None) -> None:
        super().__init__(parent)
        self._settings = QSettings("cognition", "revops-analysis-agent")
        stored_loaded_path = self._settings.value("loaded_data_path", "")
        loaded_path = str(stored_loaded_path).strip() if stored_loaded_path else ""
        self._loaded_data_path: Optional[str] = loaded_path or None

        stored_output_path = self._settings.value("output_data_path", "")
        output_path = str(stored_output_path).strip() if stored_output_path else ""
        self._output_data_path: Optional[str] = output_path or None

        self.dataset: Optional[dict[str, Any]] = None
        self.reps: list[dict] = []
        self.accounts: list[dict] = []
        self.opportunities: list[dict] = []
        self.territories: list[dict] = []
        self.opportunity_history: list[dict] = []

        self.runs: list[dict] = []
        self.issues: list[dict] = []
        self.selected_run_id: Optional[int] = None

        default_run_path = self.get_default_run_json_path()
        stored_run_path = self._settings.value("run_json_path", default_run_path)
        self._run_json_path = str(stored_run_path) if stored_run_path else default_run_path

    @property
    def loaded_data_path(self) -> Optional[str]:
        return self._loaded_data_path

    @loaded_data_path.setter
    def loaded_data_path(self, value: Optional[str]) -> None:
        new_value = str(value or "").strip() or None
        if new_value == getattr(self, "_loaded_data_path", None):
            return
        self._loaded_data_path = new_value
        self._settings.setValue("loaded_data_path", new_value or "")
        self.loadedDataChanged.emit(new_value or "")

    @property
    def output_data_path(self) -> Optional[str]:
        return self._output_data_path

    @output_data_path.setter
    def output_data_path(self, value: Optional[str]) -> None:
        new_value = str(value or "").strip() or None
        if new_value == getattr(self, "_output_data_path", None):
            return
        self._output_data_path = new_value
        self._settings.setValue("output_data_path", new_value or "")
        self.outputPathChanged.emit(new_value or "")

    @property
    def run_json_path(self) -> str:
        return self._run_json_path

    @run_json_path.setter
    def run_json_path(self, value: str) -> None:
        value = str(value or "").strip()
        if not value:
            value = self.get_default_run_json_path()
        if value == getattr(self, "_run_json_path", None):
            return
        self._run_json_path = value
        self._settings.setValue("run_json_path", value)
        self.runJsonPathChanged.emit(value)

    def get_default_run_json_path(self) -> str:
        try:
            import main as main_module

            base_dir = Path(main_module.__file__).resolve().parent
        except Exception:
            base_dir = Path(os.getcwd()).resolve()
        return str(base_dir / "run.json")

    def _json_friendly(self, value: Any) -> Any:
        if isinstance(value, QDateTime):
            return value.toString(Qt.ISODate)
        if isinstance(value, datetime):
            return value.astimezone(timezone.utc).isoformat()
        if isinstance(value, dict):
            return {k: self._json_friendly(v) for k, v in value.items()}
        if isinstance(value, list):
            return [self._json_friendly(v) for v in value]
        return value

    def _parse_qdatetime(self, value: Any) -> Any:
        if not isinstance(value, str):
            return value
        dt = QDateTime.fromString(value, Qt.ISODate)
        return dt if dt.isValid() else value

    def save_run_state_to_disk(self, path: Optional[str] = None) -> None:
        target = str(path or self.run_json_path)
        payload = {
            "schema": "revops-agent-run",
            "runs": self._json_friendly(self.runs),
            "selectedRun": self.selected_run_id,
        }
        with open(target, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)

    def load_run_state_from_disk(self, path: Optional[str] = None) -> bool:
        target = str(path or self.run_json_path)
        if not target or not os.path.exists(target):
            return False

        with open(target, "r", encoding="utf-8") as f:
            payload = json.load(f)

        runs = payload.get("runs")
        selected_run = payload.get("selectedRun")
        self.runs = list(runs) if isinstance(runs, list) else []
        self.issues = []

        try:
            self.selected_run_id = int(selected_run) if selected_run is not None else None
        except Exception:
            self.selected_run_id = None

        for run in self.runs:
            if isinstance(run, dict) and "datetime" in run:
                run["datetime"] = self._parse_qdatetime(run.get("datetime"))

            nested_issues = run.get("issues") if isinstance(run, dict) else None
            if isinstance(nested_issues, list):
                for issue in nested_issues:
                    if isinstance(issue, dict) and "timestamp" in issue:
                        issue["timestamp"] = self._parse_qdatetime(issue.get("timestamp"))
                    if isinstance(issue, dict) and "snoozed_until" in issue:
                        issue["snoozed_until"] = self._parse_qdatetime(issue.get("snoozed_until"))

        # Derive current issues list from selected run.
        selected_run_dict: Optional[dict] = None
        if self.selected_run_id is not None:
            selected_run_dict = next(
                (r for r in self.runs if isinstance(r, dict) and int(r.get("run_id", -1)) == int(self.selected_run_id)),
                None,
            )

        if selected_run_dict is None and self.runs:
            # Fallback to most recent run by run_id.
            try:
                selected_run_dict = max(
                    (r for r in self.runs if isinstance(r, dict) and r.get("run_id") is not None),
                    key=lambda r: int(r.get("run_id")),
                )
            except Exception:
                selected_run_dict = None

        if isinstance(selected_run_dict, dict):
            try:
                self.selected_run_id = int(selected_run_dict.get("run_id"))
            except Exception:
                self.selected_run_id = None

            run_issues = selected_run_dict.get("issues")
            self.issues = list(run_issues) if isinstance(run_issues, list) else []
        else:
            self.issues = []

        return True

    def load_json_data(self, path: str) -> None:
        with open(path, "r", encoding="utf-8") as f:
            payload = json.load(f)

        self.dataset = payload
        self.reps = list(payload.get("reps") or [])
        self.accounts = list(payload.get("accounts") or [])
        self.opportunities = list(payload.get("opportunities") or [])
        self.territories = list(payload.get("territories") or [])
        self.opportunity_history = list(payload.get("opportunity_history") or [])

        account_name_by_id = {int(a.get("id")): str(a.get("name", "")) for a in self.accounts if a.get("id") is not None}
        rep_name_by_id = {int(r.get("id")): str(r.get("name", "")) for r in self.reps if r.get("id") is not None}

        generated_at = payload.get("generated_at")
        try:
            default_created = datetime.fromisoformat(generated_at.replace("Z", "+00:00")) if isinstance(generated_at, str) else datetime.now(tz=timezone.utc)
        except Exception:
            default_created = datetime.now(tz=timezone.utc)

        def _parse_date_or_datetime(value: Any) -> Any:
            if isinstance(value, datetime):
                return value
            if not isinstance(value, str):
                return value
            try:
                # Accept YYYY-MM-DD or full ISO8601; normalize to timezone-aware datetime where possible.
                if len(value) == 10:
                    return datetime.fromisoformat(value).replace(tzinfo=timezone.utc)
                return datetime.fromisoformat(value.replace("Z", "+00:00"))
            except Exception:
                return value
        
        # Add rep names to accounts
        for acct in self.accounts:
            rep_id = acct.get('repId')
            if rep_id is not None and "owner" not in acct:
                acct["owner"] = rep_name_by_id.get(int(rep_id), "")

        # Normalize opportunities for rules (owner/created_date/history)
        for o in self.opportunities:
            rep_id = o.get("repId")
            if rep_id is not None and "owner" not in o:
                o["owner"] = rep_name_by_id.get(int(rep_id), "")

            account_id = o.get("accountId")
            if account_id is not None and "account_name" not in o:
                o["account_name"] = account_name_by_id.get(int(account_id), "")

            if "created_date" in o:
                o["created_date"] = _parse_date_or_datetime(o.get("created_date"))
            else:
                o["created_date"] = default_created

        for h in self.opportunity_history:
            if "change_date" in h:
                h["change_date"] = _parse_date_or_datetime(h.get("change_date"))

        self.datasetChanged.emit()
