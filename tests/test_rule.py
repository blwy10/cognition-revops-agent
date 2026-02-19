"""Tests for rules.rule module."""
import pytest
from datetime import datetime
from types import SimpleNamespace

from rules.rule import Rule
from rules.rule_result import RuleResult
from rules.severity import Severity


class TestRuleDefaults:
    def test_default_name(self):
        r = Rule()
        assert r.name == ""

    def test_default_category(self):
        r = Rule()
        assert r.category == ""

    def test_default_rule_type(self):
        r = Rule()
        assert r.rule_type == "opportunity"

    def test_default_metric_returns_zero(self):
        r = Rule()
        assert r.metric({}) == 0.0

    def test_default_condition_returns_none_severity(self):
        r = Rule()
        assert r.condition(0) == Severity.NONE

    def test_default_responsible_returns_empty(self):
        r = Rule()
        assert r.responsible({}) == ""

    def test_default_fields_empty(self):
        r = Rule()
        assert r.fields == []

    def test_default_resolution_empty(self):
        r = Rule()
        assert r.resolution == ""


class TestRuleProperties:
    def test_name_setter(self):
        r = Rule(name="Original")
        r.name = "Changed"
        assert r.name == "Changed"

    def test_category_setter(self):
        r = Rule(category="Cat1")
        r.category = "Cat2"
        assert r.category == "Cat2"

    def test_rule_type_setter(self):
        r = Rule(rule_type="opportunity")
        r.rule_type = "account"
        assert r.rule_type == "account"

    def test_responsible_setter(self):
        r = Rule()
        r.responsible = lambda obj: "Bob"
        assert r.responsible({}) == "Bob"

    def test_metric_name_setter(self):
        r = Rule(metric_name="X")
        r.metric_name = "Y"
        assert r.metric_name == "Y"

    def test_metric_setter(self):
        r = Rule()
        r.metric = lambda obj: 42
        assert r.metric({}) == 42

    def test_condition_setter(self):
        r = Rule()
        r.condition = lambda val: Severity.HIGH
        assert r.condition(0) == Severity.HIGH

    def test_fields_setter(self):
        r = Rule()
        r.fields = ["a", "b"]
        assert r.fields == ["a", "b"]

    def test_resolution_setter(self):
        r = Rule()
        r.resolution = "Fix it"
        assert r.resolution == "Fix it"


class TestRuleRun:
    def test_run_returns_none_when_no_severity(self):
        r = Rule(
            name="Test",
            metric=lambda obj: 5,
            condition=lambda val: Severity.NONE,
        )
        assert r.run({}) is None

    def test_run_returns_result_on_severity(self):
        r = Rule(
            name="Test",
            category="Cat",
            rule_type="opportunity",
            metric=lambda obj: 10,
            condition=lambda val: Severity.HIGH,
            responsible=lambda obj: "Alice",
            metric_name="Count",
            format_metric_value=lambda v: f"{v}x",
            explanation=lambda mn, v: f"{mn} is {v}",
            resolution="Do something",
            fields=["field1"],
        )
        opp = SimpleNamespace(account_name="Acme", name="Deal")
        result = r.run(opp)
        assert isinstance(result, RuleResult)
        assert result.name == "Test"
        assert result.category == "Cat"
        assert result.severity == "HIGH"
        assert result.account_name == "Acme"
        assert result.opportunity_name == "Deal"
        assert result.responsible == "Alice"
        assert result.metric_name == "Count"
        assert result.metric_value == 10
        assert result.formatted_metric_value == "10x"
        assert result.explanation == "Count is 10"
        assert result.resolution == "Do something"
        assert result.fields == ("field1",)

    def test_run_opportunity_extracts_names(self):
        r = Rule(
            rule_type="opportunity",
            metric=lambda obj: 1,
            condition=lambda val: Severity.LOW,
        )
        opp = SimpleNamespace(account_name="ACME", name="Big Deal")
        result = r.run(opp)
        assert result.account_name == "ACME"
        assert result.opportunity_name == "Big Deal"

    def test_run_account_extracts_name(self):
        r = Rule(
            rule_type="account",
            metric=lambda obj: 1,
            condition=lambda val: Severity.LOW,
        )
        acct = SimpleNamespace(name="ACME Corp")
        result = r.run(acct)
        assert result.account_name == "ACME Corp"
        assert result.opportunity_name == ""

    def test_run_unknown_type_empty_names(self):
        r = Rule(
            rule_type="portfolio_opp",
            metric=lambda obj: 1,
            condition=lambda val: Severity.LOW,
        )
        result = r.run({})
        assert result.account_name == ""
        assert result.opportunity_name == ""

    def test_run_with_other_context(self):
        def metric_with_ctx(obj, ctx):
            return obj.get("val", 0) + len(ctx.get("items", []))

        r = Rule(
            metric=metric_with_ctx,
            condition=lambda val: Severity.HIGH if val > 5 else Severity.NONE,
        )
        result = r.run({"val": 3}, other_context={"items": [1, 2, 3, 4]})
        assert result is not None
        assert result.metric_value == 7

    def test_run_without_other_context(self):
        r = Rule(
            metric=lambda obj: obj.get("val", 0),
            condition=lambda val: Severity.HIGH if val > 5 else Severity.NONE,
        )
        result = r.run({"val": 10})
        assert result is not None
        assert result.metric_value == 10

    def test_run_result_has_timestamp(self):
        r = Rule(
            metric=lambda obj: 1,
            condition=lambda val: Severity.LOW,
        )
        result = r.run({})
        assert isinstance(result.timestamp, datetime)

    def test_severity_value_in_result(self):
        r = Rule(
            metric=lambda obj: 1,
            condition=lambda val: Severity.MEDIUM,
        )
        result = r.run({})
        assert result.severity == "MEDIUM"
