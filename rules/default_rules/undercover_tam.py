from rules.rule_settings import RuleSettings
from rules.severity import Severity
from rules.rule import Rule
from rules.rule_setting_field import RuleSettingField

RULE_SETTINGS_GROUP = "TAM Settings"
RULE_SETTINGS_FIELDS = [
    RuleSettingField(
        key="tam.revenue_per_developer",
        label="Revenue per developer",
        default=1000,
        minimum=0,
        maximum=2000,
    ),
    RuleSettingField(
        key="tam.coverage_percentage",
        label="Coverage percentage",
        default=50,
        minimum=0,
        maximum=100,
    ),
    RuleSettingField(
        key="tam.coverage_low_severity_pct",
        label="TAM coverage threshold (LOW severity)",
        default=60,
        minimum=0,
        maximum=100,
    ),
    RuleSettingField(
        key="tam.coverage_medium_severity_pct",
        label="TAM coverage threshold (MEDIUM severity)",
        default=50,
        minimum=0,
        maximum=100,
    ),
    RuleSettingField(
        key="tam.coverage_high_severity_pct",
        label="TAM coverage threshold (HIGH severity)",
        default=40,
        minimum=0,
        maximum=100,
    ),
]


def undercover_tam_metric(acct: dict, opportunities: list[dict]) -> dict:
    total_opps = len([opp for opp in opportunities if opp.get("account_id") == acct.get("id")])
    if total_opps == 0:
        return {'pipeline': 0, 'tam': 0, 'coverage': 100}
    total_opp_amt = sum(opp['amount'] for opp in opportunities if opp.get("account_id") == acct.get("id"))
    revenue_per_developer = RuleSettings.get("tam.revenue_per_developer", 1000)
    coverage_pct = RuleSettings.get("tam.coverage_percentage", 50)
    tam = acct['numDevelopers'] * revenue_per_developer * coverage_pct / 100
    return {'pipeline': total_opp_amt, 'tam': tam, 'coverage': int(total_opp_amt / tam * 100)}

def undercover_tam_condition(metric_value: dict) -> Severity:
    low_severity = RuleSettings.get("tam.coverage_low_severity_pct", 60)
    medium_severity = RuleSettings.get("tam.coverage_medium_severity_pct", 50)
    high_severity = RuleSettings.get("tam.coverage_high_severity_pct", 40)
    
    if metric_value['coverage'] < high_severity:
        return Severity.HIGH
    elif metric_value['coverage'] < medium_severity:
        return Severity.MEDIUM
    elif metric_value['coverage'] < low_severity:
        return Severity.LOW
    else:
        return Severity.NONE

def undercover_tam_responsible(acct: dict) -> str:
    return acct.get('owner')

def undercover_tam_explanation(metric_name: str, metric_value: dict) -> str:
    return f"TAM: {metric_value['tam']}\nPipeline: {metric_value['pipeline']}\nCoverage: {metric_value['coverage']}%" if metric_value['coverage'] < 100 else "No opportunities found for this account"

UndercoverTam = Rule(
    rule_type="account",
    name="Under-covered TAM",
    category="Territory imbalance",
    metric=undercover_tam_metric,
    condition=undercover_tam_condition,
    responsible=undercover_tam_responsible,
    fields=['accountId', 'amount'],
    metric_name="Under-covered TAM",
    format_metric_value=lambda x: f"{x['coverage']}%",
    explanation=undercover_tam_explanation,
    resolution="Ops should ask rep why there is not enough pipeline for this account",
)
