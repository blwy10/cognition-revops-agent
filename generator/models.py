from __future__ import annotations

from typing import Optional
from typing import TypedDict


class Rep(TypedDict):
    id: int
    name: str
    homeState: str
    region: str
    quota: int
    territoryId: int


class Account(TypedDict):
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


class Opportunity(TypedDict):
    id: int
    name: str
    amount: int
    stage: str
    created_date: str
    closeDate: Optional[str]
    repId: int
    accountId: int


class OpportunityHistory(TypedDict):
    id: int
    opportunity_id: int
    field_name: str
    old_value: Optional[str]
    new_value: Optional[str]
    change_date: str


class Territory(TypedDict):
    id: int
    name: str
