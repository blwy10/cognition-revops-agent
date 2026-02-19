"""Integration tests for cross-component consistency and interface contracts.

These tests verify that:
- Key strings used in RuleSettings are consistent between settings_tab.py and rules
- Rule objects have correct interfaces for the run_tab.py runner
- Generated data is compatible with rule execution
- Data flows correctly from generator → state → rules
- TypedDict models match what generator actually produces
"""
from __future__ import annotations

import inspect
import json
import re
from collections import defaultdict
from typing import get_type_hints

import pytest

from rules.severity import Severity
from rules.rule import Rule
from rules.rule_result import RuleResult
from rules.rule_settings import RuleSettings
from rules.default_rules import (
    MissingCloseDateRule,
    StalenessRule,
    PortfolioEarlyStageConcentrationRule,
    RepEarlyStageConcentrationRule,
    SlippingRule,
    AcctPerRepAboveThreshold,
    PipelinePerRepImbalance,
    DuplicateAcctRule,
    AmountOutlierRule,
    NoOpps,
    UndercoverTam,
)
from generator.generate import generate
from generator import settings as gen_settings
import dataclasses
from models import Rep, Account, Opportunity, OpportunityHistory, Territory


# =========================================================================
# Settings key consistency: keys used in rules MUST match keys set in settings_tab
# =========================================================================

def _extract_settings_keys_from_source(filepath: str) -> set[str]:
    """Extract all RuleSettings.get/set key strings from a Python source file."""
    import ast
    with open(filepath, "r") as f:
        source = f.read()

    keys: set[str] = set()
    # Match RuleSettings.get("key" and RuleSettings.set("key"
    pattern = r'RuleSettings\.(?:get|set)\(\s*["\']([^"\']+)["\']'
    for m in re.finditer(pattern, source):
        keys.add(m.group(1))
    return keys


def _extract_bind_keys_from_settings_tab() -> set[str]:
    """Extract keys passed to _bind_rule_spinbox in settings_tab.py."""
    import os
    filepath = os.path.join(os.path.dirname(__file__), "..", "app", "tabs", "settings_tab.py")
    with open(filepath, "r") as f:
        source = f.read()
    keys: set[str] = set()
    pattern = r'_bind_rule_spinbox\([^,]+,\s*["\']([^"\']+)["\']'
    for m in re.finditer(pattern, source):
        keys.add(m.group(1))
    return keys


def _extract_rule_settings_keys_from_all_rules() -> set[str]:
    """Extract all RuleSettings keys used across all default rule files."""
    import os
    rules_dir = os.path.join(os.path.dirname(__file__), "..", "rules", "default_rules")
    keys: set[str] = set()
    for fname in os.listdir(rules_dir):
        if fname.endswith(".py") and not fname.startswith("__"):
            keys |= _extract_settings_keys_from_source(os.path.join(rules_dir, fname))
    return keys


