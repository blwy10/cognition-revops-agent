from rules.severity import Severity
from rules.rule_settings import RuleSettings
from rules.rule import Rule
from rules.rule_setting_field import RuleSettingField

RULE_SETTINGS_GROUP = "Rep Early Stage Concentration Settings"
RULE_SETTINGS_FIELDS = [
    RuleSettingField(
        key="rep_early_stage_concentration.low_pct",
        label="Low pct",
        default=35,
        minimum=0,
        maximum=100,
    ),
    RuleSettingField(
        key="rep_early_stage_concentration.medium_pct",
        label="Medium pct",
        default=45,
        minimum=0,
        maximum=100,
    ),
    RuleSettingField(
        key="rep_early_stage_concentration.high_pct",
        label="High pct",
        default=60,
        minimum=0,
        maximum=100,
    ),
    RuleSettingField(
        key="rep_early_stage_concentration.min_opps",
        label="Minimum opportunities",
        default=10,
        minimum=0,
        maximum=10000,
    ),
]


def rep_early_stage_concentration_metric(rep: dict, opportunities: list[dict]) -> dict:
    owned_by_rep = [opp for opp in opportunities if opp.get("owner") == rep.get("name")]
    total_opps = len(owned_by_rep)
    stage_0_and_1_opps = sum(1 for opp in owned_by_rep if opp.get("stage") in ("0 - Discovery", "1 - Qualification"))
    return {"total_opps": total_opps, "stage_0_and_1_opps": stage_0_and_1_opps}

def rep_early_stage_concentration_condition(metric_value: dict) -> Severity:
    total_opps = metric_value.get("total_opps", 0)
    stage_0_and_1_opps = metric_value.get("stage_0_and_1_opps", 0)
    ratio = stage_0_and_1_opps / total_opps if total_opps else 0

    min_opps = RuleSettings.get("rep_early_stage_concentration.min_opps", 10)
    try:
        min_opps_int = int(min_opps)
    except (TypeError, ValueError):
        min_opps_int = 10

    if total_opps < min_opps_int:
        return Severity.NONE

    low_pct = RuleSettings.get("rep_early_stage_concentration.low_pct", 35)
    medium_pct = RuleSettings.get("rep_early_stage_concentration.medium_pct", 45)
    high_pct = RuleSettings.get("rep_early_stage_concentration.high_pct", 60)

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

def rep_early_stage_concentration_responsible(rep: dict) -> str:
    return rep.get("name")

def rep_early_stage_concentration_formatted_metric_value(metric_value: dict) -> str:
    total_opps = metric_value.get("total_opps", 0)
    stage_0_and_1_opps = metric_value.get("stage_0_and_1_opps", 0)
    ratio = stage_0_and_1_opps / total_opps if total_opps > 0 else 0
    return f"Total Opps: {total_opps}\nStage 0 & 1 Opps: {stage_0_and_1_opps}\nRatio: {ratio:.2%}"

def rep_early_stage_concentration_explanation(metric_name: str, metric_value: dict) -> str:
    total_opps = metric_value.get("total_opps", 0)
    stage_0_and_1_opps = metric_value.get("stage_0_and_1_opps", 0)
    ratio = stage_0_and_1_opps / total_opps if total_opps > 0 else 0
    return f"Total Opps: {total_opps}\nStage 0 & 1 Opps: {stage_0_and_1_opps}\nRatio: {ratio:.2%}"

RepEarlyStageConcentrationRule = Rule(
    rule_type="rep",
    name="Rep concentration",
    category="Pipeline Hygiene",
    metric=rep_early_stage_concentration_metric,
    condition=rep_early_stage_concentration_condition,
    responsible=rep_early_stage_concentration_responsible,
    fields=["stage"],
    metric_name="Rep concentration",
    format_metric_value=rep_early_stage_concentration_formatted_metric_value,
    explanation=rep_early_stage_concentration_explanation,
    resolution="Ops work with rep to identify bottlenecks in moving forward opportunities",
)