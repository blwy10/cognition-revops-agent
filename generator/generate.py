from __future__ import annotations

from collections import defaultdict

from . import settings
from .io import parse_state_region_mapping, read_json, read_text_list
from .rng import Rng


def _clamp_int(x: float, lo: int, hi: int) -> int:
    if x < lo:
        return lo
    if x > hi:
        return hi
    return int(x)


def _build_account_name(rng: Rng, nouns: list[str], suffixes: list[str]) -> str:
    return f"{rng.choice(nouns)} {rng.choice(suffixes)}"


def _build_rep_name(rng: Rng, first: list[str], last: list[str]) -> str:
    return f"{rng.choice(first)} {rng.choice(last)}"


def _pareto_revenue(rng: Rng) -> int:
    # Pareto sampling approach:
    # random.Random.paretovariate(alpha) returns a value >= 1 with heavy tail.
    # We use alpha from settings and then scale into dollars.
    r = rng.paretovariate(float(settings.PARETO_ALPHA))
    dollars = int(settings.REVENUE_SCALE_DOLLARS * r)
    if dollars > settings.REVENUE_CAP_DOLLARS:
        dollars = settings.REVENUE_CAP_DOLLARS
    return dollars


def _num_developers(rng: Rng, annual_revenue: int) -> int:
    revenue_per_employee = rng.uniform(
        float(settings.REVENUE_PER_EMPLOYEE_MIN), float(settings.REVENUE_PER_EMPLOYEE_MAX)
    )
    total_employees = annual_revenue / revenue_per_employee
    developer_pct = rng.uniform(settings.DEVELOPER_PCT_MIN, settings.DEVELOPER_PCT_MAX)
    devs = int(round(total_employees * developer_pct))
    return max(1, devs)


def _reconcile_opp_counts(rng: Rng, counts: list[int], target: int) -> list[int]:
    total = sum(counts)
    lo = settings.OPPS_PER_ACCOUNT_MIN
    hi = settings.OPPS_PER_ACCOUNT_MAX

    while total < target:
        eligible = [i for i, c in enumerate(counts) if c < hi]
        if not eligible:
            raise RuntimeError("Cannot add opportunities: no eligible accounts < max")
        idx = rng.choice(eligible)
        counts[idx] += 1
        total += 1

    while total > target:
        eligible = [i for i, c in enumerate(counts) if c > lo]
        if not eligible:
            raise RuntimeError("Cannot remove opportunities: no eligible accounts > min")
        idx = rng.choice(eligible)
        counts[idx] -= 1
        total -= 1

    return counts


def _enforce_tam_int(amounts: list[int], tam: int) -> list[int]:
    # Deterministic TAM enforcement with rounding-safe overflow adjustment.
    total = sum(amounts)
    if total <= tam:
        return amounts

    if total <= 0:
        return amounts

    factor = tam / float(total)
    scaled = [int(round(a * factor)) for a in amounts]

    # Re-check and if rounding overflow happens, subtract a few dollars from largest opps.
    while sum(scaled) > tam and any(a > 0 for a in scaled):
        i = max(range(len(scaled)), key=lambda j: scaled[j])
        if scaled[i] <= 0:
            break
        scaled[i] -= 1

    return scaled


def _generate_amounts_for_accounts(
    rng: Rng,
    accounts: list[dict],
    opp_counts: list[int],
) -> dict[int, list[int]]:
    # Per-account TAM enforcement:
    # - Compute TAM = TAM_PER_DEVELOPER * numDevelopers
    # - Choose coveragePct ~ U[0.5, 1.0]
    # - X = TAM * coveragePct
    # - Each opp amount = X * U where U ~ U[0.5, 2.0]
    # - If sum exceeds TAM, scale down deterministically to TAM.
    by_account: dict[int, list[int]] = {}

    for acct, n in zip(accounts, opp_counts, strict=True):
        acct_id = int(acct["id"])
        if n <= 0:
            by_account[acct_id] = []
            continue

        tam = int(settings.TAM_PER_DEVELOPER * int(acct["numDevelopers"]))
        coverage = rng.uniform(settings.COVERAGE_PCT_MIN, settings.COVERAGE_PCT_MAX)
        x = tam * coverage

        raw = []
        for _ in range(n):
            u = rng.uniform(settings.AMOUNT_MULTIPLIER_MIN, settings.AMOUNT_MULTIPLIER_MAX)
            raw.append(int(round(x * u)))

        enforced = _enforce_tam_int(raw, tam)
        by_account[acct_id] = enforced

    return by_account