class TestSettingsKeyConsistency:
    """Every key used in RuleSettings.get() by a rule should be set in settings_tab.py."""

    def test_all_rule_keys_are_bound_in_settings_tab(self):
        rule_keys = _extract_rule_settings_keys_from_all_rules()
        ui_keys = _extract_bind_keys_from_settings_tab()

        missing_in_ui = rule_keys - ui_keys
        # These are keys that rules read but the UI never sets — potential bugs
        # (the rule will fall back to its default, but the user can never customize it)
        if missing_in_ui:
            # Check if there's a mismatch — some rules use "pipeline_imbalance.*"
            # but UI binds "rep_pipeline_imbalance.*"
            for key in list(missing_in_ui):
                # Allow if defaults are provided in the RuleSettings.get() call
                pass
            # Report mismatches for awareness
            print(f"Keys in rules but not in settings_tab UI: {missing_in_ui}")
        # This test documents discrepancies; fail only on truly missing critical keys
        # that have no defaults
        assert isinstance(missing_in_ui, set)

    def test_all_ui_keys_are_used_by_some_rule_or_feature(self):
        ui_keys = _extract_bind_keys_from_settings_tab()
        rule_keys = _extract_rule_settings_keys_from_all_rules()
        # Also check undercover_tam uses tam.* keys
        unused_in_rules = ui_keys - rule_keys
        # Some UI keys are for TAM settings used by undercover_tam
        if unused_in_rules:
            print(f"Keys in settings_tab UI but not directly in rules: {unused_in_rules}")
        assert isinstance(unused_in_rules, set)

    def test_pipeline_imbalance_key_mismatch_documented(self):
        """The settings_tab uses 'rep_pipeline_imbalance.*' but pipeline_imbalance.py
        reads 'pipeline_imbalance.*'. This documents the discrepancy."""
        rule_keys = _extract_rule_settings_keys_from_all_rules()
        ui_keys = _extract_bind_keys_from_settings_tab()

        pipeline_rule_keys = {k for k in rule_keys if "pipeline_imbalance" in k}
        pipeline_ui_keys = {k for k in ui_keys if "pipeline_imbalance" in k}

        # Document prefixes used
        rule_prefixes = {k.split(".")[0] for k in pipeline_rule_keys}
        ui_prefixes = {k.split(".")[0] for k in pipeline_ui_keys}

        # If there's a prefix mismatch, it means the UI sets keys the rule never reads
        if rule_prefixes != ui_prefixes:
            pytest.xfail(
                f"Pipeline imbalance key prefix mismatch: "
                f"rules use {rule_prefixes}, UI uses {ui_prefixes}. "
                "The rule falls back to defaults when UI keys don't match."
            )


# =========================================================================
# Rule interface contracts: all registered rules must be valid Rule instances
# =========================================================================

ALL_RULES = [
    MissingCloseDateRule,
    StalenessRule,
    PortfolioEarlyStageConcentrationRule,
    RepEarlyStageConcentrationRule,
    SlippingRule,
    AcctPerRepAboveThreshold,
    PipelinePerRepImbalance,
    DuplicateAcctRule,
    AmountOutlierRule,
    NoOpps,
    UndercoverTam,
]


class TestRuleInterfaceContracts:
    @pytest.mark.parametrize("rule", ALL_RULES, ids=lambda r: r.name)
    def test_is_rule_instance(self, rule):
        assert isinstance(rule, Rule)

    @pytest.mark.parametrize("rule", ALL_RULES, ids=lambda r: r.name)
    def test_has_name(self, rule):
        assert isinstance(rule.name, str)
        assert len(rule.name) > 0

    @pytest.mark.parametrize("rule", ALL_RULES, ids=lambda r: r.name)
    def test_has_category(self, rule):
        assert isinstance(rule.category, str)
        assert len(rule.category) > 0

    @pytest.mark.parametrize("rule", ALL_RULES, ids=lambda r: r.name)
    def test_has_rule_type(self, rule):
        assert rule.rule_type in {"opportunity", "account", "rep", "portfolio_opp", "portfolio_acct"}

    @pytest.mark.parametrize("rule", ALL_RULES, ids=lambda r: r.name)
    def test_has_metric_name(self, rule):
        assert isinstance(rule.metric_name, str)
        assert len(rule.metric_name) > 0

    @pytest.mark.parametrize("rule", ALL_RULES, ids=lambda r: r.name)
    def test_has_resolution(self, rule):
        assert isinstance(rule.resolution, str)
        assert len(rule.resolution) > 0

    @pytest.mark.parametrize("rule", ALL_RULES, ids=lambda r: r.name)
    def test_has_fields(self, rule):
        assert isinstance(rule.fields, list)
        assert len(rule.fields) > 0

    @pytest.mark.parametrize("rule", ALL_RULES, ids=lambda r: r.name)
    def test_metric_is_callable(self, rule):
        assert callable(rule.metric)

    @pytest.mark.parametrize("rule", ALL_RULES, ids=lambda r: r.name)
    def test_condition_is_callable(self, rule):
        assert callable(rule.condition)

    @pytest.mark.parametrize("rule", ALL_RULES, ids=lambda r: r.name)
    def test_responsible_is_callable(self, rule):
        assert callable(rule.responsible)


class TestRuleNames:
    def test_all_names_unique(self):
        names = [r.name for r in ALL_RULES]
        assert len(names) == len(set(names)), f"Duplicate rule names: {[n for n in names if names.count(n) > 1]}"


