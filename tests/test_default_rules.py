"""Tests for all rules in rules/default_rules/."""
import pytest
from types import SimpleNamespace

from models import Account, Opportunity, Rep
from rules.severity import Severity
from rules.rule import Rule
from rules.rule_result import RuleResult
from rules.rule_settings import RuleSettings


# =========================================================================
# MissingCloseDateRule
# =========================================================================
class TestMissingCloseDateRule:
    @pytest.fixture(autouse=True)
    def _import_rule(self):
        from rules.default_rules.missing_close_date import (
            MissingCloseDateRule,
            missing_close_date_metric,
            missing_close_date_condition,
            missing_close_date_responsible,
            missing_close_date_format_metric_value,
            missing_close_date_explanation,
        )
        self.rule = MissingCloseDateRule
        self.metric = missing_close_date_metric
        self.condition = missing_close_date_condition
        self.responsible = missing_close_date_responsible
        self.format_metric = missing_close_date_format_metric_value
        self.explanation = missing_close_date_explanation

    def test_rule_is_instance_of_rule(self):
        assert isinstance(self.rule, Rule)

    def test_rule_type_is_opportunity(self):
        assert self.rule.rule_type == "opportunity"

    def test_metric_extracts_closedate_and_stage(self):
        opp = Opportunity(id=1, name="Test", amount=100, stage="2 - Discovery", closeDate="2026-06-01")
        m = self.metric(opp)
        assert m == {"closeDate": "2026-06-01", "stage": "2 - Discovery"}

    def test_condition_none_when_close_date_present(self):
        assert self.condition({"closeDate": "2026-06-01", "stage": "2 - Discovery"}) == Severity.NONE

    def test_condition_low_early_stage_missing(self):
        RuleSettings.set("missing_close_date.low_max_stage", 1)
        RuleSettings.set("missing_close_date.medium_max_stage", 2)
        assert self.condition({"closeDate": None, "stage": "1 - Qualification"}) == Severity.LOW

    def test_condition_medium_mid_stage_missing(self):
        RuleSettings.set("missing_close_date.low_max_stage", 1)
        RuleSettings.set("missing_close_date.medium_max_stage", 2)
        assert self.condition({"closeDate": None, "stage": "2 - Discovery"}) == Severity.MEDIUM

    def test_condition_high_late_stage_missing(self):
        RuleSettings.set("missing_close_date.low_max_stage", 1)
        RuleSettings.set("missing_close_date.medium_max_stage", 2)
        assert self.condition({"closeDate": None, "stage": "5 - Negotiation"}) == Severity.HIGH

    def test_condition_high_when_stage_not_parseable(self):
        assert self.condition({"closeDate": None, "stage": "Unknown"}) == Severity.HIGH

    def test_responsible_returns_owner(self):
        opp = Opportunity(id=1, name="Test", amount=100, stage="2 - Discovery", owner="Alice")
        assert self.responsible(opp) == "Alice"

    def test_format_metric_value(self):
        result = self.format_metric({"closeDate": None, "stage": "2 - Discovery"})
        assert "Stage: 2 - Discovery" in result
        assert "Close Date:" in result

    def test_explanation_contains_severity(self):
        RuleSettings.set("missing_close_date.low_max_stage", 1)
        RuleSettings.set("missing_close_date.medium_max_stage", 2)
        expl = self.explanation("Close date", {"closeDate": None, "stage": "5 - Negotiation"})
        assert "high" in expl.lower()

    def test_full_run_fires_on_missing(self):
        opp = Opportunity(id=1, name="Deal", amount=100, stage="3 - Solutioning",
                          closeDate=None, owner="Bob", account_name="Acme")
        RuleSettings.set("missing_close_date.low_max_stage", 1)
        RuleSettings.set("missing_close_date.medium_max_stage", 2)
        result = self.rule.run(opp)
        assert result is not None
        assert result.severity == "HIGH"

    def test_full_run_returns_none_when_present(self):
        opp = Opportunity(id=1, name="Deal", amount=100, stage="3 - Solutioning",
                          closeDate="2026-06-01", owner="Bob", account_name="Acme")
        result = self.rule.run(opp)
        assert result is None


