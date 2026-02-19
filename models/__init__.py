from __future__ import annotations

import dataclasses
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional


@dataclass
class Rep:
    id: int
    name: str
    homeState: str
    region: str
    quota: int
    territoryId: int


@dataclass
class Account:
    id: int
    name: str
    annualRevenue: int
    numDevelopers: int
    state: str
    industry: str
    isCustomer: bool
    inPipeline: bool
    repId: int
    territoryId: int
    owner: str = ""


@dataclass
class Opportunity:
    id: int
    name: str
    amount: int
    stage: str
    created_date: Any = None  # str | datetime depending on lifecycle
    closeDate: Optional[str] = None
    repId: int = 0
    accountId: int = 0
    owner: str = ""
    account_name: str = ""


@dataclass
class OpportunityHistory:
    id: int
    opportunity_id: int
    field_name: str
    old_value: Optional[str]
    new_value: Optional[str]
    change_date: Any = None  # str | datetime depending on lifecycle


@dataclass
class Territory:
    id: int
    name: str


@dataclass
class Issue:
    severity: str = ""
    name: str = ""
    account_name: str = ""
    opportunity_name: str = ""
    category: str = ""
    owner: str = ""
    fields: list[str] = field(default_factory=list)
    metric_name: str = ""
    metric_value: Any = None
    formatted_metric_value: str = ""
    explanation: str = ""
    resolution: str = ""
    status: str = "Open"
    timestamp: Any = None
    is_unread: bool = True
    snoozed_until: Any = None


@dataclass
class Run:
    run_id: int = 0
    datetime: Any = None
    issues_count: int = 0
    issues: list[Issue] = field(default_factory=list)


def to_dict(obj: Any) -> Any:
    """Recursively convert dataclass instances to plain dicts for JSON serialization."""
    if dataclasses.is_dataclass(obj) and not isinstance(obj, type):
        return {k: to_dict(v) for k, v in dataclasses.asdict(obj).items()}
    if isinstance(obj, list):
        return [to_dict(item) for item in obj]
    if isinstance(obj, dict):
        return {k: to_dict(v) for k, v in obj.items()}
    return obj