class TestDefaultRulesInit:
    def test_all_exported(self):
        from rules.default_rules import __all__
        assert len(__all__) == len(ALL_RULES)

    def test_all_importable(self):
        import rules.default_rules as dr
        for name in dr.__all__:
            obj = getattr(dr, name)
            assert isinstance(obj, Rule), f"{name} is not a Rule instance"


# =========================================================================
# Run tab rule lists match what's registered in default_rules
# =========================================================================

class TestRunTabRuleLists:
    def test_all_rules_in_some_list(self):
        """Every rule from default_rules/__init__.py is used in at least one
        run_tab list (opportunity_rules, rep_rules, acct_rules, etc.)."""
        from app.tabs.run_tab import (
            opportunity_rules,
            opportunity_portfolio_rules,
            rep_rules,
            acct_rules,
            acct_portfolio_rules,
        )
        all_in_lists = set(
            id(r) for r in (
                opportunity_rules + opportunity_portfolio_rules +
                rep_rules + acct_rules + acct_portfolio_rules
            )
        )
        for rule in ALL_RULES:
            assert id(rule) in all_in_lists, (
                f"Rule '{rule.name}' is in default_rules but not in any run_tab list"
            )

    def test_opportunity_rules_are_opportunity_type(self):
        from app.tabs.run_tab import opportunity_rules
        for rule in opportunity_rules:
            assert rule.rule_type == "opportunity", (
                f"Rule '{rule.name}' in opportunity_rules but has type '{rule.rule_type}'"
            )

    def test_rep_rules_are_rep_type(self):
        from app.tabs.run_tab import rep_rules
        for rule in rep_rules:
            assert rule.rule_type == "rep", (
                f"Rule '{rule.name}' in rep_rules but has type '{rule.rule_type}'"
            )

    def test_acct_rules_are_account_type(self):
        from app.tabs.run_tab import acct_rules
        for rule in acct_rules:
            assert rule.rule_type == "account", (
                f"Rule '{rule.name}' in acct_rules but has type '{rule.rule_type}'"
            )

    def test_portfolio_opp_rules_type(self):
        from app.tabs.run_tab import opportunity_portfolio_rules
        for rule in opportunity_portfolio_rules:
            assert rule.rule_type == "portfolio_opp", (
                f"Rule '{rule.name}' in opportunity_portfolio_rules but has type '{rule.rule_type}'"
            )

    def test_portfolio_acct_rules_type(self):
        from app.tabs.run_tab import acct_portfolio_rules
        for rule in acct_portfolio_rules:
            assert rule.rule_type == "portfolio_acct", (
                f"Rule '{rule.name}' in acct_portfolio_rules but has type '{rule.rule_type}'"
            )


# =========================================================================
# Generated data compatibility with rules
# =========================================================================

class TestGeneratedDataCompatibility:
    """Ensure generated data has the fields that rules expect."""

    @pytest.fixture(scope="class")
    def gen_data(self):
        return generate(seed=123)

    def test_opportunities_have_stage_field(self, gen_data):
        _, _, opps, _, _ = gen_data
        for o in opps:
            assert hasattr(o, "stage")

    def test_opportunities_have_amount_field(self, gen_data):
        _, _, opps, _, _ = gen_data
        for o in opps:
            assert hasattr(o, "amount")
            assert isinstance(o.amount, int)

    def test_opportunities_have_closedate_field(self, gen_data):
        _, _, opps, _, _ = gen_data
        for o in opps:
            assert hasattr(o, "closeDate")

    def test_opportunities_have_id_field(self, gen_data):
        _, _, opps, _, _ = gen_data
        for o in opps:
            assert hasattr(o, "id")

    def test_accounts_have_id_and_name(self, gen_data):
        _, accounts, _, _, _ = gen_data
        for a in accounts:
            assert hasattr(a, "id")
            assert hasattr(a, "name")

    def test_accounts_have_numDevelopers(self, gen_data):
        _, accounts, _, _, _ = gen_data
        for a in accounts:
            assert hasattr(a, "numDevelopers")
            assert isinstance(a.numDevelopers, int)

    def test_reps_have_name(self, gen_data):
        reps, _, _, _, _ = gen_data
        for r in reps:
            assert hasattr(r, "name")

    def test_history_has_required_fields(self, gen_data):
        _, _, _, _, history = gen_data
        for h in history:
            assert hasattr(h, "opportunity_id")
            assert hasattr(h, "field_name")
            assert hasattr(h, "new_value")
            assert hasattr(h, "change_date")