# =========================================================================
# AmountOutlierRule
# =========================================================================
class TestAmountOutlierRule:
    @pytest.fixture(autouse=True)
    def _import_rule(self):
        from rules.default_rules.amount_outlier import (
            AmountOutlierRule,
            amount_outlier_metric,
            amount_outlier_condition,
            amount_outlier_responsible,
            amount_outlier_format_metric_value,
            amount_outlier_explanation,
            _is_closed_stage,
            _safe_int,
            _safe_float,
        )
        self.rule = AmountOutlierRule
        self.metric = amount_outlier_metric
        self.condition = amount_outlier_condition
        self.responsible = amount_outlier_responsible
        self.format_metric = amount_outlier_format_metric_value
        self.explanation = amount_outlier_explanation
        self._is_closed_stage = _is_closed_stage
        self._safe_int = _safe_int
        self._safe_float = _safe_float

    def test_rule_type_is_opportunity(self):
        assert self.rule.rule_type == "opportunity"

    def test_metric_extracts_amount_and_stage(self):
        opp = Opportunity(id=1, name="Test", amount=500_000, stage="3 - Solutioning")
        m = self.metric(opp)
        assert m == {"amount": 500_000, "stage": "3 - Solutioning"}

    def test_is_closed_stage_true(self):
        assert self._is_closed_stage("Closed Won") is True
        assert self._is_closed_stage("7 - Closed Lost") is True

    def test_is_closed_stage_false(self):
        assert self._is_closed_stage("3 - Solutioning") is False
        assert self._is_closed_stage(None) is False
        assert self._is_closed_stage(123) is False

    def test_safe_int(self):
        assert self._safe_int("42", 0) == 42
        assert self._safe_int("abc", 99) == 99
        assert self._safe_int(None, 10) == 10

    def test_safe_float(self):
        assert self._safe_float(42) == 42.0
        assert self._safe_float("3.14") == 3.14
        assert self._safe_float(None) is None
        assert self._safe_float("abc") is None

    def test_condition_none_for_closed_stage(self):
        assert self.condition({"amount": 9_999_999, "stage": "Closed Won"}) == Severity.NONE

    def test_condition_none_for_normal_amount(self):
        assert self.condition({"amount": 200_000, "stage": "2 - Discovery"}) == Severity.NONE

    def test_condition_high_for_very_large(self):
        RuleSettings.set("amount_outlier.high_low_threshold", 300_000)
        RuleSettings.set("amount_outlier.high_medium_threshold", 600_000)
        RuleSettings.set("amount_outlier.high_high_threshold", 1_000_000)
        RuleSettings.set("amount_outlier.low_low_threshold", 60_000)
        RuleSettings.set("amount_outlier.low_medium_threshold", 30_000)
        RuleSettings.set("amount_outlier.low_high_threshold", 20_000)
        assert self.condition({"amount": 2_000_000, "stage": "3 - Solutioning"}) == Severity.HIGH

    def test_condition_low_for_slightly_large(self):
        RuleSettings.set("amount_outlier.high_low_threshold", 300_000)
        RuleSettings.set("amount_outlier.high_medium_threshold", 600_000)
        RuleSettings.set("amount_outlier.high_high_threshold", 1_000_000)
        RuleSettings.set("amount_outlier.low_low_threshold", 60_000)
        RuleSettings.set("amount_outlier.low_medium_threshold", 30_000)
        RuleSettings.set("amount_outlier.low_high_threshold", 20_000)
        assert self.condition({"amount": 400_000, "stage": "3 - Solutioning"}) == Severity.LOW

    def test_condition_high_for_very_small(self):
        RuleSettings.set("amount_outlier.high_low_threshold", 300_000)
        RuleSettings.set("amount_outlier.high_medium_threshold", 600_000)
        RuleSettings.set("amount_outlier.high_high_threshold", 1_000_000)
        RuleSettings.set("amount_outlier.low_low_threshold", 60_000)
        RuleSettings.set("amount_outlier.low_medium_threshold", 30_000)
        RuleSettings.set("amount_outlier.low_high_threshold", 20_000)
        assert self.condition({"amount": 10_000, "stage": "3 - Solutioning"}) == Severity.HIGH

    def test_condition_none_for_none_amount(self):
        assert self.condition({"amount": None, "stage": "3 - Solutioning"}) == Severity.NONE

    def test_condition_none_for_non_dict(self):
        assert self.condition("not a dict") == Severity.NONE

    def test_responsible_returns_owner(self):
        opp = Opportunity(id=1, name="Test", amount=100, stage="2", owner="Bob")
        assert self.responsible(opp) == "Bob"

    def test_responsible_missing_owner(self):
        opp = Opportunity(id=1, name="Test", amount=100, stage="2", owner="")
        assert self.responsible(opp) == ""

    def test_format_metric_value_with_dict(self):
        result = self.format_metric({"amount": 500_000, "stage": "3 - Solutioning"})
        assert "Amount:" in result
        assert "Stage:" in result

    def test_format_metric_value_non_dict(self):
        assert self.format_metric("bad") == ""

    def test_explanation_large(self):
        RuleSettings.set("amount_outlier.high_low_threshold", 300_000)
        RuleSettings.set("amount_outlier.high_medium_threshold", 600_000)
        RuleSettings.set("amount_outlier.high_high_threshold", 1_000_000)
        expl = self.explanation("Amount", {"amount": 2_000_000, "stage": "3"})
        assert "large" in expl.lower()

    def test_explanation_small(self):
        RuleSettings.set("amount_outlier.low_low_threshold", 60_000)
        RuleSettings.set("amount_outlier.low_medium_threshold", 30_000)
        RuleSettings.set("amount_outlier.low_high_threshold", 20_000)
        expl = self.explanation("Amount", {"amount": 10_000, "stage": "3"})
        assert "small" in expl.lower()

    def test_explanation_empty_for_normal(self):
        RuleSettings.set("amount_outlier.high_low_threshold", 300_000)
        RuleSettings.set("amount_outlier.high_medium_threshold", 600_000)
        RuleSettings.set("amount_outlier.high_high_threshold", 1_000_000)
        RuleSettings.set("amount_outlier.low_low_threshold", 60_000)
        RuleSettings.set("amount_outlier.low_medium_threshold", 30_000)
        RuleSettings.set("amount_outlier.low_high_threshold", 20_000)
        expl = self.explanation("Amount", {"amount": 200_000, "stage": "3"})
        assert expl == ""


