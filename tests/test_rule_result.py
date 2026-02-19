"""Tests for rules.rule_result module."""
from datetime import datetime

from rules.rule_result import RuleResult


def _make_result(**overrides) -> RuleResult:
    defaults = dict(
        name="Test Rule",
        category="Test Category",
        account_name="Acme Corp",
        opportunity_name="Acme Deal",
        responsible="Alice",
        fields=("amount",),
        metric_name="Amount",
        metric_value=100.0,
        formatted_metric_value="$100",
        timestamp=datetime(2026, 1, 1),
        explanation="Test explanation",
        resolution="Test resolution",
        severity="HIGH",
    )
    defaults.update(overrides)
    return RuleResult(**defaults)


class TestRuleResult:
    def test_all_properties(self):
        r = _make_result()
        assert r.name == "Test Rule"
        assert r.category == "Test Category"
        assert r.account_name == "Acme Corp"
        assert r.opportunity_name == "Acme Deal"
        assert r.responsible == "Alice"
        assert r.fields == ("amount",)
        assert r.metric_name == "Amount"
        assert r.metric_value == 100.0
        assert r.formatted_metric_value == "$100"
        assert r.timestamp == datetime(2026, 1, 1)
        assert r.explanation == "Test explanation"
        assert r.resolution == "Test resolution"
        assert r.severity == "HIGH"

    def test_fields_is_tuple(self):
        r = _make_result(fields=("a", "b", "c"))
        assert isinstance(r.fields, tuple)
        assert len(r.fields) == 3

    def test_empty_fields(self):
        r = _make_result(fields=())
        assert r.fields == ()

    def test_metric_value_can_be_dict(self):
        r = _make_result(metric_value={"days": 30})
        assert r.metric_value == {"days": 30}

    def test_severity_is_string(self):
        r = _make_result(severity="LOW")
        assert isinstance(r.severity, str)
        assert r.severity == "LOW"

    def test_properties_are_readonly(self):
        r = _make_result()
        import pytest
        with pytest.raises(AttributeError):
            r.name = "new"  # type: ignore[misc]
        with pytest.raises(AttributeError):
            r.severity = "LOW"  # type: ignore[misc]