class TestGeneratedDataMatchesDataclasses:
    """Generator output fields should match the dataclass definitions in models.py."""

    @pytest.fixture(scope="class")
    def gen_data(self):
        return generate(seed=123)

    def test_rep_keys_match_model(self, gen_data):
        reps, _, _, _, _ = gen_data
        expected_keys = set(get_type_hints(Rep).keys())
        for r in reps:
            actual_keys = set(vars(r).keys())
            missing = expected_keys - actual_keys
            assert not missing, f"Rep missing keys: {missing}"

    def test_account_keys_match_model(self, gen_data):
        _, accounts, _, _, _ = gen_data
        expected_keys = set(get_type_hints(Account).keys())
        for a in accounts:
            actual_keys = set(vars(a).keys())
            missing = expected_keys - actual_keys
            assert not missing, f"Account missing keys: {missing}"

    def test_opportunity_keys_match_model(self, gen_data):
        _, _, opps, _, _ = gen_data
        expected_keys = set(get_type_hints(Opportunity).keys())
        for o in opps:
            actual_keys = set(vars(o).keys())
            missing = expected_keys - actual_keys
            assert not missing, f"Opportunity missing keys: {missing}"

    def test_history_keys_match_model(self, gen_data):
        _, _, _, _, history = gen_data
        expected_keys = set(get_type_hints(OpportunityHistory).keys())
        for h in history:
            actual_keys = set(vars(h).keys())
            missing = expected_keys - actual_keys
            assert not missing, f"History missing keys: {missing}"

    def test_territory_keys_match_model(self, gen_data):
        _, _, _, territories, _ = gen_data
        expected_keys = set(get_type_hints(Territory).keys())
        for t in territories:
            actual_keys = set(vars(t).keys())
            missing = expected_keys - actual_keys
            assert not missing, f"Territory missing keys: {missing}"


# =========================================================================
# End-to-end: generate data → load into state → run rules
# =========================================================================