# =========================================================================
# DuplicateAcctRule
# =========================================================================
class TestDuplicateAcctRule:
    @pytest.fixture(autouse=True)
    def _import_rule(self):
        from rules.default_rules.duplicate_acct import (
            DuplicateAcctRule,
            duplicate_acct_metric,
            duplicate_acct_condition,
            duplicate_acct_responsible,
            duplicate_acct_explanation,
        )
        self.rule = DuplicateAcctRule
        self.metric = duplicate_acct_metric
        self.condition = duplicate_acct_condition
        self.responsible = duplicate_acct_responsible
        self.explanation = duplicate_acct_explanation

    def test_rule_type_is_portfolio_acct(self):
        assert self.rule.rule_type == "portfolio_acct"

    def test_metric_no_duplicates(self):
        accounts = [SimpleNamespace(name="A"), SimpleNamespace(name="B"), SimpleNamespace(name="C")]
        assert self.metric(accounts) == 0

    def test_metric_with_duplicates(self):
        accounts = [SimpleNamespace(name="A"), SimpleNamespace(name="A"), SimpleNamespace(name="B")]
        assert self.metric(accounts) == 1

    def test_metric_multiple_duplicates(self):
        accounts = [SimpleNamespace(name="A"), SimpleNamespace(name="A"), SimpleNamespace(name="A"), SimpleNamespace(name="B"), SimpleNamespace(name="B")]
        assert self.metric(accounts) == 3

    def test_condition_high_when_duplicates_exist(self):
        assert self.condition(1) == Severity.HIGH

    def test_condition_none_when_no_duplicates(self):
        assert self.condition(0) == Severity.NONE

    def test_responsible(self):
        assert self.responsible([]) == "0 - Ops"

    def test_explanation(self):
        expl = self.explanation("Duplicate accounts", 3)
        assert "3" in expl
        assert "duplicate" in expl.lower()

    def test_full_run_with_duplicates(self):
        accounts = [SimpleNamespace(name="A"), SimpleNamespace(name="A"), SimpleNamespace(name="B")]
        result = self.rule.run(accounts)
        assert result is not None
        assert result.severity == "HIGH"

    def test_full_run_no_duplicates(self):
        accounts = [SimpleNamespace(name="A"), SimpleNamespace(name="B"), SimpleNamespace(name="C")]
        result = self.rule.run(accounts)
        assert result is None