def _try_global_scale(
    accounts: list[dict],
    opp_amounts_by_account: dict[int, list[int]],
) -> dict[int, list[int]]:
    # Global scaling logic:
    # Multiply all opportunity amounts by a single constant k towards 10M,
    # but only if no account total exceeds its TAM after scaling.
    totals = []
    per_acct_total: dict[int, int] = {}

    for acct in accounts:
        acct_id = int(acct["id"])
        amounts = opp_amounts_by_account.get(acct_id, [])
        t = sum(amounts)
        per_acct_total[acct_id] = t
        totals.append(t)

    total = sum(totals)
    if total <= 0:
        return opp_amounts_by_account

    k_ideal = settings.TOTAL_PIPELINE_TARGET / float(total)

    # Scaling down is always safe wrt TAM.
    if k_ideal < 1.0:
        k_applied = k_ideal
    else:
        k_max = float("inf")
        for acct in accounts:
            acct_id = int(acct["id"])
            acct_total = per_acct_total[acct_id]
            if acct_total <= 0:
                continue
            tam = int(settings.TAM_PER_DEVELOPER * int(acct["numDevelopers"]))
            k_max = min(k_max, tam / float(acct_total))
        k_applied = min(k_ideal, k_max)

    if abs(k_applied - 1.0) < 1e-12:
        return opp_amounts_by_account

    scaled_by_account: dict[int, list[int]] = {}
    for acct in accounts:
        acct_id = int(acct["id"])
        amounts = opp_amounts_by_account.get(acct_id, [])
        if not amounts:
            scaled_by_account[acct_id] = []
            continue

        tam = int(settings.TAM_PER_DEVELOPER * int(acct["numDevelopers"]))
        scaled = [int(round(a * k_applied)) for a in amounts]
        scaled = _enforce_tam_int(scaled, tam)
        scaled_by_account[acct_id] = scaled

    return scaled_by_account