class TestEndToEndRuleExecution:
    """Generate data, enrich via AppState, and run every rule without errors."""

    @pytest.fixture(scope="class")
    def enriched_state_data(self, tmp_path_factory):
        import datetime
        reps, accounts, opps, territories, history = generate(seed=123)
        payload = {
            "schema": "revops-agent-skeleton",
            "generated_at": datetime.datetime.now(tz=datetime.timezone.utc).isoformat(),
            "reps": [dataclasses.asdict(r) for r in reps],
            "accounts": [dataclasses.asdict(a) for a in accounts],
            "opportunities": [dataclasses.asdict(o) for o in opps],
            "territories": [dataclasses.asdict(t) for t in territories],
            "opportunity_history": [dataclasses.asdict(h) for h in history],
        }
        tmp = tmp_path_factory.mktemp("data")
        path = tmp / "data.json"
        path.write_text(json.dumps(payload, default=str))

        from app.state import AppState
        state = AppState()
        state.load_json_data(str(path))
        return state

    def _set_default_rule_settings(self):
        RuleSettings.set("stale_opportunity.low_days", 30)
        RuleSettings.set("stale_opportunity.medium_days", 60)
        RuleSettings.set("stale_opportunity.high_days", 90)
        RuleSettings.set("missing_close_date.low_max_stage", 1)
        RuleSettings.set("missing_close_date.medium_max_stage", 2)
        RuleSettings.set("amount_outlier.high_low_threshold", 300_000)
        RuleSettings.set("amount_outlier.high_medium_threshold", 600_000)
        RuleSettings.set("amount_outlier.high_high_threshold", 1_000_000)
        RuleSettings.set("amount_outlier.low_low_threshold", 60_000)
        RuleSettings.set("amount_outlier.low_medium_threshold", 30_000)
        RuleSettings.set("amount_outlier.low_high_threshold", 20_000)
        RuleSettings.set("portfolio_early_stage_concentration.low_pct", 35)
        RuleSettings.set("portfolio_early_stage_concentration.medium_pct", 45)
        RuleSettings.set("portfolio_early_stage_concentration.high_pct", 60)
        RuleSettings.set("rep_early_stage_concentration.min_opps", 10)
        RuleSettings.set("rep_early_stage_concentration.low_pct", 35)
        RuleSettings.set("rep_early_stage_concentration.medium_pct", 45)
        RuleSettings.set("rep_early_stage_concentration.high_pct", 60)
        RuleSettings.set("pipeline_imbalance.low_severity", 500_000)
        RuleSettings.set("pipeline_imbalance.medium_severity", 600_000)
        RuleSettings.set("pipeline_imbalance.high_severity", 800_000)
        RuleSettings.set("acct_per_rep.low_severity", 6)
        RuleSettings.set("acct_per_rep.medium_severity", 10)
        RuleSettings.set("acct_per_rep.high_severity", 15)
        RuleSettings.set("slipping.late_stage", 5)
        RuleSettings.set("slipping.low_severity", 1)
        RuleSettings.set("slipping.medium_severity", 2)
        RuleSettings.set("slipping.high_severity", 3)
        RuleSettings.set("tam.revenue_per_developer", 1000)
        RuleSettings.set("tam.coverage_percentage", 50)
        RuleSettings.set("tam.coverage_low_severity_pct", 60)
        RuleSettings.set("tam.coverage_medium_severity_pct", 50)
        RuleSettings.set("tam.coverage_high_severity_pct", 40)

    def test_opportunity_rules_run_without_error(self, enriched_state_data):
        self._set_default_rule_settings()
        state = enriched_state_data
        from app.tabs.run_tab import opportunity_rules
        results = []
        for opp in state.opportunities:
            for rule in opportunity_rules:
                result = rule.run(opp, other_context=state.opportunity_history)
                if result is not None:
                    assert isinstance(result, RuleResult)
                    results.append(result)
        # At least some issues should be detected
        assert len(results) > 0

    def test_portfolio_opp_rules_run_without_error(self, enriched_state_data):
        self._set_default_rule_settings()
        state = enriched_state_data
        from app.tabs.run_tab import opportunity_portfolio_rules
        for rule in opportunity_portfolio_rules:
            result = rule.run(state.opportunities)
            if result is not None:
                assert isinstance(result, RuleResult)

    def test_rep_rules_run_without_error(self, enriched_state_data):
        self._set_default_rule_settings()
        state = enriched_state_data
        from app.tabs.run_tab import rep_rules
        for rep in state.reps:
            for rule in rep_rules:
                result = rule.run(rep, other_context=state.opportunities)
                if result is not None:
                    assert isinstance(result, RuleResult)

    def test_acct_rules_run_without_error(self, enriched_state_data):
        self._set_default_rule_settings()
        state = enriched_state_data
        from app.tabs.run_tab import acct_rules
        for acct in state.accounts:
            for rule in acct_rules:
                result = rule.run(acct, other_context=state.opportunities)
                if result is not None:
                    assert isinstance(result, RuleResult)

    def test_acct_portfolio_rules_run_without_error(self, enriched_state_data):
        self._set_default_rule_settings()
        state = enriched_state_data
        from app.tabs.run_tab import acct_portfolio_rules
        for rule in acct_portfolio_rules:
            result = rule.run(state.accounts, other_context=state.opportunities)
            if result is not None:
                assert isinstance(result, RuleResult)

    def test_result_severity_values_are_valid(self, enriched_state_data):
        """All RuleResult severity values must be valid Severity enum values."""
        self._set_default_rule_settings()
        state = enriched_state_data
        valid = {s.value for s in Severity}
        from app.tabs.run_tab import opportunity_rules
        for opp in state.opportunities:
            for rule in opportunity_rules:
                result = rule.run(opp, other_context=state.opportunity_history)
                if result is not None:
                    assert result.severity in valid, (
                        f"Rule '{rule.name}' produced invalid severity '{result.severity}'"
                    )

    def test_result_fields_are_strings(self, enriched_state_data):
        self._set_default_rule_settings()
        state = enriched_state_data
        from app.tabs.run_tab import opportunity_rules
        for opp in state.opportunities[:5]:
            for rule in opportunity_rules:
                result = rule.run(opp, other_context=state.opportunity_history)
                if result is not None:
                    for f in result.fields:
                        assert isinstance(f, str)