# =========================================================================
# NoOpps
# =========================================================================
class TestNoOpps:
    @pytest.fixture(autouse=True)
    def _import_rule(self):
        from rules.default_rules.no_opps import (
            NoOpps,
            no_opps_metric,
            no_opps_condition,
            no_opps_responsible,
            no_opps_explanation,
        )
        self.rule = NoOpps
        self.metric = no_opps_metric
        self.condition = no_opps_condition
        self.responsible = no_opps_responsible
        self.explanation = no_opps_explanation

    def test_rule_type_is_account(self):
        assert self.rule.rule_type == "account"

    def test_metric_zero_when_no_matching_opps(self):
        acct = SimpleNamespace(id=1)
        opps = [SimpleNamespace(accountId=2), SimpleNamespace(accountId=3)]
        assert self.metric(acct, opps) == 0

    def test_metric_counts_matching_opps(self):
        acct = SimpleNamespace(id=1)
        opps = [SimpleNamespace(accountId=1), SimpleNamespace(accountId=2), SimpleNamespace(accountId=1)]
        assert self.metric(acct, opps) == 2

    def test_condition_high_when_zero(self):
        assert self.condition(0) == Severity.HIGH

    def test_condition_none_when_nonzero(self):
        assert self.condition(1) == Severity.NONE
        assert self.condition(5) == Severity.NONE

    def test_responsible(self):
        acct = SimpleNamespace(owner="Alice")
        assert self.responsible(acct) == "Alice"

    def test_explanation_zero(self):
        assert "no opportunities" in self.explanation("", 0).lower()

    def test_explanation_nonzero(self):
        assert self.explanation("", 1) == ""

    def test_full_run_fires(self):
        acct = SimpleNamespace(id=1, name="Acme", owner="Alice")
        opps = [SimpleNamespace(accountId=2)]
        result = self.rule.run(acct, other_context=opps)
        assert result is not None
        assert result.severity == "HIGH"

    def test_full_run_none_when_has_opps(self):
        acct = SimpleNamespace(id=1, name="Acme", owner="Alice")
        opps = [SimpleNamespace(accountId=1)]
        result = self.rule.run(acct, other_context=opps)
        assert result is None


# =========================================================================
# AcctPerRepAboveThreshold
# =========================================================================
class TestAcctPerRep:
    @pytest.fixture(autouse=True)
    def _import_rule(self):
        from rules.default_rules.acct_per_rep import (
            AcctPerRepAboveThreshold,
            acct_per_rep_metric,
            acct_per_rep_condition,
            acct_per_rep_responsible,
            acct_per_rep_explanation,
        )
        self.rule = AcctPerRepAboveThreshold
        self.metric = acct_per_rep_metric
        self.condition = acct_per_rep_condition
        self.responsible = acct_per_rep_responsible
        self.explanation = acct_per_rep_explanation

    def test_rule_type_is_rep(self):
        assert self.rule.rule_type == "rep"

    def test_metric_counts_unique_accounts(self):
        rep = SimpleNamespace(name="Alice")
        opps = [
            SimpleNamespace(owner="Alice", accountId=1),
            SimpleNamespace(owner="Alice", accountId=1),
            SimpleNamespace(owner="Alice", accountId=2),
            SimpleNamespace(owner="Bob", accountId=3),
        ]
        assert self.metric(rep, opps) == 2

    def test_metric_zero_for_no_matching(self):
        rep = SimpleNamespace(name="Charlie")
        opps = [SimpleNamespace(owner="Alice", accountId=1)]
        assert self.metric(rep, opps) == 0

    def test_condition_none_below_threshold(self):
        RuleSettings.set("acct_per_rep.low_severity", 6)
        assert self.condition(5) == Severity.NONE

    def test_condition_low(self):
        RuleSettings.set("acct_per_rep.low_severity", 6)
        RuleSettings.set("acct_per_rep.medium_severity", 10)
        RuleSettings.set("acct_per_rep.high_severity", 15)
        assert self.condition(7) == Severity.LOW

    def test_condition_medium(self):
        RuleSettings.set("acct_per_rep.low_severity", 6)
        RuleSettings.set("acct_per_rep.medium_severity", 10)
        RuleSettings.set("acct_per_rep.high_severity", 15)
        assert self.condition(12) == Severity.MEDIUM

    def test_condition_high(self):
        RuleSettings.set("acct_per_rep.low_severity", 6)
        RuleSettings.set("acct_per_rep.medium_severity", 10)
        RuleSettings.set("acct_per_rep.high_severity", 15)
        assert self.condition(20) == Severity.HIGH

    def test_responsible_is_ops(self):
        assert self.responsible({}) == "0 - Ops"

    def test_explanation_contains_count(self):
        RuleSettings.set("acct_per_rep.low_severity", 6)
        RuleSettings.set("acct_per_rep.medium_severity", 10)
        RuleSettings.set("acct_per_rep.high_severity", 15)
        expl = self.explanation("Accts per rep", 20)
        assert "20" in expl


