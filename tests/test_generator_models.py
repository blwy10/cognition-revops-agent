"""Tests for generator.models module (TypedDict schemas)."""
import pytest
from typing import get_type_hints

from generator.models import Rep, Account, Opportunity, OpportunityHistory, Territory


class TestRepTypedDict:
    def test_has_expected_keys(self):
        hints = get_type_hints(Rep)
        expected = {"id", "name", "homeState", "region", "quota", "territoryId"}
        assert set(hints.keys()) == expected

    def test_can_create(self):
        r: Rep = {
            "id": 1, "name": "Alice", "homeState": "CA",
            "region": "West", "quota": 500_000, "territoryId": 1,
        }
        assert r["name"] == "Alice"


class TestAccountTypedDict:
    def test_has_expected_keys(self):
        hints = get_type_hints(Account)
        expected = {
            "id", "name", "annualRevenue", "numDevelopers", "state",
            "industry", "isCustomer", "inPipeline", "repId", "territoryId",
        }
        assert set(hints.keys()) == expected


class TestOpportunityTypedDict:
    def test_has_expected_keys(self):
        hints = get_type_hints(Opportunity)
        expected = {"id", "name", "amount", "stage", "created_date", "closeDate", "repId", "accountId"}
        assert set(hints.keys()) == expected


class TestOpportunityHistoryTypedDict:
    def test_has_expected_keys(self):
        hints = get_type_hints(OpportunityHistory)
        expected = {"id", "opportunity_id", "field_name", "old_value", "new_value", "change_date"}
        assert set(hints.keys()) == expected


class TestTerritoryTypedDict:
    def test_has_expected_keys(self):
        hints = get_type_hints(Territory)
        expected = {"id", "name"}
        assert set(hints.keys()) == expected
