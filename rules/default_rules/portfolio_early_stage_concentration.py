from rules.severity import Severity
from rules.rule import Rule


def portfolio_early_stage_concentration_metric(opportunities: list[dict], *args, **kwargs) -> dict:
    total_opps = len(opportunities)
    stage_0_and_1_opps = sum(1 for opp in opportunities if opp.get("stage") in ("0 - Discovery", "1 - Qualification"))
    return {"total_opps": total_opps, "stage_0_and_1_opps": stage_0_and_1_opps}

def portfolio_early_stage_concentration_condition(metric_value: dict) -> Severity:
    total_opps = metric_value.get("total_opps", 0)
    stage_0_and_1_opps = metric_value.get("stage_0_and_1_opps", 0)
    if total_opps == 0:
        return Severity.NONE
    if stage_0_and_1_opps / total_opps >= 0.5:
        return Severity.HIGH
    return Severity.MEDIUM

def portfolio_early_stage_concentration_responsible(opportunities: list[dict]) -> str:
    return '0 - Ops'

def portfolio_early_stage_concentration_formatted_metric_value(metric_value: dict) -> str:
    total_opps = metric_value.get("total_opps", 0)
    stage_0_and_1_opps = metric_value.get("stage_0_and_1_opps", 0)
    ratio = stage_0_and_1_opps / total_opps if total_opps > 0 else 0
    return f"Total Opps: {total_opps}\nStage 0 & 1 Opps: {stage_0_and_1_opps}\nRatio: {ratio:.2%}"

def portfolio_early_stage_concentration_explanation(metric_name: str, metric_value: dict) -> str:
    total_opps = metric_value.get("total_opps", 0)
    stage_0_and_1_opps = metric_value.get("stage_0_and_1_opps", 0)
    severity = portfolio_early_stage_concentration_condition(metric_value)
    return f"Early stage concentration detected with {stage_0_and_1_opps} opportunities in stages 0 and 1 out of {total_opps} total opportunities ({stage_0_and_1_opps/total_opps:.2%}), which makes it {severity.value.lower()} severity"

PortfolioEarlyStageConcentrationRule = Rule(
    rule_type="portfolio",
    name="Early stage concentration",
    category="Pipeline Hygiene",
    metric=portfolio_early_stage_concentration_metric,
    condition=portfolio_early_stage_concentration_condition,
    responsible=portfolio_early_stage_concentration_responsible,
    fields=["stage"],
    metric_name="Early stage concentration",
    format_metric_value=portfolio_early_stage_concentration_formatted_metric_value,
    explanation=portfolio_early_stage_concentration_explanation,
    resolution="Ops to analyse what is causing bottlenecks in early stages",
)