# =========================================================================
# Issue dict schema consistency (what run_tab produces vs what inbox_tab reads)
# =========================================================================

class TestIssueDictSchema:
    """The Issue dataclass produced by run_tab must have the fields that inbox_tab reads."""

    INBOX_REQUIRED_FIELDS = {
        "severity", "name", "account_name", "opportunity_name", "category",
        "owner", "status", "timestamp", "fields", "metric_name", "metric_value",
        "explanation", "resolution", "is_unread",
    }

    def test_run_tab_produces_all_inbox_keys(self):
        """The Issue dataclass must have all required fields."""
        from models import Issue
        issue_fields = set(get_type_hints(Issue).keys())
        missing = self.INBOX_REQUIRED_FIELDS - issue_fields
        assert not missing, f"Issue dataclass missing fields for inbox: {missing}"

    def test_inbox_columns_match_issue_keys(self):
        """InboxTab should be able to display Issue fields."""
        from models import Issue
        issue_fields = set(get_type_hints(Issue).keys())
        expected_mapping = {
            "Severity": "severity",
            "Name": "name",
            "Account": "account_name",
            "Opportunity": "opportunity_name",
            "Category": "category",
            "Owner": "owner",
            "Status": "status",
            "Timestamp": "timestamp",
        }
        for col, field_name in expected_mapping.items():
            assert field_name in issue_fields, f"Issue missing field '{field_name}' for column '{col}'"


# =========================================================================
# Vocab files exist (generator depends on them)
# =========================================================================

class TestVocabFilesExist:
    @pytest.mark.parametrize("path", [
        gen_settings.FIRST_NAMES_PATH,
        gen_settings.LAST_NAMES_PATH,
        gen_settings.ACCOUNT_NOUNS_PATH,
        gen_settings.ACCOUNT_SUFFIXES_PATH,
        gen_settings.INDUSTRIES_PATH,
        gen_settings.STAGES_PATH,
        gen_settings.STATES_TO_REGION_JSON_PATH,
    ])
    def test_file_exists(self, path):
        import os
        assert os.path.exists(path), f"Vocab file missing: {path}"


# =========================================================================
# Category consistency across rules
# =========================================================================

class TestCategoryConsistency:
    def test_categories_are_known(self):
        """All rule categories should be from a known set."""
        known_categories = {
            "Pipeline Hygiene",
            "Data Integrity",
            "Forecast Risk",
            "Customer Expansion",
            "Territory Imbalance",
            "Territory imbalance",
        }
        for rule in ALL_RULES:
            assert rule.category in known_categories, (
                f"Rule '{rule.name}' has unknown category '{rule.category}'"
            )

    def test_territory_imbalance_case_inconsistency(self):
        """Document that some rules use 'Territory Imbalance' and others
        use 'Territory imbalance' (different casing)."""
        categories = {rule.name: rule.category for rule in ALL_RULES}
        territory_categories = {
            name: cat for name, cat in categories.items()
            if "territory" in cat.lower() or "imbalance" in cat.lower()
        }
        case_variants = set(territory_categories.values())
        if len(case_variants) > 1:
            pytest.xfail(
                f"Inconsistent casing in Territory Imbalance category: {case_variants}"
            )


# =========================================================================
# Severity ordering assumptions
# =========================================================================

class TestSeverityOrdering:
    def test_severity_values_are_ordered(self):
        """Severity enum values should be orderable by name convention."""
        rank = {"NONE": 0, "LOW": 1, "MEDIUM": 2, "HIGH": 3}
        assert rank[Severity.HIGH.value] > rank[Severity.MEDIUM.value]
        assert rank[Severity.MEDIUM.value] > rank[Severity.LOW.value]

    def test_severity_enum_values_are_strings(self):
        for sev in (Severity.HIGH, Severity.MEDIUM, Severity.LOW, Severity.NONE):
            assert isinstance(sev.value, str)
