from rules.rule_settings import RuleSettings
from rules.severity import Severity
from rules.rule import Rule

def pipeline_per_rep_metric(rep: dict, opportunities: list[dict]) -> int:
    return sum(opp.get("amount", 0) for opp in opportunities if opp.get("owner") == rep.get("name"))

def pipeline_per_rep_condition(metric_value: int) -> Severity:
    low = RuleSettings.get("pipeline_imbalance.low_severity", 500000)
    medium = RuleSettings.get("pipeline_imbalance.medium_severity", 600000)
    high = RuleSettings.get("pipeline_imbalance.high_severity", 800000)
    
    if metric_value >= high:
        return Severity.HIGH
    elif metric_value >= medium:
        return Severity.MEDIUM
    elif metric_value >= low:
        return Severity.LOW
    return Severity.NONE

def pipeline_per_rep_responsible(rep: dict) -> str:
    return "0 - Ops"

def pipeline_per_rep_format_value(metric_value: int) -> str:
    return f"USD {metric_value:,.0f}"

def pipeline_per_rep_explanation(metric_name: str, metric_value: int) -> str:
    low = RuleSettings.get("pipeline_imbalance.low_severity", 500000)
    medium = RuleSettings.get("pipeline_imbalance.medium_severity", 600000)
    high = RuleSettings.get("pipeline_imbalance.high_severity", 800000)
    if metric_value >= high:
        return f"Pipeline imbalance: USD {metric_value:,.0f} which is above the threshold of USD {high:,.0f} for high severity"
    elif metric_value >= medium:
        return f"Pipeline imbalance: USD {metric_value:,.0f} which is above the threshold of USD {medium:,.0f} for medium severity"
    elif metric_value >= low:
        return f"Pipeline imbalance: USD {metric_value:,.0f} which is above the threshold of USD {low:,.0f} for low severity"
    return f"Pipeline imbalance: USD {metric_value:,.0f}"

PipelinePerRepImbalance = Rule(
    rule_type="rep",
    name="Pipeline imbalance",
    category="Pipeline Hygiene",
    metric=pipeline_per_rep_metric,
    condition=pipeline_per_rep_condition,
    responsible=pipeline_per_rep_responsible,
    fields=['amount'],
    metric_name="Pipeline imbalance",
    format_metric_value=pipeline_per_rep_format_value,
    explanation=pipeline_per_rep_explanation,
    resolution="Ops rebalance pipeline among reps and see if there are routing issues in CRM",
)
