from rules.rule import Rule, Severity

def no_opps_metric(acct: dict, opportunities: list[dict]) -> int:
    return len([opp for opp in opportunities if opp.get("accountId") == acct.get("id")])

def no_opps_condition(metric_value: int) -> Severity:
    return Severity.HIGH if metric_value == 0 else Severity.NONE

def no_opps_responsible(acct: dict) -> str:
    return acct.get('owner')

def no_opps_explanation(metric_name: str, metric_value: int) -> str:
    return "No opportunities found for this account" if metric_value == 0 else ""

NoOpps = Rule(
    rule_type="account",
    name="No opps",
    category="Customer Expansion",
    metric=no_opps_metric,
    condition=no_opps_condition,
    responsible=no_opps_responsible,
    fields=['accountId'],
    metric_name="No opps",
    format_metric_value=lambda x: f"{x}",
    explanation=no_opps_explanation,
    resolution="Ops should ask rep why there are no opportunities for this account",
)
