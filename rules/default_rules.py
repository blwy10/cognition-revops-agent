from __future__ import annotations
 
from datetime import datetime
 
import pandas as pd
 
from rules.rule_settings import RuleSettings
from .rule import Rule
from .severity import Severity

# Stale opportunities
def staleness_metric(opp: dict, history: list[dict]) -> int:
    df = pd.DataFrame(history)
    opp_history = df[(df['opportunity_id'] == opp['id']) & (df['field_name'] == 'stage')]
    if opp_history.empty:
        last_known_stage = opp['stage']
        last_change_date = opp['created_date']
    else:
        most_recent = opp_history.loc[opp_history['change_date'].idxmax()]
        last_known_stage, last_change_date = most_recent['new_value'], most_recent['change_date']
    if last_known_stage != opp['stage']:
        return 0
    days_since_last_change = (datetime.today().date() - last_change_date.date()).days
    return days_since_last_change

def staleness_condition(days) -> Severity:
    if days > RuleSettings.get("stale_opportunity.high_days"):
        return Severity.HIGH
    elif days > RuleSettings.get("stale_opportunity.medium_days"):
        return Severity.MEDIUM
    elif days > RuleSettings.get("stale_opportunity.low_days"):
        return Severity.LOW
    return Severity.NONE

def staleness_responsible(opp: dict) -> str:
    return opp['owner']

def staleness_explanation(metric_name: str, value: float) -> str:
    selected_threshold = 0
    severity_label = None
    if value > RuleSettings.get("stale_opportunity.high_days"):
        selected_threshold = RuleSettings.get("stale_opportunity.high_days")
        severity_label = Severity.HIGH
    elif value > RuleSettings.get("stale_opportunity.medium_days"):
        selected_threshold = RuleSettings.get("stale_opportunity.medium_days")
        severity_label = Severity.MEDIUM
    elif value > RuleSettings.get("stale_opportunity.low_days"):
        selected_threshold = RuleSettings.get("stale_opportunity.low_days")
        severity_label = Severity.LOW
    return f"Days since last stage change is {value} days old, which is above the {severity_label.value.lower()} threshold of {selected_threshold} days"

StalenessRule = Rule(
    name="Stale Opportunity",
    category="Pipeline Hygiene",
    metric=staleness_metric,
    condition=staleness_condition,
    responsible=staleness_responsible,
    fields=["stage"],
    metric_name='Days since last stage change (or since creation if no stage changes)',
    explanation=staleness_explanation,
    resolution="Reach out to the sales rep to confirm the opportunity is still active.",
)
