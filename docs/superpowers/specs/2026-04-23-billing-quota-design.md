# Billing & Token Quota System — Design Spec
_Date: 2026-04-23_

## Context

Hexal-LM needs per-user token quota tracking with rolling carryover and hard daily caps. Users are billed based on output tokens weighted by model. No new infra — DB-only (fits existing SQLAlchemy async + Supabase Postgres stack).

---

## Requirements

- 100 base tokens per user per day
- Unused tokens roll over at 50% to next day
- Rollover window: 3 days; resets on day 4
- Hard cap: max 150% of daily_base in any single day
- Mid-generation: complete even if quota exceeded, deduct after
- Block new requests (429) when daily_used >= available
- Billing = output tokens × model weight × global cost rate
- All rates/weights configurable via env vars

---

## Architecture

### Option chosen: DB-only quota table (Option A)

Fits existing stack. No new dependencies. 1 row per user. Lazy daily reset (on first request of new day — no cron). 2 DB hits per request (check + deduct). Survives restarts, scales horizontally.

---

## Data Model

### New table: `user_quota`

```sql
user_id           UUID PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE
daily_used        INTEGER NOT NULL DEFAULT 0
rollover_balance  INTEGER NOT NULL DEFAULT 0
window_start_date DATE NOT NULL
timezone          VARCHAR(64) NOT NULL DEFAULT 'UTC'
updated_at        TIMESTAMPTZ NOT NULL DEFAULT now()
```

- One row per user (upserted on first use)
- `window_start_date` = date of day 1 of current 3-day window
- `daily_used` resets to 0 at start of each new day (lazy, on first request)
- `rollover_balance` zeroed on day 4 of window

---

## Config

### `app/billing/config.py`

All values read from env with these defaults:

```python
DAILY_BASE_TOKENS: int = 100
ROLLOVER_RATE: float = 0.5
ROLLOVER_WINDOW_DAYS: int = 3
HARD_CAP_MULTIPLIER: float = 1.5
GLOBAL_COST_RATE: float = 0.05   # cost % per 100 output tokens

MODEL_WEIGHTS: dict[str, float] = {
    "Apex":    2.0,
    "Pulse":   2.0,
    "Swift":   1.0,
    "Prism":   1.5,
    "Depth":   1.5,
    "Atlas":   1.0,
    "Horizon": 1.5,
}
```

---

## QuotaService (`app/billing/quota.py`)

### Key formulas

```python
available = min(
    DAILY_BASE_TOKENS + rollover_balance,
    DAILY_BASE_TOKENS * HARD_CAP_MULTIPLIER  # cap at 150
)

weighted_tokens = tokens_out * MODEL_WEIGHTS.get(model, 1.0)

# End of day rollover update
leftover = max(available - daily_used, 0)
new_rollover = int(leftover * ROLLOVER_RATE)

# Day 4 window reset
if (today - window_start_date).days >= ROLLOVER_WINDOW_DAYS:
    rollover_balance = 0
    window_start_date = today
```

### Methods

| Method | Behavior |
|--------|----------|
| `get_or_create(db, user_id, tz)` | Fetch row; lazy-reset daily_used if new day; zero rollover if day 4+ |
| `available(quota)` | `min(base + rollover, base * cap_mult)` |
| `check(quota)` | Raise `QuotaExceededError` (→ 429) if `daily_used >= available` |
| `deduct(db, quota, tokens_out, model)` | Add weighted tokens to `daily_used`; update `rollover_balance`; flush |

### Lazy daily reset logic

On `get_or_create`, if `today > last_updated date`:
1. Compute rollover: `new_rollover = int(max(available - daily_used, 0) * ROLLOVER_RATE)`
2. Check window: if `(today - window_start_date).days >= ROLLOVER_WINDOW_DAYS` → zero rollover, reset window
3. Set `daily_used = 0`, `rollover_balance = new_rollover`, `updated_at = now()`

---

## Integration: `app/api/query.py`

Two injection points:

```python
# 1. BEFORE stream — check quota
quota = await QuotaService.get_or_create(db, user.id, user_tz)
QuotaService.check(quota)  # raises 429 if exceeded

# 2. AFTER stream — deduct (in finally block)
await QuotaService.deduct(db, quota, tokens_out=total_tokens, model=primary_model)
```

`tokens_out` sourced from `_TokenCarry.total_tokens` already accumulated in all modes (Oracle, Council, Relay, Workflow). For Council (multi-model), deduct separately per model after each hex completes.

---

## New files

| File | Purpose |
|------|---------|
| `app/billing/__init__.py` | Package |
| `app/billing/config.py` | All rates/weights/caps |
| `app/billing/quota.py` | `QuotaService`, `QuotaExceededError`, `UserQuota` SQLAlchemy model |
| `alembic/versions/0003_user_quota.py` | Migration: create `user_quota` table |

## Modified files

| File | Change |
|------|--------|
| `app/api/query.py` | Add quota check before stream, deduct after |
| `app/db/models/__init__.py` | Export `UserQuota` |
| `.env.example` | Document new billing env vars |

---

## Error response

```json
HTTP 429
{"detail": "daily quota exceeded", "available": 0, "resets_at": "2026-04-24T00:00:00Z"}
```

---

## Testing

- `tests/test_billing_quota.py` — unit tests for `QuotaService` (mock DB session via existing `FakeSession` pattern)
- Test cases: fresh user, rollover calculation, day-4 reset, hard cap enforcement, 429 on exceeded, deduct after stream, Council multi-model deduct
- No live API tests needed for quota logic

---

## Out of scope

- Frontend quota display
- Admin quota override
- Per-session breakdown
- Stripe/payment integration
