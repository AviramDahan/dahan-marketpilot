# AI Handoff: VSCode GitHub Copilot + Claude Code Opus Agent Mode

SIMULATED PAPER TRADING ONLY - NOT FINANCIAL ADVICE

This handoff is for continuing Dahan MarketPilot from a fresh GitHub clone in
VSCode GitHub Copilot agent mode using Claude Code Opus.

## Repository

- GitHub: `https://github.com/AviramDahan/dahan-marketpilot.git`
- Default branch: `master`
- Project root after clone: `dahan-marketpilot`
- Current milestone: `v1.0`
- Current GSD phase: `10.1`
- Current stop point: Phase `10.1-03` completed; next work is Phase `10.1-04`.

## Current State

Phase `10.1` was inserted by milestone audit to close the runtime integration
gap from strategy evidence to paper-trading runtime, Telegram notifications,
and dashboard state.

Completed in Phase `10.1`:

- `10.1-01`: Runtime contracts and setup registry.
- `10.1-02`: Pure runtime pipeline composition.
- `10.1-03`: Safe LEAN bridge and thin `lean/main.py` runtime adapter.

Remaining in Phase `10.1`:

- `10.1-04`: Dashboard export producer and read-only Object Store/API-style
  dashboard source loader.
- `10.1-05`: Runtime notification emission, docs, UAT, and verification.

The next GSD command should be:

```text
/gsd-execute-phase 10.1 --wave 4
```

If the receiving environment cannot run the GSD slash command directly, execute
the plan manually from:

```text
.planning/phases/10.1-close-gap-runtime-orchestrator-for-strategy-to-paper-e2e-flo/10.1-04-PLAN.md
```

After `10.1-04` completes, the next command is:

```text
/gsd-execute-phase 10.1 --wave 5
```

## Critical Project Rules

- The project is simulated Paper Trading only.
- Do not add real-money trading support.
- Do not add broker setup, live-money execution, leverage, margin, shorting,
  options, futures, crypto, Forex, or dashboard order-entry controls.
- QuantConnect remains the authority for Paper portfolio/backtest state.
- Render/dashboard is read-only and must never become an authority or mutation
  surface.
- Telegram is notification-only; delivery success or failure must never control
  trading, exits, reconciliation, recovery, or safety logic.
- External QuantConnect/Render checks must remain `not_run` unless actually run.
- Never commit secrets, tokens, passwords, account credentials, API keys, or chat
  IDs.

## Recommended Agent Prompt

Use this prompt in VSCode GitHub Copilot agent mode:

```text
You are continuing the Dahan MarketPilot project from a fresh clone.

Repository: https://github.com/AviramDahan/dahan-marketpilot.git
Branch: master

SIMULATED PAPER TRADING ONLY - NOT FINANCIAL ADVICE.

Read these files before editing:
- README.md
- AGENTS.md
- docs/AI-HANDOFF-COPILOT-CLAUDE.md
- .planning/STATE.md
- .planning/ROADMAP.md
- .planning/REQUIREMENTS.md
- .planning/phases/10.1-close-gap-runtime-orchestrator-for-strategy-to-paper-e2e-flo/CONTEXT.md
- .planning/phases/10.1-close-gap-runtime-orchestrator-for-strategy-to-paper-e2e-flo/10.1-04-PLAN.md
- .planning/phases/10.1-close-gap-runtime-orchestrator-for-strategy-to-paper-e2e-flo/10.1-01-SUMMARY.md
- .planning/phases/10.1-close-gap-runtime-orchestrator-for-strategy-to-paper-e2e-flo/10.1-02-SUMMARY.md
- .planning/phases/10.1-close-gap-runtime-orchestrator-for-strategy-to-paper-e2e-flo/10.1-03-SUMMARY.md

Continue the GSD workflow from Phase 10.1 Wave 4 only:
/gsd-execute-phase 10.1 --wave 4

If slash commands are unavailable, manually execute:
.planning/phases/10.1-close-gap-runtime-orchestrator-for-strategy-to-paper-e2e-flo/10.1-04-PLAN.md

Scope for this step:
- Add dashboard export producer shape and read-only Object Store/API-style source loader.
- Preserve QuantConnect authority and dashboard read-only behavior.
- Keep external QuantConnect/Object Store/API execution marked not_run unless actually executed.
- Do not store, print, or commit secrets.
- Do not add real-money, live broker, leverage, margin, shorting, or dashboard order controls.
- Commit atomically and update GSD documentation/state after tests pass.

Expected verification for 10.1-04:
- python -m pytest tests/test_dashboard_object_store_source.py tests/test_dashboard_runtime_source.py tests/test_dashboard_data_contracts.py tests/test_dashboard_read_only.py -q
- python -m pytest tests/test_dashboard_pages.py tests/test_dashboard_secret_masking.py tests/test_dashboard_render_config.py -q

When 10.1-04 is complete, create:
.planning/phases/10.1-close-gap-runtime-orchestrator-for-strategy-to-paper-e2e-flo/10.1-04-SUMMARY.md

Then continue with:
/gsd-execute-phase 10.1 --wave 5

Do not mark Phase 10.1 complete until 10.1-05 creates UAT and VERIFICATION
artifacts and the required full verification passes.
```

## Local Setup Commands

From a clean machine or folder:

```powershell
git clone https://github.com/AviramDahan/dahan-marketpilot.git
cd dahan-marketpilot
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements-dev.txt
python -m pytest tests/test_runtime_contract.py tests/test_runtime_orchestrator.py tests/test_lean_runtime_bridge_static.py -q
```

If the project is run with Python 3.10, most local tests have worked during
development, but release validation should use the Python version declared in
`pyproject.toml`.

## Phase 10.1 Wave 4 Files

Expected write scope for the next step:

- `marketpilot/dashboard_export.py`
- `marketpilot/lean_bridge.py`
- `marketpilot/runtime_orchestrator.py`
- `dashboard/config.py`
- `dashboard/data.py`
- `config/dashboard.yaml`
- `tests/test_dashboard_object_store_source.py`
- `docs/dashboard.md`
- `docs/render_dashboard.md`
- `.planning/phases/10.1-close-gap-runtime-orchestrator-for-strategy-to-paper-e2e-flo/10.1-04-SUMMARY.md`

## Phase 10.1 Wave 5 Files

Expected write scope after Wave 4:

- `marketpilot/runtime_orchestrator.py`
- `marketpilot/notification_events.py`
- `docs/operations.md`
- `docs/testing.md`
- `docs/release.md`
- `.planning/REQUIREMENTS.md`
- `.planning/ROADMAP.md`
- `.planning/STATE.md`
- `.planning/phases/10.1-close-gap-runtime-orchestrator-for-strategy-to-paper-e2e-flo/10.1-UAT.md`
- `.planning/phases/10.1-close-gap-runtime-orchestrator-for-strategy-to-paper-e2e-flo/10.1-VERIFICATION.md`
- `tests/test_runtime_notification_emission.py`

## Before Marking Complete

Run at minimum:

```powershell
python -m pytest -q
git status --short --branch
```

Run a secret scan before pushing. The scan must not reveal any real secret
values in tracked files.

After Phase `10.1` passes verification, rerun the milestone audit workflow and
only then archive/complete the milestone.
