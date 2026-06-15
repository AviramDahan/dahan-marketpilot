# Phase 14: Data Sync & Dashboard Integration — Context

**Gathered:** 2026-06-16
**Status:** Ready for planning

<domain>
## Phase Boundary

Phase 14 delivers reliable portfolio state synchronization from QuantConnect Cloud and freshness-aware display on the existing Streamlit dashboard. It creates a sync module that polls QC, persists snapshots, evaluates freshness, and extends the dashboard Portfolio page with live data.

Phase 14 must NOT: deploy algorithms, deliver signals, place orders, schedule anything autonomously, or introduce a new database. Those belong to Phases 15-17.
</domain>

<decisions>
## Implementation Decisions

### Sync Storage

- **D-01:** Synced portfolio state persists as append-only JSONL at `data/portfolio_sync.jsonl`. Each poll appends one JSON line with the full `QuantConnectPaperSnapshot` plus metadata (timestamp, generation counter, sync_status).
- **D-02:** Dashboard reads the last line of the JSONL file to get latest state. This is the only read pattern needed (no querying historical records for display).
- **D-03:** Historical records in the JSONL serve debugging/audit purposes. Optional daily/weekly rotation is out of scope for this phase but the format supports it.
- **D-04:** Atomic writes use temp-file-then-rename pattern to prevent partial lines from corrupting the JSONL on crash (SYNC-05).
- **D-05:** Each record carries a monotonic generation counter. If the dashboard reads a record with a lower generation than expected, it treats the data as potentially corrupt and shows ERROR state (SYNC-05).

### Polling & Triggering

- **D-06:** The sync module is a callable function (not a daemon). It performs one sync cycle: poll QC → reconcile → persist → return status. Phase 16 (Production Scheduler) will invoke it on the NYSE market schedule.
- **D-07:** For Phase 14 testing and manual use, a CLI entrypoint (`python -m marketpilot.sync`) triggers a single sync cycle. No loop, no timer.
- **D-08:** Polling cadence target is ~5 minutes during market hours (DASH-01). The sync module itself does not enforce timing — the caller (scheduler in Phase 16) is responsible.

### Freshness & Staleness

- **D-09:** Three freshness states replace the current single-threshold model:
  - **FRESH:** age ≤ 10 minutes (green)
  - **STALE:** 10 min < age ≤ 30 minutes (yellow warning, DASH-02)
  - **ERROR:** age > 30 minutes (red, strong stale state, DASH-03)
- **D-10:** Freshness is calculated from `source_timestamp` (when QC produced the data) relative to current wall-clock time. Not from when we last polled.
- **D-11:** All timestamps stored as UTC internally (SAFE-04). Convert to ET only at display boundaries in the dashboard.

### Dashboard Display

- **D-12:** Extend the existing Portfolio page (not a new page). Add sections at the top for sync/live data from QC.
- **D-13:** Display elements (top to bottom):
  1. **Freshness banner** — color-coded (green/yellow/red) with `last_sync_time` and `source_timestamp` in ET
  2. **Portfolio summary metrics** — Cash, Equity, Unrealized P&L as metric cards
  3. **Holdings table** — symbol, quantity, avg_price, market_price, P&L%
  4. **Sync status section** — last poll time, next expected poll (if scheduler running), error count
- **D-14:** If no sync data exists yet (first run, empty JSONL), dashboard shows informational "No sync data available" message — never fabricates data (DASH-04).
- **D-15:** QC is explicitly labeled as authoritative source in the dashboard UI (DASH-04).

### Reconciliation Integration

- **D-16:** Each sync cycle runs `reconcile_quantconnect_state()` after polling QC. If mismatches exceed threshold, fire `SYNC_DISCREPANCY` alert through existing Telegram pipeline (SYNC-03).
- **D-17:** Reconciliation detects but never auto-corrects (SYNC-04). The alert includes mismatch details for human review.
- **D-18:** Discrepancy threshold: any mismatch in ORDER_ID, ORDER_STATE, or FILL_DATA triggers alert. CASH/HOLDINGS mismatches trigger alert only if delta > 1% of portfolio equity.

### Prior Decisions Carried Forward

- **D-19:** QC is authoritative for all portfolio state — local records are audit mirrors only (Phase 8/13 D-11).
- **D-20:** All existing tests (454) must pass unchanged; new modules use lazy imports (SAFE-03 / Phase 13 D-12).
- **D-21:** `PAPER_TRADING_ONLY` enforcement continues — sync module validates the constant on initialization (SAFE-01).
</decisions>

<code_context>
## Reusable Codebase Assets

- `marketpilot/qc_api.py` — `QCApiClient.read_live_algorithm()` returns `QuantConnectPaperSnapshot`; `read_live_orders()` returns order tuples
- `marketpilot/quantconnect_paper.py` — All dataclasses: `QuantConnectPaperSnapshot`, `QuantConnectHolding`, `QuantConnectPaperOrder`, `QuantConnectPaperFill`, `QuantConnectPaperPerformance`, status enums
- `marketpilot/reconciliation.py` — `reconcile_quantconnect_state()` → `ReconciliationDecision` with mismatch detection
- `marketpilot/dashboard_export.py` — `DashboardExportPayload`, `ObjectStoreSourceLoader` with freshness evaluation (needs threshold update from 1→3 states), `DashboardSourceMetadata`
- `marketpilot/notification_events.py` — Existing Telegram alert pipeline for system incidents
- `marketpilot/constants.py` — `PAPER_TRADING_ONLY = True`
- `data/` directory — existing pattern for JSONL audit files
</code_context>

<canonical_refs>
## Canonical References

- `.planning/REQUIREMENTS.md` — Requirements SYNC-01..06, DASH-01..05, SAFE-04
- `.planning/phases/13-qc-api-client-and-safety-foundation/13-CONTEXT.md` — QC API client decisions, credential management
- `marketpilot/qc_api.py` — API client interface (read_live_algorithm, read_live_orders)
- `marketpilot/reconciliation.py` — Reconciliation logic and mismatch types
- `marketpilot/dashboard_export.py` — Freshness evaluation patterns (needs 3-state upgrade)
- `marketpilot/quantconnect_paper.py` — Dataclass contracts for portfolio state
</canonical_refs>

<deferred>
## Deferred Ideas

- Historical sync analytics (trend of equity over time from JSONL history) — future phase
- JSONL rotation/compaction policy — operational concern for later
- WebSocket streaming from QC (explicitly Out of Scope — REST polling sufficient for swing trading)
</deferred>
