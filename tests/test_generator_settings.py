"""Tests for generator.settings module."""
import pytest
from generator.settings import (
    DateWindow,
    DEFAULT_SEED,
    NUM_REPS,
    NUM_ACCOUNTS,
    NUM_OPPORTUNITIES,
    PRODUCTS,
    OPPS_PER_ACCOUNT_MIN,
    OPPS_PER_ACCOUNT_MAX,
    TOTAL_PIPELINE_MIN,
    TOTAL_PIPELINE_MAX,
    TOTAL_PIPELINE_TARGET,
    RECENT_CLOSE_WINDOW,
    FUTURE_CLOSE_WINDOW,
    OPPORTUNITY_CREATED_WINDOW,
    OPPORTUNITY_HISTORY_CHANGE_WINDOW,
    RECENT_CLOSE_PCT,
    MISSING_CLOSE_PCT,
    QUOTA_MIN,
    QUOTA_MAX,
    FIRST_NAMES_PATH,
    LAST_NAMES_PATH,
    ACCOUNT_NOUNS_PATH,
    ACCOUNT_SUFFIXES_PATH,
    INDUSTRIES_PATH,
    STAGES_PATH,
    STATES_TO_REGION_JSON_PATH,
)


class TestDateWindow:
    def test_frozen(self):
        w = DateWindow(start="2026-01-01", end="2026-12-31")
        with pytest.raises(AttributeError):
            w.start = "2027-01-01"

    def test_fields(self):
        w = DateWindow(start="2026-01-01", end="2026-12-31")
        assert w.start == "2026-01-01"
        assert w.end == "2026-12-31"


class TestSettingsConstants:
    def test_seed_is_int(self):
        assert isinstance(DEFAULT_SEED, int)

    def test_counts_positive(self):
        assert NUM_REPS > 0
        assert NUM_ACCOUNTS > 0
        assert NUM_OPPORTUNITIES > 0

    def test_pipeline_range_valid(self):
        assert TOTAL_PIPELINE_MIN <= TOTAL_PIPELINE_TARGET <= TOTAL_PIPELINE_MAX

    def test_opps_per_account_range(self):
        assert OPPS_PER_ACCOUNT_MIN <= OPPS_PER_ACCOUNT_MAX

    def test_close_pct_in_range(self):
        assert 0 <= RECENT_CLOSE_PCT <= 1
        assert 0 <= MISSING_CLOSE_PCT <= 1

    def test_quota_range(self):
        assert QUOTA_MIN < QUOTA_MAX

    def test_date_windows_chronological(self):
        for w in (RECENT_CLOSE_WINDOW, FUTURE_CLOSE_WINDOW, OPPORTUNITY_CREATED_WINDOW, OPPORTUNITY_HISTORY_CHANGE_WINDOW):
            assert w.start <= w.end, f"{w} start is after end"

    def test_products_non_empty(self):
        assert len(PRODUCTS) > 0

    def test_vocab_paths_are_strings(self):
        for p in (FIRST_NAMES_PATH, LAST_NAMES_PATH, ACCOUNT_NOUNS_PATH,
                  ACCOUNT_SUFFIXES_PATH, INDUSTRIES_PATH, STAGES_PATH,
                  STATES_TO_REGION_JSON_PATH):
            assert isinstance(p, str)
            assert len(p) > 0
