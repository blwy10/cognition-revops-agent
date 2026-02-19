from __future__ import annotations

from . import settings
from .generate import generate
from .validate import validate


def main() -> None:
    reps, accounts, opportunities, territories, opportunity_history = generate(seed=123)

    validate(
        reps,
        accounts,
        opportunities,
        territories,
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

    total = sum(int(o["amount"]) for o in opportunities)
    print(
        f"OK reps={len(reps)} accounts={len(accounts)} opps={len(opportunities)} territories={len(territories)} "
        f"history={len(opportunity_history)} total={total}"
    )


if __name__ == "__main__":
    main()