# =========================================================================
# PipelinePerRepImbalance
# =========================================================================
class TestPipelineImbalance:
    @pytest.fixture(autouse=True)
    def _import_rule(self):
        from rules.default_rules.pipeline_imbalance import (
            PipelinePerRepImbalance,
            pipeline_per_rep_metric,
            pipeline_per_rep_condition,
            pipeline_per_rep_responsible,
            pipeline_per_rep_format_value,
            pipeline_per_rep_explanation,
        )
        self.rule = PipelinePerRepImbalance
        self.metric = pipeline_per_rep_metric
        self.condition = pipeline_per_rep_condition
        self.responsible = pipeline_per_rep_responsible
        self.format_value = pipeline_per_rep_format_value
        self.explanation = pipeline_per_rep_explanation

    def test_rule_type_is_rep(self):
        assert self.rule.rule_type == "rep"

    def test_metric_sums_amounts(self):
        rep = SimpleNamespace(name="Alice")
        opps = [
            SimpleNamespace(owner="Alice", amount=100_000),
            SimpleNamespace(owner="Alice", amount=200_000),
            SimpleNamespace(owner="Bob", amount=500_000),
        ]
        assert self.metric(rep, opps) == 300_000

    def test_metric_zero_for_no_matching(self):
        rep = SimpleNamespace(name="Charlie")
        opps = [SimpleNamespace(owner="Alice", amount=100_000)]
        assert self.metric(rep, opps) == 0

    def test_condition_none_below(self):
        RuleSettings.set("pipeline_imbalance.low_severity", 500_000)
        assert self.condition(400_000) == Severity.NONE

    def test_condition_low(self):
        RuleSettings.set("pipeline_imbalance.low_severity", 500_000)
        RuleSettings.set("pipeline_imbalance.medium_severity", 600_000)
        RuleSettings.set("pipeline_imbalance.high_severity", 800_000)
        assert self.condition(550_000) == Severity.LOW

    def test_condition_high(self):
        RuleSettings.set("pipeline_imbalance.low_severity", 500_000)
        RuleSettings.set("pipeline_imbalance.medium_severity", 600_000)
        RuleSettings.set("pipeline_imbalance.high_severity", 800_000)
        assert self.condition(900_000) == Severity.HIGH

    def test_responsible_is_ops(self):
        assert self.responsible({}) == "0 - Ops"

    def test_format_value(self):
        assert "USD" in self.format_value(500_000)

    def test_explanation_contains_amount(self):
        RuleSettings.set("pipeline_imbalance.low_severity", 500_000)
        RuleSettings.set("pipeline_imbalance.medium_severity", 600_000)
        RuleSettings.set("pipeline_imbalance.high_severity", 800_000)
        expl = self.explanation("Pipeline imbalance", 900_000)
        assert "900,000" in expl


