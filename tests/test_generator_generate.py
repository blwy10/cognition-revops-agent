"""Tests for generator.generate module."""
import datetime as _dt
import pytest

from generator import generate as gen_module
from generator.generate import (
    generate,
    _clamp_ymd_min,
    _is_ymd,
    _ensure_unique_names,
    _clamp_int,
    _build_account_name,
    _build_rep_name,
    _reconcile_opp_counts,
    _enforce_tam_int,
)
from generator.rng import Rng
from generator import settings


# =========================================================================
# Helper functions
# =========================================================================

class TestClampYmdMin:
    def test_no_clamp_needed(self):
        assert _clamp_ymd_min("2026-06-01", "2026-01-01") == "2026-06-01"

    def test_clamp_applied(self):
        assert _clamp_ymd_min("2025-01-01", "2026-01-01") == "2026-01-01"

    def test_equal_values(self):
        assert _clamp_ymd_min("2026-01-01", "2026-01-01") == "2026-01-01"


class TestIsYmd:
    def test_valid_date(self):
        assert _is_ymd("2026-01-15") is True

    def test_invalid_date(self):
        assert _is_ymd("not-a-date") is False

    def test_empty_string(self):
        assert _is_ymd("") is False

    def test_partial_date(self):
        assert _is_ymd("2026-01") is False


class TestEnsureUniqueNames:
    def test_no_duplicates(self):
        items = [{"name": "A"}, {"name": "B"}, {"name": "C"}]
        _ensure_unique_names(items, kind="test")
        names = [i["name"] for i in items]
        assert len(set(names)) == 3

    def test_duplicates_resolved(self):
        items = [{"name": "A"}, {"name": "A"}, {"name": "A"}]
        _ensure_unique_names(items, kind="test")
        names = [i["name"] for i in items]
        assert len(set(names)) == 3
        assert names[0] == "A"
        assert "A (2)" in names
        assert "A (3)" in names

    def test_missing_name_raises(self):
        items = [{"name": ""}]
        with pytest.raises(ValueError, match="missing name"):
            _ensure_unique_names(items, kind="test")


class TestClampInt:
    def test_within_range(self):
        assert _clamp_int(5.0, 0, 10) == 5

    def test_below_range(self):
        assert _clamp_int(-5.0, 0, 10) == 0

    def test_above_range(self):
        assert _clamp_int(15.0, 0, 10) == 10


class TestBuildNames:
    def test_build_account_name(self):
        rng = Rng.from_seed(0)
        name = _build_account_name(rng, ["Acme", "Widget"], ["Corp", "Inc"])
        assert isinstance(name, str)
        parts = name.split(" ")
        assert len(parts) == 2

    def test_build_rep_name(self):
        rng = Rng.from_seed(0)
        name = _build_rep_name(rng, ["Alice", "Bob"], ["Smith", "Jones"])
        assert isinstance(name, str)
        parts = name.split(" ")
        assert len(parts) == 2


class TestReconcileOppCounts:
    def test_sum_matches_target(self):
        rng = Rng.from_seed(0)
        counts = [1, 1, 1, 1, 1]
        result = _reconcile_opp_counts(rng, counts, 10)
        assert sum(result) == 10

    def test_reduce_to_target(self):
        rng = Rng.from_seed(0)
        counts = [2, 2, 2, 2, 2]
        result = _reconcile_opp_counts(rng, counts, 5)
        assert sum(result) == 5

    def test_already_at_target(self):
        rng = Rng.from_seed(0)
        counts = [2, 3]
        result = _reconcile_opp_counts(rng, counts, 5)
        assert sum(result) == 5


class TestEnforceTamInt:
    def test_under_tam_unchanged(self):
        amounts = [100, 200, 300]
        result = _enforce_tam_int(amounts, 1000)
        assert result == [100, 200, 300]

    def test_over_tam_scaled_down(self):
        amounts = [500, 500, 500]
        result = _enforce_tam_int(amounts, 1000)
        assert sum(result) <= 1000

    def test_exact_tam(self):
        amounts = [500, 500]
        result = _enforce_tam_int(amounts, 1000)
        assert sum(result) <= 1000

    def test_empty_amounts(self):
        result = _enforce_tam_int([], 1000)
        assert result == []


# =========================================================================
# Full generate() integration
# =========================================================================

