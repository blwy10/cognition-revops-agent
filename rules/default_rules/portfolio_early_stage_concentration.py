from rules.severity import Severity
from rules.rule import Rule
from rules.rule_settings import RuleSettings
from rules.rule_setting_field import RuleSettingField

RULE_ID = "portfolio_early_stage_concentration"
RULE_SETTINGS_GROUP = "Portfolio Early Stage Concentration Settings"
RULE_SETTINGS_FIELDS = [
    RuleSettingField(
        key="portfolio_early_stage_concentration.low_pct",
        label="Low pct",
        default=35,
        minimum=0,
        maximum=100,
    ),
    RuleSettingField(
        key="portfolio_early_stage_concentration.medium_pct",
        label="Medium pct",
        default=45,
        minimum=0,
        maximum=100,
    ),
    RuleSettingField(
        key="portfolio_early_stage_concentration.high_pct",
        label="High pct",
        default=60,
        minimum=0,
        maximum=100,
    ),
]


def portfolio_early_stage_concentration_metric(opportunities: list[dict], *args, **kwargs) -> dict:
    total_opps = len(opportunities)
    stage_0_and_1_opps = sum(1 for opp in opportunities if opp.get("stage") in ("0 - Discovery", "1 - Qualification"))
    return {"total_opps": total_opps, "stage_0_and_1_opps": stage_0_and_1_opps}

def portfolio_early_stage_concentration_condition(metric_value: dict) -> Severity:
    total_opps = metric_value.get("total_opps", 0)
    stage_0_and_1_opps = metric_value.get("stage_0_and_1_opps", 0)
    ratio = stage_0_and_1_opps / total_opps if total_opps else 0

    low_pct = RuleSettings.get("portfolio_early_stage_concentration.low_pct", 35)
    medium_pct = RuleSettings.get("portfolio_early_stage_concentration.medium_pct", 45)
    high_pct = RuleSettings.get("portfolio_early_stage_concentration.high_pct", 60)

    def _to_ratio_threshold(value: object) -> float:
        try:
            v = float(value)
        except (TypeError, ValueError):
            return 0.0
        if 0.0 <= v <= 1.0:
            return v
        return v / 100.0

    low_threshold = _to_ratio_threshold(low_pct)
    medium_threshold = _to_ratio_threshold(medium_pct)
    high_threshold = _to_ratio_threshold(high_pct)

    if ratio >= high_threshold:
        return Severity.HIGH
    elif ratio >= medium_threshold:
        return Severity.MEDIUM
    elif ratio >= low_threshold:
        return Severity.LOW
    return Severity.NONE

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
    rule_type="portfolio_opp",
    settings_id=RULE_ID,
    name="Portfolio concentration",
    category="Pipeline Hygiene",
    metric=portfolio_early_stage_concentration_metric,
    condition=portfolio_early_stage_concentration_condition,
    responsible=portfolio_early_stage_concentration_responsible,
    fields=["stage"],
    metric_name="Portfolio concentration",
    format_metric_value=portfolio_early_stage_concentration_formatted_metric_value,
    explanation=portfolio_early_stage_concentration_explanation,
    resolution="Ops to analyse what is causing bottlenecks in early stages",
)
