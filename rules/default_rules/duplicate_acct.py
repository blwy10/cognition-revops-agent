from collections import Counter
from rules.severity import Severity
from rules.rule import Rule

def duplicate_acct_metric(accounts: list[dict], *args, **kwargs) -> int:
    c = Counter(acc.get("name") for acc in accounts)
    counter = 0
    for count in c.values():
        counter += count - 1
    return counter

def duplicate_acct_condition(metric_value: int) -> Severity:
    if metric_value > 0:
        return Severity.HIGH
    return Severity.NONE

def duplicate_acct_responsible(accounts: list[dict]) -> str:
    return '0 - Ops'

def duplicate_acct_explanation(metric_name: str, metric_value: int) -> str:
    return f"Duplicate accounts detected with {metric_value} duplicates"

DuplicateAcctRule = Rule(
    rule_type="portfolio_acct",
    name="Duplicate accounts",
    category="Data Integrity",
    metric=duplicate_acct_metric,
    condition=duplicate_acct_condition,
    responsible=duplicate_acct_responsible,
    fields=["name"],
    metric_name="Duplicate accounts",
    explanation=duplicate_acct_explanation,
    resolution="Ops to clean up CRM data and rebalance accounts",
)
