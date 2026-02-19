from __future__ import annotations
 
from datetime import datetime
 
import pandas as pd
 
from models import Opportunity, OpportunityHistory
from rules.rule_settings import RuleSettings
from rules.rule import Rule
from rules.severity import Severity
from rules.rule_setting_field import RuleSettingField

# Stale opportunities
RULE_ID = "stale_opportunity"
RULE_SETTINGS_GROUP = "Stale Opportunity Settings"
RULE_SETTINGS_FIELDS = [
    RuleSettingField(
        key="stale_opportunity.low_days",
        label="Stale days (low)",
        default=30,
        minimum=0,
        maximum=365,
    ),
    RuleSettingField(
        key="stale_opportunity.medium_days",
        label="Stale days (medium)",
        default=60,
        minimum=0,
        maximum=365,
    ),
    RuleSettingField(
        key="stale_opportunity.high_days",
        label="Stale days (high)",
        default=90,
        minimum=0,
        maximum=365,
    ),
]

def staleness_metric(opp: Opportunity, history: list[OpportunityHistory]) -> dict:
    df = pd.DataFrame([vars(h) for h in history])
    opp_history = df[(df['opportunity_id'] == opp.id) & (df['field_name'] == 'stage')]
    if opp_history.empty:
        last_known_stage = opp.stage
        last_change_date = opp.created_date
    else:
        most_recent = opp_history.loc[opp_history['change_date'].idxmax()]
        last_known_stage, last_change_date = most_recent['new_value'], most_recent['change_date']
    if last_known_stage != opp.stage:
        return {'days_since_last_change': 0, 'last_change_date': last_change_date}
    days_since_last_change = (datetime.today().date() - last_change_date.date()).days
    return {'days_since_last_change': days_since_last_change, 'last_change_date': last_change_date}

def staleness_condition(days: dict) -> Severity:
    if days['days_since_last_change'] > RuleSettings.get("stale_opportunity.high_days"):
        return Severity.HIGH
    elif days['days_since_last_change'] > RuleSettings.get("stale_opportunity.medium_days"):
        return Severity.MEDIUM
    elif days['days_since_last_change'] > RuleSettings.get("stale_opportunity.low_days"):
        return Severity.LOW
    return Severity.NONE

def staleness_responsible(opp: Opportunity) -> str:
    return opp.owner

def staleness_format_value(value: dict) -> str:
    return f"Last change date: {value['last_change_date'].strftime('%Y-%m-%d')}\nDays since last change: {value['days_since_last_change']} days"

def staleness_explanation(metric_name: str, value: dict) -> str:
    days = value['days_since_last_change']
    selected_threshold = 0
    severity_label = None
    if days > RuleSettings.get("stale_opportunity.high_days"):
        selected_threshold = RuleSettings.get("stale_opportunity.high_days")
        severity_label = Severity.HIGH
    elif days > RuleSettings.get("stale_opportunity.medium_days"):
        selected_threshold = RuleSettings.get("stale_opportunity.medium_days")
        severity_label = Severity.MEDIUM
    elif days > RuleSettings.get("stale_opportunity.low_days"):
        selected_threshold = RuleSettings.get("stale_opportunity.low_days")
        severity_label = Severity.LOW
    return f"Days since last stage change is {days} days old, which is above the {severity_label.value.lower()} threshold of {selected_threshold} days"

StalenessRule = Rule(
    rule_type="opportunity",
    settings_id=RULE_ID,
    name="Stale Opp",
    category="Pipeline Hygiene",
    metric=staleness_metric,
    condition=staleness_condition,
    responsible=staleness_responsible,
    fields=["stage"],
    metric_name='Days since last stage change (or since creation if no stage changes)',
    explanation=staleness_explanation,
    format_metric_value=staleness_format_value,
    resolution="Reach out to the sales rep to confirm the opportunity is still active.",
)