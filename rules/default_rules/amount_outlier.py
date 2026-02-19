from __future__ import annotations

from rules.rule import Rule
from rules.rule_settings import RuleSettings
from rules.severity import Severity
from rules.rule_setting_field import RuleSettingField

RULE_SETTINGS_GROUP = "Amount Outlier Settings"
RULE_SETTINGS_FIELDS = [
    RuleSettingField(
        key="amount_outlier.high_low_threshold",
        label="High outlier threshold (LOW severity)",
        default=300000,
        minimum=0,
        maximum=100000000,
    ),
    RuleSettingField(
        key="amount_outlier.high_medium_threshold",
        label="High outlier threshold (MEDIUM severity)",
        default=600000,
        minimum=0,
        maximum=100000000,
    ),
    RuleSettingField(
        key="amount_outlier.high_high_threshold",
        label="High outlier threshold (HIGH severity)",
        default=1000000,
        minimum=0,
        maximum=100000000,
    ),
    RuleSettingField(
        key="amount_outlier.low_low_threshold",
        label="Low-end threshold (LOW severity)",
        default=60000,
        minimum=0,
        maximum=100000000,
    ),
    RuleSettingField(
        key="amount_outlier.low_medium_threshold",
        label="Low-end threshold (MEDIUM severity)",
        default=30000,
        minimum=0,
        maximum=100000000,
    ),
    RuleSettingField(
        key="amount_outlier.low_high_threshold",
        label="Low-end threshold (HIGH severity)",
        default=20000,
        minimum=0,
        maximum=100000000,
    ),
]


def amount_outlier_metric(opp: dict, *args, **kwargs) -> dict:
    return {"amount": opp.get("amount"), "stage": opp.get("stage")}


def _is_closed_stage(stage: object) -> bool:
    if not isinstance(stage, str):
        return False
    s = stage.strip().lower()
    return "closed" in s


def _safe_int(value: object, default: int) -> int:
    try:
        return int(value)  # type: ignore[arg-type]
    except Exception:
        return default


def _safe_float(value: object) -> float | None:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    try:
        return float(str(value).strip())
    except Exception:
        return None


def amount_outlier_condition(metric_value: dict) -> Severity:
    if not isinstance(metric_value, dict):
        return Severity.NONE

    stage = metric_value.get("stage")
    if _is_closed_stage(stage):
        return Severity.NONE

    amount = _safe_float(metric_value.get("amount"))
    if amount is None:
        return Severity.NONE

    high_low = _safe_int(RuleSettings.get("amount_outlier.high_low_threshold", 300000), 300000)
    high_med = _safe_int(RuleSettings.get("amount_outlier.high_medium_threshold", 600000), 600000)
    high_high = _safe_int(RuleSettings.get("amount_outlier.high_high_threshold", 1000000), 1000000)

    low_low = _safe_int(RuleSettings.get("amount_outlier.low_low_threshold", 60000), 60000)
    low_med = _safe_int(RuleSettings.get("amount_outlier.low_medium_threshold", 30000), 30000)
    low_high = _safe_int(RuleSettings.get("amount_outlier.low_high_threshold", 20000), 20000)

    # Enforce monotonicity.
    if high_med < high_low:
        high_med = high_low
    if high_high < high_med:
        high_high = high_med

    if low_med > low_low:
        low_med = low_low
    if low_high > low_med:
        low_high = low_med

    if amount > float(high_high):
        return Severity.HIGH
    if amount > float(high_med):
        return Severity.MEDIUM
    if amount > float(high_low):
        return Severity.LOW

    if amount < float(low_high):
        return Severity.HIGH
    if amount < float(low_med):
        return Severity.MEDIUM
    if amount < float(low_low):
        return Severity.LOW

    return Severity.NONE


def amount_outlier_responsible(opp: dict) -> str:
    return opp.get("owner", "")


def amount_outlier_format_metric_value(metric_value: dict) -> str:
    if not isinstance(metric_value, dict):
        return ""
    amount = metric_value.get("amount")
    stage = metric_value.get("stage")
    return f"Stage: {'' if stage is None else stage}\nAmount: {'' if amount is None else amount}"


def amount_outlier_explanation(metric_name: str, metric_value: dict) -> str:
    if not isinstance(metric_value, dict):
        return ""

    amount = _safe_float(metric_value.get("amount"))
    if amount is None:
        return ""

    high_low = _safe_int(RuleSettings.get("amount_outlier.high_low_threshold", 300000), 300000)
    high_med = _safe_int(RuleSettings.get("amount_outlier.high_medium_threshold", 600000), 600000)
    high_high = _safe_int(RuleSettings.get("amount_outlier.high_high_threshold", 1000000), 1000000)

    low_low = _safe_int(RuleSettings.get("amount_outlier.low_low_threshold", 60000), 60000)
    low_med = _safe_int(RuleSettings.get("amount_outlier.low_medium_threshold", 30000), 30000)
    low_high = _safe_int(RuleSettings.get("amount_outlier.low_high_threshold", 20000), 20000)

    if high_med < high_low:
        high_med = high_low
    if high_high < high_med:
        high_high = high_med

    if low_med > low_low:
        low_med = low_low
    if low_high > low_med:
        low_high = low_med

    if amount > float(high_high):
        return f"Amount ({amount:,.0f}) is unusually large, above the high threshold ({high_high:,.0f})"
    if amount > float(high_med):
        return f"Amount ({amount:,.0f}) is unusually large, above the medium threshold ({high_med:,.0f})"
    if amount > float(high_low):
        return f"Amount ({amount:,.0f}) is unusually large, above the low threshold ({high_low:,.0f})"

    if amount < float(low_high):
        return f"Amount ({amount:,.0f}) is unusually small, below the high threshold ({low_high:,.0f})"
    if amount < float(low_med):
        return f"Amount ({amount:,.0f}) is unusually small, below the medium threshold ({low_med:,.0f})"
    if amount < float(low_low):
        return f"Amount ({amount:,.0f}) is unusually small, below the low threshold ({low_low:,.0f})"

    return ""


AmountOutlierRule = Rule(
    rule_type="opportunity",
    name="Amount outlier",
    category="Data Integrity",
    metric=amount_outlier_metric,
    condition=amount_outlier_condition,
    responsible=amount_outlier_responsible,
    fields=["amount"],
    metric_name="Amount",
    format_metric_value=amount_outlier_format_metric_value,
    explanation=amount_outlier_explanation,
    resolution="Validate the opportunity amount; correct potential data entry issues or confirm this deal size is accurate.",
)
