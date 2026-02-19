from __future__ import annotations

import datetime as _dt
from collections import defaultdict


def _assert(cond: bool, msg: str) -> None:
    if not cond:
        raise ValueError(msg)


def _is_ymd(s: str) -> bool:
    try:
        _dt.date.fromisoformat(s)
        return True
    except Exception:
        return False


def validate(
    reps: list[dict],
    accounts: list[dict],
    opportunities: list[dict],
    territories: list[dict],
    *,
    expected_reps: int,
    expected_accounts: int,
    expected_opportunities: int,
    expected_total_min: int,
    expected_total_max: int,
    recent_window: tuple[str, str],
    future_window: tuple[str, str],
    expected_recent_count: int,
    tam_per_developer: int,
) -> None:
    _assert(len(reps) == expected_reps, f"Expected {expected_reps} reps, got {len(reps)}")
    _assert(
        len(accounts) == expected_accounts,
        f"Expected {expected_accounts} accounts, got {len(accounts)}",
    )
    _assert(
        len(opportunities) == expected_opportunities,
        f"Expected {expected_opportunities} opportunities, got {len(opportunities)}",
    )

    for i, r in enumerate(reps, start=1):
        _assert(r.get("id") == i, f"Rep ids must be sequential starting at 1 (expected {i})")
    for i, a in enumerate(accounts, start=1):
        _assert(
            a.get("id") == i,
            f"Account ids must be sequential starting at 1 (expected {i})",
        )
    for i, o in enumerate(opportunities, start=1):
        _assert(
            o.get("id") == i,
            f"Opportunity ids must be sequential starting at 1 (expected {i})",
        )
    for i, t in enumerate(territories, start=1):
        _assert(
            t.get("id") == i,
            f"Territory ids must be sequential starting at 1 (expected {i})",
        )

    rep_by_id = {r["id"]: r for r in reps}
    acct_by_id = {a["id"]: a for a in accounts}
    terr_by_id = {t["id"]: t for t in territories}

    _assert(len(rep_by_id) == len(reps), "Duplicate rep ids")
    _assert(len(acct_by_id) == len(accounts), "Duplicate account ids")
    _assert(len(terr_by_id) == len(territories), "Duplicate territory ids")

    rep_by_name = {r.get("name"): r for r in reps}
    acct_by_name = {a.get("name"): a for a in accounts}
    opp_by_name = {o.get("name"): o for o in opportunities}
    terr_by_name = {t.get("name"): t for t in territories}

    _assert(len(rep_by_name) == len(reps), "Duplicate rep names")
    _assert(len(acct_by_name) == len(accounts), "Duplicate account names")
    _assert(len(opp_by_name) == len(opportunities), "Duplicate opportunity names")
    _assert(len(terr_by_name) == len(territories), "Duplicate territory names")

    # Account core relationships
    for a in accounts:
        rep_id = a.get("repId")
        terr_id = a.get("territoryId")
        _assert(rep_id in rep_by_id, f"Account {a['id']} has invalid repId {rep_id}")
        _assert(
            terr_id in terr_by_id,
            f"Account {a['id']} has invalid territoryId {terr_id}",
        )
        _assert(
            rep_by_id[rep_id]["territoryId"] == terr_id,
            f"Account {a['id']} territoryId must equal its rep.territoryId",
        )
        _assert(
            a.get("state") == rep_by_id[rep_id].get("homeState"),
            f"Account {a['id']} state must equal its rep.homeState",
        )

    # Opp relationships + per-account totals
    opps_by_acct: dict[int, list[dict]] = defaultdict(list)
    for o in opportunities:
        acct_id = o.get("accountId")
        rep_id = o.get("repId")
        _assert(acct_id in acct_by_id, f"Opportunity {o['id']} has invalid accountId {acct_id}")
        _assert(rep_id in rep_by_id, f"Opportunity {o['id']} has invalid repId {rep_id}")
        _assert(
            rep_id == acct_by_id[acct_id]["repId"],
            f"Opportunity {o['id']} repId must equal parent account.repId",
        )
        _assert(_is_ymd(o.get("closeDate", "")), f"Opportunity {o['id']} closeDate must be YYYY-MM-DD")
        _assert(isinstance(o.get("amount"), int) and o["amount"] >= 0, f"Opportunity {o['id']} amount must be int >= 0")
        opps_by_acct[acct_id].append(o)

    for a in accounts:
        acct_id = a["id"]
        in_pipeline = len(opps_by_acct.get(acct_id, [])) > 0
        _assert(
            bool(a.get("inPipeline")) == in_pipeline,
            f"Account {acct_id} inPipeline must match whether it has opportunities",
        )

        tam = int(tam_per_developer * int(a["numDevelopers"]))
        acct_total = sum(int(o["amount"]) for o in opps_by_acct.get(acct_id, []))
        _assert(
            acct_total <= tam,
            f"Account {acct_id} violates TAM constraint: total={acct_total} TAM={tam}",
        )

    # Close date distribution
    recent_start, recent_end = map(_dt.date.fromisoformat, recent_window)
    future_start, future_end = map(_dt.date.fromisoformat, future_window)

    recent = 0
    for o in opportunities:
        d = _dt.date.fromisoformat(o["closeDate"])
        if recent_start <= d <= recent_end:
            recent += 1
        else:
            _assert(
                future_start <= d <= future_end,
                f"Opportunity {o['id']} closeDate outside allowed windows: {o['closeDate']}",
            )

    _assert(
        recent == expected_recent_count,
        f"Expected exactly {expected_recent_count} recent closeDates, got {recent}",
    )

    total = sum(int(o["amount"]) for o in opportunities)
    _assert(
        expected_total_min <= total <= expected_total_max,
        f"Total pipeline {total} outside range [{expected_total_min}, {expected_total_max}]",
    )

    # Rep region/state sanity
    for r in reps:
        _assert(isinstance(r.get("quota"), int) and r["quota"] > 0, f"Rep {r['id']} quota must be positive int")
        _assert(isinstance(r.get("homeState"), str) and r["homeState"], f"Rep {r['id']} homeState required")
        _assert(isinstance(r.get("region"), str) and r["region"], f"Rep {r['id']} region required")
