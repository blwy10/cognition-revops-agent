"""Shared fixtures for the test suite."""
from __future__ import annotations

import os
import sys
import pytest

# ---------------------------------------------------------------------------
# Ensure the project root is on sys.path so that ``import rules``, etc. work
# regardless of how pytest is invoked.
# ---------------------------------------------------------------------------
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


# ---------------------------------------------------------------------------
# RuleSettings helpers – many default rules read from the singleton at import
# time, so we provide a fixture that resets it between tests.
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def _reset_rule_settings():
    """Clear RuleSettings before *and* after every test so tests are isolated."""
    from rules.rule_settings import RuleSettings
    RuleSettings._values.clear()
    yield
    RuleSettings._values.clear()


# ---------------------------------------------------------------------------
# Sample data factories
# ---------------------------------------------------------------------------

@pytest.fixture()
def sample_opportunity():
    """Return a factory that builds a minimal opportunity dict."""
    _counter = 0

    def _make(**overrides) -> dict:
        nonlocal _counter
        _counter += 1
        base = {
            "id": _counter,
            "name": f"Opp {_counter}",
            "amount": 100_000,
            "stage": "2 - Discovery",
            "closeDate": "2026-06-01",
            "created_date": "2025-01-01",
            "repId": 1,
            "accountId": 1,
            "owner": "Alice Smith",
            "account_name": "Acme Corp",
        }
        base.update(overrides)
        return base

    return _make


@pytest.fixture()
def sample_account():
    """Return a factory that builds a minimal account dict."""
    _counter = 0

    def _make(**overrides) -> dict:
        nonlocal _counter
        _counter += 1
        base = {
            "id": _counter,
            "name": f"Account {_counter}",
            "annualRevenue": 10_000_000,
            "numDevelopers": 50,
            "state": "CA",
            "industry": "Technology",
            "isCustomer": False,
            "inPipeline": True,
            "repId": 1,
            "territoryId": 1,
            "owner": "Alice Smith",
        }
        base.update(overrides)
        return base

    return _make


@pytest.fixture()
def sample_rep():
    """Return a factory that builds a minimal rep dict."""
    _counter = 0

    def _make(**overrides) -> dict:
        nonlocal _counter
        _counter += 1
        base = {
            "id": _counter,
            "name": f"Rep {_counter}",
            "homeState": "CA",
            "region": "West",
            "quota": 500_000,
            "territoryId": 1,
        }
        base.update(overrides)
        return base

    return _make


@pytest.fixture()
def sample_territory():
    """Return a factory that builds a minimal territory dict."""
    _counter = 0

    def _make(**overrides) -> dict:
        nonlocal _counter
        _counter += 1
        base = {
            "id": _counter,
            "name": f"Territory {_counter}",
        }
        base.update(overrides)
        return base

    return _make
