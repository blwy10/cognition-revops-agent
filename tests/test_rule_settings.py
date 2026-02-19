"""Tests for rules.rule_settings module."""
import pytest
from rules.rule_settings import RuleSettings, _RuleSettings


class TestRuleSettings:
    def test_get_default(self):
        assert RuleSettings.get("nonexistent", 42) == 42

    def test_get_none_default(self):
        assert RuleSettings.get("nonexistent") is None

    def test_set_and_get(self):
        RuleSettings.set("test.key", 100)
        assert RuleSettings.get("test.key") == 100

    def test_set_emits_changed(self, qtbot):
        with qtbot.waitSignal(RuleSettings.changed, timeout=500):
            RuleSettings.set("test.signal_key", "hello")

    def test_set_same_value_does_not_emit(self, qtbot):
        RuleSettings.set("test.no_emit", 5)
        with qtbot.assertNotEmitted(RuleSettings.changed, wait=100):
            RuleSettings.set("test.no_emit", 5)

    def test_getitem(self):
        RuleSettings.set("test.bracket", "val")
        assert RuleSettings["test.bracket"] == "val"

    def test_getitem_missing_raises(self):
        with pytest.raises(KeyError):
            _ = RuleSettings["definitely_missing"]

    def test_setitem(self):
        RuleSettings["test.setitem"] = 99
        assert RuleSettings.get("test.setitem") == 99

    def test_to_dict(self):
        RuleSettings.set("a", 1)
        RuleSettings.set("b", 2)
        d = RuleSettings.to_dict()
        assert isinstance(d, dict)
        assert d["a"] == 1
        assert d["b"] == 2

    def test_to_dict_returns_copy(self):
        RuleSettings.set("x", 10)
        d = RuleSettings.to_dict()
        d["x"] = 999
        assert RuleSettings.get("x") == 10

    def test_singleton_identity(self):
        assert isinstance(RuleSettings, _RuleSettings)