class TestGenerate:
    @pytest.fixture(scope="class")
    def generated_data(self):
        """Run generate once and share across tests in this class."""
        return generate(seed=123)

    def test_returns_five_tuple(self, generated_data):
        assert len(generated_data) == 5

    def test_rep_count(self, generated_data):
        reps, _, _, _, _ = generated_data
        assert len(reps) == settings.NUM_REPS

    def test_account_count(self, generated_data):
        _, accounts, _, _, _ = generated_data
        assert len(accounts) == settings.NUM_ACCOUNTS

    def test_opportunity_count(self, generated_data):
        _, _, opps, _, _ = generated_data
        assert len(opps) == settings.NUM_OPPORTUNITIES

    def test_rep_ids_sequential(self, generated_data):
        reps, _, _, _, _ = generated_data
        for i, r in enumerate(reps, 1):
            assert r.id == i

    def test_account_ids_sequential(self, generated_data):
        _, accounts, _, _, _ = generated_data
        for i, a in enumerate(accounts, 1):
            assert a.id == i

    def test_opportunity_ids_sequential(self, generated_data):
        _, _, opps, _, _ = generated_data
        for i, o in enumerate(opps, 1):
            assert o.id == i

    def test_unique_rep_names(self, generated_data):
        reps, _, _, _, _ = generated_data
        names = [r.name for r in reps]
        assert len(set(names)) == len(names)

    def test_unique_account_names(self, generated_data):
        _, accounts, _, _, _ = generated_data
        names = [a.name for a in accounts]
        assert len(set(names)) == len(names)

    def test_unique_opportunity_names(self, generated_data):
        _, _, opps, _, _ = generated_data
        names = [o.name for o in opps]
        assert len(set(names)) == len(names)

    def test_total_pipeline_in_range(self, generated_data):
        _, _, opps, _, _ = generated_data
        total = sum(o.amount for o in opps)
        assert settings.TOTAL_PIPELINE_MIN <= total <= settings.TOTAL_PIPELINE_MAX

    def test_opportunity_amounts_non_negative(self, generated_data):
        _, _, opps, _, _ = generated_data
        for o in opps:
            assert o.amount >= 0

    def test_account_repid_valid(self, generated_data):
        reps, accounts, _, _, _ = generated_data
        rep_ids = {r.id for r in reps}
        for a in accounts:
            assert a.repId in rep_ids

    def test_opportunity_accountid_valid(self, generated_data):
        _, accounts, opps, _, _ = generated_data
        acct_ids = {a.id for a in accounts}
        for o in opps:
            assert o.accountId in acct_ids

    def test_opportunity_repid_matches_account(self, generated_data):
        _, accounts, opps, _, _ = generated_data
        acct_rep = {a.id: a.repId for a in accounts}
        for o in opps:
            assert o.repId == acct_rep[o.accountId]

    def test_territories_exist(self, generated_data):
        _, _, _, territories, _ = generated_data
        assert len(territories) > 0

    def test_opportunity_history_exists(self, generated_data):
        _, _, _, _, history = generated_data
        assert len(history) > 0

    def test_opportunity_history_references_valid_opps(self, generated_data):
        _, _, opps, _, history = generated_data
        opp_ids = {o.id for o in opps}
        for h in history:
            assert h.opportunity_id in opp_ids

    def test_history_field_names_valid(self, generated_data):
        _, _, _, _, history = generated_data
        valid_fields = {"stage", "closeDate"}
        for h in history:
            assert h.field_name in valid_fields

    def test_close_date_distribution(self, generated_data):
        _, _, opps, _, _ = generated_data
        missing = sum(1 for o in opps if o.closeDate is None)
        expected_missing = int(round(settings.NUM_OPPORTUNITIES * settings.MISSING_CLOSE_PCT))
        assert missing == expected_missing

    def test_reps_have_quotas(self, generated_data):
        reps, _, _, _, _ = generated_data
        for r in reps:
            assert isinstance(r.quota, int)
            assert r.quota > 0

    def test_reps_have_regions(self, generated_data):
        reps, _, _, _, _ = generated_data
        for r in reps:
            assert isinstance(r.region, str)
            assert r.region != ""

    def test_reps_have_home_state(self, generated_data):
        reps, _, _, _, _ = generated_data
        for r in reps:
            assert isinstance(r.homeState, str)
            assert r.homeState != ""

    def test_accounts_have_state_matching_rep(self, generated_data):
        reps, accounts, _, _, _ = generated_data
        rep_by_id = {r.id: r for r in reps}
        for a in accounts:
            rep = rep_by_id[a.repId]
            assert a.state == rep.homeState

    def test_created_date_present(self, generated_data):
        _, _, opps, _, _ = generated_data
        for o in opps:
            assert hasattr(o, "created_date")
            assert _is_ymd(o.created_date)

    def test_deterministic_with_same_seed(self):
        r1 = generate(seed=42)
        r2 = generate(seed=42)
        assert r1[0] == r2[0]  # reps
        assert r1[1] == r2[1]  # accounts
        assert r1[2] == r2[2]  # opportunities

    def test_different_seed_produces_different_data(self):
        r1 = generate(seed=1)
        r2 = generate(seed=2)
        names1 = [r.name for r in r1[0]]
        names2 = [r.name for r in r2[0]]
        assert names1 != names2
