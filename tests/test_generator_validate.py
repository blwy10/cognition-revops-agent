"""Tests for generator.validate module."""
import pytest

from generator.validate import validate, _is_ymd
from generator.generate import generate
from generator import settings


class TestIsYmd:
    def test_valid(self):
        assert _is_ymd("2026-01-15") is True

    def test_invalid(self):
        assert _is_ymd("not-a-date") is False

    def test_empty(self):
        assert _is_ymd("") is False


class TestValidateHappyPath:
    """Run validate against freshly generated data — should pass without error."""

    @pytest.fixture(scope="class")
    def data(self):
        return generate(seed=123)

    def test_validate_passes(self, data):
        reps, accounts, opps, territories, _ = data
        validate(
            reps, accounts, opps, territories,
            expected_reps=settings.NUM_REPS,
            expected_accounts=settings.NUM_ACCOUNTS,
            expected_opportunities=settings.NUM_OPPORTUNITIES,
            expected_total_min=settings.TOTAL_PIPELINE_MIN,
            expected_total_max=settings.TOTAL_PIPELINE_MAX,
            recent_window=(settings.RECENT_CLOSE_WINDOW.start, settings.RECENT_CLOSE_WINDOW.end),
            future_window=(settings.FUTURE_CLOSE_WINDOW.start, settings.FUTURE_CLOSE_WINDOW.end),
            expected_recent_count=int(settings.NUM_OPPORTUNITIES * settings.RECENT_CLOSE_PCT),
            tam_per_developer=settings.TAM_PER_DEVELOPER,
        )


class TestValidateErrorCases:
    """Validate raises on bad data."""

    @pytest.fixture()
    def good_data(self):
        return generate(seed=123)

    def _default_kwargs(self):
        return dict(
            expected_reps=settings.NUM_REPS,
            expected_accounts=settings.NUM_ACCOUNTS,
            expected_opportunities=settings.NUM_OPPORTUNITIES,
            expected_total_min=settings.TOTAL_PIPELINE_MIN,
            expected_total_max=settings.TOTAL_PIPELINE_MAX,
            recent_window=(settings.RECENT_CLOSE_WINDOW.start, settings.RECENT_CLOSE_WINDOW.end),
            future_window=(settings.FUTURE_CLOSE_WINDOW.start, settings.FUTURE_CLOSE_WINDOW.end),
            expected_recent_count=int(settings.NUM_OPPORTUNITIES * settings.RECENT_CLOSE_PCT),
            tam_per_developer=settings.TAM_PER_DEVELOPER,
        )

    def test_wrong_rep_count(self, good_data):
        reps, accounts, opps, territories, _ = good_data
        kwargs = self._default_kwargs()
        kwargs["expected_reps"] = 999
        with pytest.raises(ValueError, match="Expected 999 reps"):
            validate(reps, accounts, opps, territories, **kwargs)

    def test_wrong_account_count(self, good_data):
        reps, accounts, opps, territories, _ = good_data
        kwargs = self._default_kwargs()
        kwargs["expected_accounts"] = 999
        with pytest.raises(ValueError, match="Expected 999 accounts"):
            validate(reps, accounts, opps, territories, **kwargs)

    def test_wrong_opp_count(self, good_data):
        reps, accounts, opps, territories, _ = good_data
        kwargs = self._default_kwargs()
        kwargs["expected_opportunities"] = 999
        with pytest.raises(ValueError, match="Expected 999 opportunities"):
            validate(reps, accounts, opps, territories, **kwargs)

    def test_duplicate_rep_ids(self, good_data):
        reps, accounts, opps, territories, _ = good_data
        bad_reps = list(reps)
        bad_reps[1] = dict(bad_reps[0])  # duplicate id
        kwargs = self._default_kwargs()
        with pytest.raises(ValueError):
            validate(bad_reps, accounts, opps, territories, **kwargs)
