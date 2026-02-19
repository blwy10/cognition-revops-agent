from __future__ import annotations

import json
import os
from pathlib import Path
from datetime import datetime, timezone
from typing import Any, Optional

from PySide6.QtCore import QDateTime, QObject, Qt, Signal, QSettings

from models import (
    Account,
    Issue,
    Opportunity,
    OpportunityHistory,
    Rep,
    Run,
    Territory,
    to_dict,
)


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
        self.reps: list[Rep] = []
        self.accounts: list[Account] = []
        self.opportunities: list[Opportunity] = []
        self.territories: list[Territory] = []
        self.opportunity_history: list[OpportunityHistory] = []

        self.runs: list[Run] = []
        self.issues: list[Issue] = []
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
            "runs": self._json_friendly(to_dict(self.runs)),
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

        runs_raw = payload.get("runs")
        selected_run = payload.get("selectedRun")
        self.runs = []
        self.issues = []

        if isinstance(runs_raw, list):
            for rd in runs_raw:
                if not isinstance(rd, dict):
                    continue
                if "datetime" in rd:
                    rd["datetime"] = self._parse_qdatetime(rd["datetime"])
                nested_issues_raw = rd.get("issues")
                issues_list: list[Issue] = []
                if isinstance(nested_issues_raw, list):
                    for isd in nested_issues_raw:
                        if not isinstance(isd, dict):
                            continue
                        if "timestamp" in isd:
                            isd["timestamp"] = self._parse_qdatetime(isd["timestamp"])
                        if "snoozed_until" in isd:
                            isd["snoozed_until"] = self._parse_qdatetime(isd["snoozed_until"])
                        issues_list.append(Issue(
                            severity=isd.get("severity", ""),
                            name=isd.get("name", ""),
                            account_name=isd.get("account_name", ""),
                            opportunity_name=isd.get("opportunity_name", ""),
                            category=isd.get("category", ""),
                            owner=isd.get("owner", ""),
                            fields=isd.get("fields", []),
                            metric_name=isd.get("metric_name", ""),
                            metric_value=isd.get("metric_value"),
                            formatted_metric_value=str(isd.get("formatted_metric_value", "")),
                            explanation=isd.get("explanation", ""),
                            resolution=isd.get("resolution", ""),
                            status=isd.get("status", "Open"),
                            timestamp=isd.get("timestamp"),
                            is_unread=isd.get("is_unread", True),
                            snoozed_until=isd.get("snoozed_until"),
                        ))
                self.runs.append(Run(
                    run_id=int(rd.get("run_id", 0)),
                    datetime=rd.get("datetime"),
                    issues_count=int(rd.get("issues_count", 0)),
                    issues=issues_list,
                ))

        try:
            self.selected_run_id = int(selected_run) if selected_run is not None else None
        except Exception:
            self.selected_run_id = None

        # Derive current issues list from selected run.
        selected_run_obj: Optional[Run] = None
        if self.selected_run_id is not None:
            selected_run_obj = next(
                (r for r in self.runs if r.run_id == self.selected_run_id),
                None,
            )

        if selected_run_obj is None and self.runs:
            # Fallback to most recent run by run_id.
            try:
                selected_run_obj = max(self.runs, key=lambda r: r.run_id)
            except Exception:
                selected_run_obj = None

        if selected_run_obj is not None:
            self.selected_run_id = selected_run_obj.run_id
            self.issues = list(selected_run_obj.issues)
        else:
            self.issues = []

        return True

    def load_json_data(self, path: str) -> None:
        with open(path, "r", encoding="utf-8") as f:
            payload = json.load(f)

        self.dataset = payload

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

        # Build reps
        self.reps = [
            Rep(
                id=int(r["id"]),
                name=str(r.get("name", "")),
                homeState=str(r.get("homeState", "")),
                region=str(r.get("region", "")),
                quota=int(r.get("quota", 0)),
                territoryId=int(r.get("territoryId", 0)),
            )
            for r in (payload.get("reps") or [])
        ]

        # Build territories
        self.territories = [
            Territory(id=int(t["id"]), name=str(t.get("name", "")))
            for t in (payload.get("territories") or [])
        ]

        rep_name_by_id = {r.id: r.name for r in self.reps}
        account_name_by_id: dict[int, str] = {}

        # Build accounts
        self.accounts = []
        for ad in (payload.get("accounts") or []):
            acct = Account(
                id=int(ad["id"]),
                name=str(ad.get("name", "")),
                annualRevenue=int(ad.get("annualRevenue", 0)),
                numDevelopers=int(ad.get("numDevelopers", 0)),
                state=str(ad.get("state", "")),
                industry=str(ad.get("industry", "")),
                isCustomer=bool(ad.get("isCustomer", False)),
                inPipeline=bool(ad.get("inPipeline", False)),
                repId=int(ad.get("repId", 0)),
                territoryId=int(ad.get("territoryId", 0)),
                owner=rep_name_by_id.get(int(ad.get("repId", 0)), ""),
            )
            self.accounts.append(acct)
            account_name_by_id[acct.id] = acct.name

        # Build opportunities
        self.opportunities = []
        for od in (payload.get("opportunities") or []):
            created_raw = od.get("created_date")
            created = _parse_date_or_datetime(created_raw) if created_raw is not None else default_created
            opp = Opportunity(
                id=int(od["id"]),
                name=str(od.get("name", "")),
                amount=int(od.get("amount", 0)),
                stage=str(od.get("stage", "")),
                created_date=created,
                closeDate=od.get("closeDate"),
                repId=int(od.get("repId", 0)),
                accountId=int(od.get("accountId", 0)),
                owner=rep_name_by_id.get(int(od.get("repId", 0)), ""),
                account_name=account_name_by_id.get(int(od.get("accountId", 0)), ""),
            )
            self.opportunities.append(opp)

        # Build opportunity history
        self.opportunity_history = []
        for hd in (payload.get("opportunity_history") or []):
            h = OpportunityHistory(
                id=int(hd["id"]),
                opportunity_id=int(hd["opportunity_id"]),
                field_name=str(hd.get("field_name", "")),
                old_value=hd.get("old_value"),
                new_value=hd.get("new_value"),
                change_date=_parse_date_or_datetime(hd.get("change_date")),
            )
            self.opportunity_history.append(h)

        self.datasetChanged.emit()
