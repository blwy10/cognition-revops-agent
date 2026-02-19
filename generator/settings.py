from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class DateWindow:
    start: str  # inclusive YYYY-MM-DD
    end: str  # inclusive YYYY-MM-DD


# -----------------
# Primary controls
# -----------------

DEFAULT_SEED = 123

NUM_REPS = 30
NUM_ACCOUNTS = 70
NUM_OPPORTUNITIES = 100

# -----------------
# Input vocab paths
# -----------------
# Text files must be: 1 token per line; blank lines ignored.
#
# You must update these paths to point at your own vocab files.
# They can be absolute, or relative to the working directory.

FIRST_NAMES_PATH = "generator/data/first-names.txt"
LAST_NAMES_PATH = "generator/data/last-names.txt"
ACCOUNT_NOUNS_PATH = "generator/data/nouns.txt"
ACCOUNT_SUFFIXES_PATH = "generator/data/company-suffixes.txt"
INDUSTRIES_PATH = "generator/data/bls-top-level.txt"
STAGES_PATH = "generator/data/partial-stages.txt"

# States/regions JSON must contain a state->region mapping.
# Supported shapes:
# 1) {"CA": "West", "NY": "Northeast", ...}
# 2) {"states": [{"state": "CA", "region": "West"}, ...]}
STATES_TO_REGION_JSON_PATH = "generator/data/regions-formatted.json"

# -----------------
# Account generation
# -----------------

# Annual revenue uses Pareto(xm=1, alpha=PARETO_ALPHA) then scaled into dollars.
# Scaling scheme:
# - We sample r ~ Pareto(alpha=PARETO_ALPHA) which is heavy tail.
# - Then annualRevenue = int(REVENUE_SCALE_DOLLARS * r)
# This yields a mix of SMB/mid-market/enterprise with occasional very large outliers.
PARETO_ALPHA = 1.0
REVENUE_SCALE_DOLLARS = 75_000_000
REVENUE_CAP_DOLLARS = 700_000_000_000

REVENUE_PER_EMPLOYEE_MIN = 20_000
REVENUE_PER_EMPLOYEE_MAX = 1_000_000

DEVELOPER_PCT_MIN = 0.05
DEVELOPER_PCT_MAX = 0.50

IS_CUSTOMER_RATE = 0.30

# ----------------------
# Opportunity generation
# ----------------------

PRODUCTS = ("Devin", "Windsurf")

OPPS_PER_ACCOUNT_MIN = 0
OPPS_PER_ACCOUNT_MAX = 2

# Per-account TAM (dollars)
TAM_PER_DEVELOPER = 1000

COVERAGE_PCT_MIN = 0.50
COVERAGE_PCT_MAX = 1.00

AMOUNT_MULTIPLIER_MIN = 0.50
AMOUNT_MULTIPLIER_MAX = 2.00

# Close date windows
RECENT_CLOSE_WINDOW = DateWindow(start="2025-10-01", end="2026-02-18")
FUTURE_CLOSE_WINDOW = DateWindow(start="2026-02-19", end="2026-09-30")
RECENT_CLOSE_PCT = 0.10
MISSING_CLOSE_PCT = 0.05

# Opportunity created_date window (must be <= 2026-02-18)
OPPORTUNITY_CREATED_WINDOW = DateWindow(start="2024-07-01", end="2026-02-18")

OPPORTUNITY_HISTORY_CHANGE_WINDOW = DateWindow(start="2025-10-01", end="2026-02-18")

# Global pipeline target (after per-account TAM enforcement)
TOTAL_PIPELINE_TARGET = 10_000_000
TOTAL_PIPELINE_MIN = 9_000_000
TOTAL_PIPELINE_MAX = 13_000_000

AMOUNT_RETRY_LIMIT = 20

# -----------------
# Rep quota settings
# -----------------
# Quota is tied to territory expected pipeline (sum of opp amounts in territory)
# with a multiplier, then clamped to a reasonable range.

QUOTA_MULTIPLIER_ON_TERRITORY_PIPELINE = 0.9
QUOTA_MIN = 200_000
QUOTA_MAX = 1_500_000
