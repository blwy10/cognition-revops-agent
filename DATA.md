# Data model (generator output)

The `generator` package produces a single JSON payload (typically saved as `data.json`) containing synthetic CRM-like data for the app and rules engine.

## Top-level JSON object

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `schema` | string | yes | Fixed identifier: `revops-agent-skeleton`. |
| `generated_at` | string (ISO-8601 datetime) | yes | Timestamp of generation (UTC offset included). |
| `reps` | array of `Rep` | yes | Sales reps (owners). |
| `accounts` | array of `Account` | yes | Customer/prospect accounts. |
| `opportunities` | array of `Opportunity` | yes | Pipeline opportunities tied to accounts and reps. |
| `territories` | array of `Territory` | yes | Territories derived from industries. |
| `opportunity_history` | array of `OpportunityHistoryEvent` | yes | Field-change events for opportunities (stage and close date changes). |

## Entity schemas

### `Rep`

| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| `id` | integer | yes | Unique rep id (1..`NUM_REPS`). |
| `name` | string | yes | Unique name (duplicates disambiguated with ` (n)`). |
| `homeState` | string | yes | A state name selected from the rep’s region. |
| `region` | string | yes | Region name derived from the states/regions mapping. |
| `quota` | integer | yes | Derived from territory pipeline; clamped to `[QUOTA_MIN, QUOTA_MAX]`. |
| `territoryId` | integer | yes | Foreign key to `Territory.id`. |

### `Account`

| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| `id` | integer | yes | Unique account id (1..`NUM_ACCOUNTS`). |
| `name` | string | yes | Unique name (duplicates disambiguated with ` (n)`). |
| `annualRevenue` | integer | yes | Dollars/year (Pareto-distributed, capped). |
| `numDevelopers` | integer | yes | Positive integer derived from `annualRevenue`. |
| `state` | string | yes | Set to the owning rep’s `homeState`. |
| `industry` | string | yes | Industry label from vocab. |
| `isCustomer` | boolean | yes | Random by `IS_CUSTOMER_RATE`. |
| `inPipeline` | boolean | yes | Derived: `true` if the account has >=1 opportunity. |
| `repId` | integer | yes | Foreign key to `Rep.id` (owner). |
| `territoryId` | integer | yes | Foreign key to `Territory.id` (derived from `industry`). |

### `Territory`

| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| `id` | integer | yes | Unique territory id. |
| `name` | string | yes | Format: `<industry> Territory` (unique). |

### `Opportunity`

| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| `id` | integer | yes | Unique opportunity id (1..`NUM_OPPORTUNITIES`). |
| `name` | string | yes | Unique name based on account + product (duplicates disambiguated with ` (n)`). |
| `amount` | integer | yes | Dollar amount; generated per-account under TAM constraints and globally scaled to meet pipeline target range. |
| `stage` | string | yes | Stage label from stages vocab (string-ordered). |
| `closeDate` | string (YYYY-MM-DD) or null | yes | Date; distribution: `RECENT_CLOSE_PCT` recent, `MISSING_CLOSE_PCT` null, remainder future. |
| `repId` | integer | yes | Foreign key to `Rep.id`. |
| `accountId` | integer | yes | Foreign key to `Account.id`. |
| `created_date` | string (YYYY-MM-DD) | yes | Date within `OPPORTUNITY_CREATED_WINDOW`. Guaranteed `<= 2026-02-18` per generator constraints. |

### `OpportunityHistoryEvent`

Represents a single field change event for an opportunity.

| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| `id` | integer | yes | Unique history event id (monotonic in-generation). |
| `opportunity_id` | integer | yes | Foreign key to `Opportunity.id`. |
| `field_name` | string | yes | One of: `stage`, `closeDate`. |
| `old_value` | string or null | yes | Prior value for the field. For `closeDate`, may be null. |
| `new_value` | string | yes | New value for the field. For `closeDate`, always a YYYY-MM-DD string. |
| `change_date` | string (YYYY-MM-DD) | yes | When the change happened (within `OPPORTUNITY_HISTORY_CHANGE_WINDOW`). |

## Relationships and invariants

- **Ownership**
  - `Account.repId` and `Opportunity.repId` reference `Rep.id`.
  - An opportunity’s `repId` is always the owning rep of its account at generation time.

- **Territories**
  - Territories are derived from the set of industries present in the generated accounts.
  - `Account.territoryId` is deterministically mapped from `Account.industry`.
  - `Rep.territoryId` is assigned by shuffling territory ids and distributing reps across them.
  - Account ownership is assigned to a rep within the same territory.

- **Geography**
  - Each territory is assigned a `region` (random) and reps in that territory inherit it.
  - `Rep.homeState` is chosen from the states belonging to its region.
  - `Account.state` is set to the owning rep’s `homeState`.

- **Dates**
  - `Opportunity.created_date` is always present.
  - Generator enforces that `Opportunity.closeDate` (if present) and any `OpportunityHistoryEvent.change_date` / `closeDate` old/new values are not earlier than `created_date`.

- **Uniqueness**
  - `name` fields for reps/accounts/opportunities/territories are made unique by suffixing ` (n)` when collisions occur.

## Counts and configurability

The generator’s default counts are controlled in `generator/settings.py`:

- `NUM_REPS` (default 30)
- `NUM_ACCOUNTS` (default 70)
- `NUM_OPPORTUNITIES` (default 100)

The output schema shape stays the same when these values change; only cardinalities and distributions vary.

## Minimal example (shape only)

```json
{
  "schema": "revops-agent-skeleton",
  "generated_at": "2026-02-19T05:00:09.013131+00:00",
  "reps": [{"id": 1, "name": "…", "homeState": "…", "region": "…", "quota": 200000, "territoryId": 8}],
  "accounts": [{"id": 1, "name": "…", "annualRevenue": 102413848, "numDevelopers": 22, "state": "…", "industry": "…", "isCustomer": false, "inPipeline": true, "repId": 19, "territoryId": 7}],
  "opportunities": [{"id": 1, "name": "…", "amount": 6184, "stage": "…", "closeDate": "2026-07-06", "repId": 19, "accountId": 1, "created_date": "2024-10-22"}],
  "territories": [{"id": 7, "name": "Natural Resources and Mining Territory"}],
  "opportunity_history": [{"id": 1, "opportunity_id": 1, "field_name": "closeDate", "old_value": "2026-07-06", "new_value": "2026-08-28", "change_date": "2025-11-18"}]
}
```