def generate(seed: int | None = None):
    """Generate reps, accounts, opportunities, territories.

    Returns:
        (reps, accounts, opportunities, territories)
        where each is a list[dict].
    """

    seed_used = settings.DEFAULT_SEED if seed is None else int(seed)
    rng = Rng.from_seed(seed_used)

    first_names = read_text_list(settings.FIRST_NAMES_PATH)
    last_names = read_text_list(settings.LAST_NAMES_PATH)
    nouns = read_text_list(settings.ACCOUNT_NOUNS_PATH)
    suffixes = read_text_list(settings.ACCOUNT_SUFFIXES_PATH)
    industries_vocab = read_text_list(settings.INDUSTRIES_PATH)
    stages = read_text_list(settings.STAGES_PATH)

    state_region_raw = read_json(settings.STATES_TO_REGION_JSON_PATH)
    state_to_region = parse_state_region_mapping(state_region_raw)

    region_to_states: dict[str, list[str]] = defaultdict(list)
    for st, rg in state_to_region.items():
        region_to_states[rg].append(st)

    regions = sorted(region_to_states.keys())
    if not regions:
        raise ValueError("No regions found in states/regions JSON")

    # -------------
    # Accounts (core fields; ownership assigned after territories exist)
    # -------------
    accounts: list[dict] = []
    for acct_id in range(1, settings.NUM_ACCOUNTS + 1):
        industry = rng.choice(industries_vocab)
        annual_revenue = _pareto_revenue(rng)
        num_devs = _num_developers(rng, annual_revenue)

        is_customer = rng.random() < settings.IS_CUSTOMER_RATE

        accounts.append(
            {
                "id": acct_id,
                "name": _build_account_name(rng, nouns, suffixes),
                "annualRevenue": int(annual_revenue),
                "numDevelopers": int(num_devs),
                "state": "",  # assigned last
                "industry": industry,
                "isCustomer": bool(is_customer),
                "inPipeline": False,  # derived later
                "repId": 0,
                "territoryId": 0,
            }
        )

    # -------------
    # Territories (industry-based deterministic mapping)
    # -------------
    used_industries = sorted({a["industry"] for a in accounts})
    industry_to_territory_id = {ind: i for i, ind in enumerate(used_industries, start=1)}
    territories: list[dict] = [
        {"id": industry_to_territory_id[ind], "name": f"{ind} Territory"} for ind in used_industries
    ]

    for a in accounts:
        a["territoryId"] = int(industry_to_territory_id[a["industry"]])

    # -------------
    # Reps (territory assigned now; state/region/quota assigned later)
    # -------------
    territory_ids = [t["id"] for t in territories]
    rng.shuffle(territory_ids)
    reps: list[dict] = []
    for rep_id in range(1, settings.NUM_REPS + 1):
        terr_id = territory_ids[(rep_id - 1) % len(territory_ids)]
        reps.append(
            {
                "id": rep_id,
                "name": _build_rep_name(rng, first_names, last_names),
                "homeState": "",  # assigned last
                "region": "",  # assigned last
                "quota": 0,  # assigned after opportunity amounts exist
                "territoryId": int(terr_id),
            }
        )

    reps_by_territory: dict[int, list[dict]] = defaultdict(list)
    for r in reps:
        reps_by_territory[int(r["territoryId"])].append(r)

    # -------------
    # Assign account ownership (repId) within matching territory
    # -------------
    for a in accounts:
        terr_id = int(a["territoryId"])
        choices = reps_by_territory.get(terr_id)
        if not choices:
            raise RuntimeError(f"No reps available for territoryId={terr_id}")
        a["repId"] = int(rng.choice(choices)["id"])

    # -------------
    # Opportunity counts per account, reconciled to exactly NUM_OPPORTUNITIES
    # -------------
    opp_counts = [rng.randint(settings.OPPS_PER_ACCOUNT_MIN, settings.OPPS_PER_ACCOUNT_MAX) for _ in accounts]
    opp_counts = _reconcile_opp_counts(rng, opp_counts, settings.NUM_OPPORTUNITIES)

    # -------------
    # Amount generation with retries to meet global pipeline target range
    # (relationships are fixed at this point; only amounts are regenerated)
    # -------------
    best: dict[int, list[int]] | None = None
    best_dist = float("inf")

    for _attempt in range(settings.AMOUNT_RETRY_LIMIT):
        per_acct_amounts = _generate_amounts_for_accounts(rng, accounts, opp_counts)
        per_acct_amounts = _try_global_scale(accounts, per_acct_amounts)

        total = sum(sum(v) for v in per_acct_amounts.values())
        dist = abs(total - settings.TOTAL_PIPELINE_TARGET)
        if dist < best_dist:
            best_dist = dist
            best = per_acct_amounts

        if settings.TOTAL_PIPELINE_MIN <= total <= settings.TOTAL_PIPELINE_MAX:
            best = per_acct_amounts
            break

    if best is None:
        raise RuntimeError("Failed to generate opportunity amounts")

    total = sum(sum(v) for v in best.values())
    if not (settings.TOTAL_PIPELINE_MIN <= total <= settings.TOTAL_PIPELINE_MAX):
        raise RuntimeError(
            f"Failed to reach total pipeline target range after {settings.AMOUNT_RETRY_LIMIT} retries; total={total}"
        )

    # -------------
    # Build opportunities with consistent account/rep ids
    # -------------
    opportunities: list[dict] = []
    opp_id = 1
    opps_by_account_id: dict[int, list[dict]] = defaultdict(list)

    for acct, n in zip(accounts, opp_counts, strict=True):
        acct_id = int(acct["id"])
        rep_id = int(acct["repId"])
        amounts = list(best.get(acct_id, []))
        if len(amounts) != n:
            raise RuntimeError(f"Internal error: amount count mismatch for account {acct_id}")

        for i in range(n):
            product = rng.choice(settings.PRODUCTS)
            opp = {
                "id": opp_id,
                "name": f"{acct['name']} {product}",
                "amount": int(amounts[i]),
                "stage": rng.choice(stages),
                "closeDate": "",  # assigned after enforcing 10% distribution
                "repId": rep_id,
                "accountId": acct_id,
            }
            opportunities.append(opp)
            opps_by_account_id[acct_id].append(opp)
            opp_id += 1

    # Derived inPipeline
    for a in accounts:
        a["inPipeline"] = bool(opps_by_account_id.get(int(a["id"])))

    # -------------
    # Close dates: exactly 10% recent window; rest future window
    # -------------
    recent_n = int(round(settings.NUM_OPPORTUNITIES * settings.RECENT_CLOSE_PCT))
    if recent_n != int(settings.NUM_OPPORTUNITIES * settings.RECENT_CLOSE_PCT):
        # Keep spec exact for current 100-opportunity config.
        pass

    recent_indices = set(rng.sample(list(range(len(opportunities))), recent_n))
    for idx, o in enumerate(opportunities):
        if idx in recent_indices:
            o["closeDate"] = rng.date_between(settings.RECENT_CLOSE_WINDOW.start, settings.RECENT_CLOSE_WINDOW.end)
        else:
            o["closeDate"] = rng.date_between(settings.FUTURE_CLOSE_WINDOW.start, settings.FUTURE_CLOSE_WINDOW.end)

    # -------------
    # Assign regions/states last and consistently
    # -------------
    territory_id_to_region: dict[int, str] = {}
    for t in territories:
        territory_id_to_region[int(t["id"])] = rng.choice(regions)

    for r in reps:
        terr_id = int(r["territoryId"])
        region = territory_id_to_region[terr_id]
        states_in_region = region_to_states.get(region)
        if not states_in_region:
            raise RuntimeError(f"No states available for region {region}")
        r["region"] = region
        r["homeState"] = rng.choice(states_in_region)

    rep_by_id = {int(r["id"]): r for r in reps}
    for a in accounts:
        rep = rep_by_id[int(a["repId"])]
        a["state"] = rep["homeState"]

    # -------------
    # Quotas last: tie to expected pipeline in territory
    # -------------
    territory_pipeline: dict[int, int] = defaultdict(int)
    for a in accounts:
        terr_id = int(a["territoryId"])
        acct_id = int(a["id"])
        acct_total = sum(int(o["amount"]) for o in opps_by_account_id.get(acct_id, []))
        territory_pipeline[terr_id] += acct_total

    for terr_id, reps_in_terr in reps_by_territory.items():
        terr_total = int(territory_pipeline.get(int(terr_id), 0))
        if not reps_in_terr:
            continue
        per_rep_expected = terr_total / float(len(reps_in_terr))
        for r in reps_in_terr:
            quota = per_rep_expected * float(settings.QUOTA_MULTIPLIER_ON_TERRITORY_PIPELINE)
            r["quota"] = _clamp_int(round(quota), settings.QUOTA_MIN, settings.QUOTA_MAX)

    return reps, accounts, opportunities, territories
