from rules.rule_settings import RuleSettings
from rules.rule import Rule
from rules.severity import Severity
from rules.rule_setting_field import RuleSettingField

# Missing close dates
RULE_SETTINGS_GROUP = "Missing Close Date Settings"
RULE_SETTINGS_FIELDS = [
    RuleSettingField(
        key="missing_close_date.low_max_stage",
        label="Highest stage for LOW severity",
        default=1,
        minimum=0,
        maximum=6,
    ),
    RuleSettingField(
        key="missing_close_date.medium_max_stage",
        label="Highest stage for MEDIUM severity",
        default=2,
        minimum=0,
        maximum=6,
    ),
]

def missing_close_date_metric(opp: dict, *args, **kwargs) -> dict:
    return {"closeDate": opp.get("closeDate"), "stage": opp.get("stage")}


def _stage_number(stage: object) -> int | None:
    if not isinstance(stage, str):
        return None
    try:
        return int(stage.split("-", 1)[0].strip())
    except Exception:
        return None


def missing_close_date_condition(metric_value: dict) -> Severity:
    close_date = metric_value.get("closeDate") if isinstance(metric_value, dict) else None
    if close_date is not None:
        return Severity.NONE

    stage = metric_value.get("stage") if isinstance(metric_value, dict) else None
    stage_num = _stage_number(stage)

    low_max_stage = RuleSettings.get("missing_close_date.low_max_stage", 1)
    medium_max_stage = RuleSettings.get("missing_close_date.medium_max_stage", 2)
    try:
        low_max_stage = int(low_max_stage)
    except Exception:
        low_max_stage = 1
    try:
        medium_max_stage = int(medium_max_stage)
    except Exception:
        medium_max_stage = 2

    if medium_max_stage < low_max_stage:
        medium_max_stage = low_max_stage

    if stage_num is not None and stage_num <= low_max_stage:
        return Severity.LOW
    if stage_num is not None and stage_num <= medium_max_stage:
        return Severity.MEDIUM
    return Severity.HIGH


def missing_close_date_responsible(opp: dict) -> str:
    return opp["owner"]

def missing_close_date_format_metric_value(metric_value: dict) -> str:
    close_date = metric_value.get("closeDate") if isinstance(metric_value, dict) else None
    stage = metric_value.get("stage") if isinstance(metric_value, dict) else None
    stage_label = "" if stage is None else str(stage)
    close_date_label = "" if close_date is None else str(close_date)
    return f"Stage: {stage_label}\nClose Date: {close_date_label}"


def missing_close_date_explanation(metric_name: str, metric_value: dict) -> str:
    stage = metric_value.get("stage") if isinstance(metric_value, dict) else None
    stage_label = "" if stage is None else str(stage)
    severity = missing_close_date_condition(metric_value)
    return f"Close date is missing at stage \"{stage_label}\" which makes it {severity.value.lower()} severity"


MissingCloseDateRule = Rule(
    rule_type="opportunity",
    name="Missing close date",
    category="Pipeline Hygiene",
    metric=missing_close_date_metric,
    condition=missing_close_date_condition,
    responsible=missing_close_date_responsible,
    fields=["closeDate"],
    metric_name="Close date",
    format_metric_value=missing_close_date_format_metric_value,
    explanation=missing_close_date_explanation,
    resolution="Reach out to sales rep to populate missing close dates",
)
