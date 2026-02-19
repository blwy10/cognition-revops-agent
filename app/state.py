from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any, Optional

from PySide6.QtCore import QDateTime, QObject, Signal


class AppState(QObject):
    loadedDataChanged = Signal(str)
    outputPathChanged = Signal(str)
    datasetChanged = Signal()
    runsChanged = Signal()
    issuesChanged = Signal()
    requestTabChange = Signal(str)

    def __init__(self, parent: Optional[QObject] = None) -> None:
        super().__init__(parent)
        self.loaded_data_path: Optional[str] = None
        self.output_data_path: Optional[str] = None

        self.dataset: Optional[dict[str, Any]] = None
        self.reps: list[dict] = []
        self.accounts: list[dict] = []
        self.opportunities: list[dict] = []
        self.territories: list[dict] = []
        self.opportunity_history: list[dict] = []

        self.runs: list[dict] = []
        self.issues: list[dict] = []

    def load_json_data(self, path: str) -> None:
        with open(path, "r", encoding="utf-8") as f:
            payload = json.load(f)

        self.dataset = payload
        self.reps = list(payload.get("reps") or [])
        self.accounts = list(payload.get("accounts") or [])
        self.opportunities = list(payload.get("opportunities") or [])
        self.territories = list(payload.get("territories") or [])
        self.opportunity_history = list(payload.get("opportunity_history") or [])

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

        # Normalize opportunities for rules (owner/created_date/history)
        for o in self.opportunities:
            rep_id = o.get("repId")
            if rep_id is not None and "owner" not in o:
                o["owner"] = rep_name_by_id.get(int(rep_id), "")

            if "created_date" in o:
                o["created_date"] = _parse_date_or_datetime(o.get("created_date"))
            else:
                o["created_date"] = default_created

        for h in self.opportunity_history:
            if "change_date" in h:
                h["change_date"] = _parse_date_or_datetime(h.get("change_date"))

        self.datasetChanged.emit()

    def seed_demo_data(self) -> None:
        now = QDateTime.currentDateTime()
        self.runs = [
            {"run_id": 1, "datetime": now.addSecs(-3600 * 5), "issues_count": 3},
            {"run_id": 2, "datetime": now.addSecs(-3600 * 2), "issues_count": 5},
        ]

        self.issues = [
            {
                "severity": "High",
                "category": "Pipeline",
                "owner": "Sales Ops",
                "status": "Open",
                "timestamp": now.addSecs(-1800),
                "is_unread": True,
            },
            {
                "severity": "Medium",
                "category": "Attribution",
                "owner": "Marketing Ops",
                "status": "Investigating",
                "timestamp": now.addSecs(-1200),
                "is_unread": True,
            },
            {
                "severity": "Low",
                "category": "CRM Hygiene",
                "owner": "RevOps",
                "status": "Backlog",
                "timestamp": now.addSecs(-600),
                "is_unread": False,
            },
        ]

        self.runsChanged.emit()
        self.issuesChanged.emit()
