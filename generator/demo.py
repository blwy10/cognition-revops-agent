from __future__ import annotations

from collections import defaultdict

from .generate import generate


def main() -> None:
    reps, accounts, opportunities, territories, opportunity_history = generate()

    total = sum(o.amount for o in opportunities)
    revenues = [a.annualRevenue for a in accounts]

    opps_by_acct = defaultdict(int)
    for o in opportunities:
        opps_by_acct[o.accountId] += 1

    print(f"reps: {len(reps)}")
    print(f"accounts: {len(accounts)}")
    print(f"opportunities: {len(opportunities)}")
    print(f"territories: {len(territories)}")
    print(f"opportunity_history: {len(opportunity_history)}")
    print(f"total_pipeline: {total}")
    print(f"annualRevenue min/max: {min(revenues)} / {max(revenues)}")
    print(f"accounts in pipeline: {sum(1 for a in accounts if a.inPipeline)}")
    print(f"opps per account min/max: {min(opps_by_acct.values(), default=0)} / {max(opps_by_acct.values(), default=0)}")


if __name__ == "__main__":
    main()
