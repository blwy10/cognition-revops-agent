"""Tests for rules.severity module."""
from rules.severity import Severity


class TestSeverityEnum:
    def test_members_exist(self):
        assert hasattr(Severity, "NONE")
        assert hasattr(Severity, "LOW")
        assert hasattr(Severity, "MEDIUM")
        assert hasattr(Severity, "HIGH")

    def test_values(self):
        assert Severity.NONE.value == "NONE"
        assert Severity.LOW.value == "LOW"
        assert Severity.MEDIUM.value == "MEDIUM"
        assert Severity.HIGH.value == "HIGH"

    def test_member_count(self):
        assert len(Severity) == 4

    def test_identity_comparison(self):
        assert Severity.HIGH is Severity.HIGH
        assert Severity.HIGH == Severity.HIGH
        assert Severity.HIGH != Severity.LOW

    def test_from_value(self):
        assert Severity("NONE") is Severity.NONE
        assert Severity("HIGH") is Severity.HIGH

    def test_iteration(self):
        members = list(Severity)
        assert len(members) == 4
        assert Severity.NONE in members
        assert Severity.HIGH in members