# =========================================================================
# PortfolioEarlyStageConcentrationRule
# =========================================================================
class TestPortfolioEarlyStageConcentration:
    @pytest.fixture(autouse=True)
    def _import_rule(self):
        from rules.default_rules.portfolio_early_stage_concentration import (
            PortfolioEarlyStageConcentrationRule,
            portfolio_early_stage_concentration_metric,
            portfolio_early_stage_concentration_condition,
            portfolio_early_stage_concentration_responsible,
            portfolio_early_stage_concentration_formatted_metric_value,
            portfolio_early_stage_concentration_explanation,
        )
        self.rule = PortfolioEarlyStageConcentrationRule
        self.metric = portfolio_early_stage_concentration_metric
        self.condition = portfolio_early_stage_concentration_condition
        self.responsible = portfolio_early_stage_concentration_responsible
        self.format_value = portfolio_early_stage_concentration_formatted_metric_value
        self.explanation = portfolio_early_stage_concentration_explanation

    def test_rule_type_is_portfolio_opp(self):
        assert self.rule.rule_type == "portfolio_opp"

    def test_metric_counts_early_stages(self):
        opps = [
            SimpleNamespace(stage="0 - New Opportunity"),
            SimpleNamespace(stage="1 - Qualification"),
            SimpleNamespace(stage="3 - Solutioning"),
            SimpleNamespace(stage="5 - Negotiation"),
        ]
        m = self.metric(opps)
        assert m["total_opps"] == 4
        assert m["stage_0_and_1_opps"] == 2

    def test_metric_empty_opps(self):
        m = self.metric([])
        assert m["total_opps"] == 0
        assert m["stage_0_and_1_opps"] == 0

    def test_condition_none_low_concentration(self):
        RuleSettings.set("portfolio_early_stage_concentration.low_pct", 35)
        RuleSettings.set("portfolio_early_stage_concentration.medium_pct", 45)
        RuleSettings.set("portfolio_early_stage_concentration.high_pct", 60)
        assert self.condition({"total_opps": 10, "stage_0_and_1_opps": 2}) == Severity.NONE

    def test_condition_high_heavy_concentration(self):
        RuleSettings.set("portfolio_early_stage_concentration.low_pct", 35)
        RuleSettings.set("portfolio_early_stage_concentration.medium_pct", 45)
        RuleSettings.set("portfolio_early_stage_concentration.high_pct", 60)
        assert self.condition({"total_opps": 10, "stage_0_and_1_opps": 7}) == Severity.HIGH

    def test_condition_zero_total_opps(self):
        assert self.condition({"total_opps": 0, "stage_0_and_1_opps": 0}) == Severity.NONE

    def test_responsible_is_ops(self):
        assert self.responsible([]) == "0 - Ops"

    def test_format_value(self):
        result = self.format_value({"total_opps": 10, "stage_0_and_1_opps": 4})
        assert "Total Opps: 10" in result
        assert "Ratio:" in result

    def test_full_run_fires(self):
        opps = [SimpleNamespace(stage="0 - New Opportunity")] * 7 + [SimpleNamespace(stage="3 - Solutioning")] * 3
        RuleSettings.set("portfolio_early_stage_concentration.low_pct", 35)
        RuleSettings.set("portfolio_early_stage_concentration.medium_pct", 45)
        RuleSettings.set("portfolio_early_stage_concentration.high_pct", 60)
        result = self.rule.run(opps)
        assert result is not None
        assert result.severity == "HIGH"


# =========================================================================
# RepEarlyStageConcentrationRule
# =========================================================================
class TestRepEarlyStageConcentration:
    @pytest.fixture(autouse=True)
    def _import_rule(self):
        from rules.default_rules.rep_early_stage_concentration import (
            RepEarlyStageConcentrationRule,
            rep_early_stage_concentration_metric,
            rep_early_stage_concentration_condition,
            rep_early_stage_concentration_responsible,
            rep_early_stage_concentration_formatted_metric_value,
        )
        self.rule = RepEarlyStageConcentrationRule
        self.metric = rep_early_stage_concentration_metric
        self.condition = rep_early_stage_concentration_condition
        self.responsible = rep_early_stage_concentration_responsible
        self.format_value = rep_early_stage_concentration_formatted_metric_value

    def test_rule_type_is_rep(self):
        assert self.rule.rule_type == "rep"

    def test_metric_filters_by_rep(self):
        rep = SimpleNamespace(name="Alice")
        opps = [
            SimpleNamespace(owner="Alice", stage="0 - New Opportunity"),
            SimpleNamespace(owner="Alice", stage="3 - Solutioning"),
            SimpleNamespace(owner="Bob", stage="0 - New Opportunity"),
        ]
        m = self.metric(rep, opps)
        assert m["total_opps"] == 2
        assert m["stage_0_and_1_opps"] == 1

    def test_condition_none_below_min_opps(self):
        RuleSettings.set("rep_early_stage_concentration.min_opps", 10)
        assert self.condition({"total_opps": 5, "stage_0_and_1_opps": 5}) == Severity.NONE

    def test_condition_high_above_threshold(self):
        RuleSettings.set("rep_early_stage_concentration.min_opps", 5)
        RuleSettings.set("rep_early_stage_concentration.low_pct", 35)
        RuleSettings.set("rep_early_stage_concentration.medium_pct", 45)
        RuleSettings.set("rep_early_stage_concentration.high_pct", 60)
        assert self.condition({"total_opps": 10, "stage_0_and_1_opps": 8}) == Severity.HIGH

    def test_responsible_returns_rep_name(self):
        rep = SimpleNamespace(name="Alice")
        assert self.responsible(rep) == "Alice"

    def test_format_value(self):
        result = self.format_value({"total_opps": 10, "stage_0_and_1_opps": 4})
        assert "Total Opps: 10" in result


