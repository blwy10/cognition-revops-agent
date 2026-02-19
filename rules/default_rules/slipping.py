import pandas as pd
from models import Opportunity, OpportunityHistory
from rules.rule import Rule
from rules.severity import Severity
from rules.rule_settings import RuleSettings
from rules.rule_setting_field import RuleSettingField

RULE_ID = "slipping"
RULE_SETTINGS_GROUP = "Slipping Opportunity Settings"
RULE_SETTINGS_FIELDS = [
    RuleSettingField(
        key="slipping.late_stage",
        label="Late stage threshold",
        default=5,
        minimum=0,
        maximum=6,
    ),
    RuleSettingField(
        key="slipping.low_severity",
        label="Number of times postponed (low severity)",
        default=1,
        minimum=0,
        maximum=10,
    ),
    RuleSettingField(
        key="slipping.medium_severity",
        label="Number of times postponed (medium severity)",
        default=2,
        minimum=0,
        maximum=10,
    ),
    RuleSettingField(
        key="slipping.high_severity",
        label="Number of times postponed (high severity)",
        default=3,
        minimum=0,
        maximum=10,
    ),
]

def slipping_metric(opp: Opportunity, history: list[OpportunityHistory]) -> list:
    df = pd.DataFrame([vars(h) for h in history])
    opp_history = df[df['opportunity_id'] == opp.id]
    if opp_history.empty:
        return None
    stages = ['0 - New Opportunity',
              '1 - Qualification',
              '2 - Discovery',
              '3 - Solutioning',
              '4 - Proposal',
              '5 - Negotiation',
              '6 - Awaiting Signature']
    slipping_stage = RuleSettings.get('slipping.late_stage')
    subset_stages = stages[slipping_stage:]
    stage_change_history = opp_history[(opp_history['field_name'] == 'stage') & (opp_history['new_value'].isin(subset_stages))]
    if stage_change_history.empty:
        return None
    earliest_late_stage_date = opp_history['change_date'].min()
    date_changes = opp_history[(opp_history['change_date'] >= earliest_late_stage_date) & (opp_history['field_name'] == 'closeDate')]
    date_changes_sorted = date_changes.sort_values('change_date')
    close_date_history = date_changes_sorted['new_value'].tolist()
    return close_date_history

def slipping_condition(close_date_history: list) -> Severity:
    if not close_date_history or len(close_date_history) < 2:
        return Severity.NONE

    recent_dates = close_date_history[-5:] if len(close_date_history) >= 5 else close_date_history

    consecutive_postponements = 0
    max_consecutive = 0

    for i in range(1, len(recent_dates)):
        if recent_dates[i] > recent_dates[i - 1]:
            consecutive_postponements += 1
            max_consecutive = max(max_consecutive, consecutive_postponements)
        else:
            consecutive_postponements = 0

    if max_consecutive >= RuleSettings.get('slipping.high_severity'):
        return Severity.HIGH
    elif max_consecutive >= RuleSettings.get('slipping.medium_severity'):
        return Severity.MEDIUM
    elif max_consecutive >= RuleSettings.get('slipping.low_severity'):
        return Severity.LOW
    return Severity.NONE

def slipping_responsible(opp: Opportunity) -> str:
    return opp.owner

def slipping_format_value(value: list) -> str:
    recent_dates = value[-5:] if len(value) >= 5 else value
    return "Close date history:\n" + "\n".join(recent_dates)

def slipping_explanation(metric_name: str, value: list) -> str:
    return "This opportunity is slipping - the close date has been postponed."

SlippingRule = Rule(
    rule_type="opportunity",
    settings_id=RULE_ID,
    name="Slipping Opp",
    category="Forecast Risk",
    metric=slipping_metric,
    condition=slipping_condition,
    responsible=slipping_responsible,
    fields=["stage", "closeDate"],
    metric_name='Close date history',
    explanation=slipping_explanation,
    format_metric_value=slipping_format_value,
    resolution="Reach out to the sales rep to understand why the close date has been postponed.",
)
