from rules.severity import Severity
from rules.rule_settings import RuleSettings
from rules.rule import Rule

def acct_per_rep_metric(rep: dict, opportunities: list[dict]) -> int:
    owned_by_rep = [opp for opp in opportunities if opp.get("owner") == rep.get("name")]
    return len(owned_by_rep)

def acct_per_rep_condition(metric_value: int) -> Severity:
    count = metric_value
    low = RuleSettings.get("acct_per_rep.low_severity", 6)
    medium = RuleSettings.get("acct_per_rep.medium_severity", 10)
    high = RuleSettings.get("acct_per_rep.high_severity", 15)
    
    if count >= high:
        return Severity.HIGH
    elif count >= medium:
        return Severity.MEDIUM
    elif count >= low:
        return Severity.LOW
    return Severity.NONE

def acct_per_rep_responsible(rep: dict) -> str:
    return "0 - Ops"

def acct_per_rep_explanation(metric_name: str, metric_value: int) -> str:
    low = RuleSettings.get("acct_per_rep.low_severity", 6)
    medium = RuleSettings.get("acct_per_rep.medium_severity", 10)
    high = RuleSettings.get("acct_per_rep.high_severity", 15)
    if metric_value >= high:
        return f"Accounts owned: {metric_value} which is above the threshold of {high} for high severity"
    elif metric_value >= medium:
        return f"Accounts owned: {metric_value} which is above the threshold of {medium} for medium severity"
    elif metric_value >= low:
        return f"Accounts owned: {metric_value} which is above the threshold of {low} for low severity"
    return f"Accounts owned: {metric_value}"

AcctPerRepAboveThreshold = Rule(
    rule_type="rep",
    name="Acct rep concentration",
    category="Pipeline Hygiene",
    metric=acct_per_rep_metric,
    condition=acct_per_rep_condition,
    responsible=acct_per_rep_responsible,
    fields=['repId'],
    metric_name="Accts per rep",
    format_metric_value=lambda x: f"{x}",
    explanation=acct_per_rep_explanation,
    resolution="Ops rebalance accounts among reps and see if there are routing issues in CRM",
)