# =========================================================================
# SlippingRule
# =========================================================================
class TestSlippingRule:
    @pytest.fixture(autouse=True)
    def _import_rule(self):
        from rules.default_rules.slipping import (
            SlippingRule,
            slipping_condition,
            slipping_responsible,
            slipping_format_value,
            slipping_explanation,
        )
        self.rule = SlippingRule
        self.condition = slipping_condition
        self.responsible = slipping_responsible
        self.format_value = slipping_format_value
        self.explanation = slipping_explanation

    def test_rule_type_is_opportunity(self):
        assert self.rule.rule_type == "opportunity"

    def test_condition_none_empty(self):
        assert self.condition(None) == Severity.NONE
        assert self.condition([]) == Severity.NONE

    def test_condition_none_single_date(self):
        assert self.condition(["2026-01-01"]) == Severity.NONE

    def test_condition_low_single_postponement(self):
        RuleSettings.set("slipping.low_severity", 1)
        RuleSettings.set("slipping.medium_severity", 2)
        RuleSettings.set("slipping.high_severity", 3)
        dates = ["2026-01-01", "2026-02-01"]
        assert self.condition(dates) == Severity.LOW

    def test_condition_high_many_postponements(self):
        RuleSettings.set("slipping.low_severity", 1)
        RuleSettings.set("slipping.medium_severity", 2)
        RuleSettings.set("slipping.high_severity", 3)
        dates = ["2026-01-01", "2026-02-01", "2026-03-01", "2026-04-01"]
        assert self.condition(dates) == Severity.HIGH

    def test_condition_none_when_dates_go_backward(self):
        RuleSettings.set("slipping.low_severity", 1)
        RuleSettings.set("slipping.medium_severity", 2)
        RuleSettings.set("slipping.high_severity", 3)
        dates = ["2026-04-01", "2026-03-01"]
        assert self.condition(dates) == Severity.NONE

    def test_responsible_returns_owner(self):
        opp = Opportunity(id=1, name="Test", amount=100, stage="2", owner="Bob")
        assert self.responsible(opp) == "Bob"

    def test_format_value(self):
        dates = ["2026-01-01", "2026-02-01", "2026-03-01"]
        result = self.format_value(dates)
        assert "2026-01-01" in result
        assert "Close date history" in result

    def test_explanation(self):
        expl = self.explanation("Close date history", ["2026-01-01", "2026-02-01"])
        assert "slipping" in expl.lower()


# =========================================================================
# StalenessRule
# =========================================================================
class TestStalenessRule:
    @pytest.fixture(autouse=True)
    def _import_rule(self):
        from rules.default_rules.stale import (
            StalenessRule,
            staleness_condition,
            staleness_responsible,
            staleness_format_value,
        )
        self.rule = StalenessRule
        self.condition = staleness_condition
        self.responsible = staleness_responsible
        self.format_value = staleness_format_value

    def test_rule_type_is_opportunity(self):
        assert self.rule.rule_type == "opportunity"

    def test_condition_none_when_recent(self):
        RuleSettings.set("stale_opportunity.low_days", 30)
        RuleSettings.set("stale_opportunity.medium_days", 60)
        RuleSettings.set("stale_opportunity.high_days", 90)
        assert self.condition({"days_since_last_change": 10, "last_change_date": None}) == Severity.NONE

    def test_condition_low(self):
        RuleSettings.set("stale_opportunity.low_days", 30)
        RuleSettings.set("stale_opportunity.medium_days", 60)
        RuleSettings.set("stale_opportunity.high_days", 90)
        assert self.condition({"days_since_last_change": 40, "last_change_date": None}) == Severity.LOW

    def test_condition_medium(self):
        RuleSettings.set("stale_opportunity.low_days", 30)
        RuleSettings.set("stale_opportunity.medium_days", 60)
        RuleSettings.set("stale_opportunity.high_days", 90)
        assert self.condition({"days_since_last_change": 70, "last_change_date": None}) == Severity.MEDIUM

    def test_condition_high(self):
        RuleSettings.set("stale_opportunity.low_days", 30)
        RuleSettings.set("stale_opportunity.medium_days", 60)
        RuleSettings.set("stale_opportunity.high_days", 90)
        assert self.condition({"days_since_last_change": 100, "last_change_date": None}) == Severity.HIGH

    def test_responsible(self):
        opp = Opportunity(id=1, name="Test", amount=100, stage="2", owner="Alice")
        assert self.responsible(opp) == "Alice"


# =========================================================================
# UndercoverTam
# =========================================================================
class TestUndercoverTam:
    @pytest.fixture(autouse=True)
    def _import_rule(self):
        from rules.default_rules.undercover_tam import (
            UndercoverTam,
            undercover_tam_metric,
            undercover_tam_condition,
            undercover_tam_responsible,
            undercover_tam_explanation,
        )
        self.rule = UndercoverTam
        self.metric = undercover_tam_metric
        self.condition = undercover_tam_condition
        self.responsible = undercover_tam_responsible
        self.explanation = undercover_tam_explanation

    def test_rule_type_is_account(self):
        assert self.rule.rule_type == "account"

    def test_metric_no_opps(self):
        acct = SimpleNamespace(id=1, numDevelopers=50)
        opps = [SimpleNamespace(accountId=2, amount=100)]
        RuleSettings.set("tam.revenue_per_developer", 1000)
        RuleSettings.set("tam.coverage_percentage", 50)
        m = self.metric(acct, opps)
        assert m["pipeline"] == 0
        assert m["coverage"] == 100

    def test_metric_with_opps(self):
        acct = SimpleNamespace(id=1, numDevelopers=100)
        opps = [
            SimpleNamespace(accountId=1, amount=10_000),
            SimpleNamespace(accountId=1, amount=15_000),
        ]
        RuleSettings.set("tam.revenue_per_developer", 1000)
        RuleSettings.set("tam.coverage_percentage", 50)
        m = self.metric(acct, opps)
        assert m["pipeline"] == 25_000
        assert m["tam"] == 50_000
        assert m["coverage"] == 50

    def test_condition_none_high_coverage(self):
        RuleSettings.set("tam.coverage_low_severity_pct", 60)
        RuleSettings.set("tam.coverage_medium_severity_pct", 50)
        RuleSettings.set("tam.coverage_high_severity_pct", 40)
        assert self.condition({"coverage": 80}) == Severity.NONE

    def test_condition_low(self):
        RuleSettings.set("tam.coverage_low_severity_pct", 60)
        RuleSettings.set("tam.coverage_medium_severity_pct", 50)
        RuleSettings.set("tam.coverage_high_severity_pct", 40)
        assert self.condition({"coverage": 55}) == Severity.LOW

    def test_condition_high(self):
        RuleSettings.set("tam.coverage_low_severity_pct", 60)
        RuleSettings.set("tam.coverage_medium_severity_pct", 50)
        RuleSettings.set("tam.coverage_high_severity_pct", 40)
        assert self.condition({"coverage": 30}) == Severity.HIGH

    def test_responsible(self):
        acct = SimpleNamespace(owner="Alice")
        assert self.responsible(acct) == "Alice"

    def test_explanation_under_coverage(self):
        expl = self.explanation("TAM", {"tam": 50_000, "pipeline": 10_000, "coverage": 20})
        assert "TAM" in expl
        assert "Pipeline" in expl

    def test_explanation_full_coverage(self):
        expl = self.explanation("TAM", {"tam": 50_000, "pipeline": 50_000, "coverage": 100})
        assert "no opportunities" in expl.lower()
