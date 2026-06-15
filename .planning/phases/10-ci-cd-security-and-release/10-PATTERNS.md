# Phase 10: CI/CD, Security and Release - Pattern Map

**Mapped:** 2026-06-15
**Files analyzed:** 12 target new/modified areas
**Analogs found:** 11 / 12

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|-------------------|------|-----------|----------------|---------------|
| `.github/workflows/tests.yml` | config | batch | `pyproject.toml`, `docs/testing.md` | partial |
| `.github/workflows/quantconnect.yml` | config | batch | `docs/quantconnect_verification.md`, `lean/README.md`, `tests/test_quantconnect_verification_docs.py` | partial |
| `.github/workflows/weekly-validation.yml` | config | batch | `tests/test_activation_gates.py`, `tests/test_backtest_artifact_safety.py` | role-match |
| `.github/workflows/dashboard-health.yml` | config | request-response | `render.yaml`, `tests/test_dashboard_render_config.py`, `docs/render_dashboard.md` | role-match |
| `scripts/*.py` CI/operator helpers | utility | batch | `scripts/telegram_smoke.py` | exact |
| `tests/test_ci_workflows.py` | test | batch | `tests/test_dashboard_render_config.py`, `tests/test_project_files.py` | role-match |
| `tests/test_security_release_gates.py` | test | transform | `tests/test_safety.py`, `tests/test_dashboard_read_only.py`, `tests/test_paper_trading_safety.py` | exact |
| `tests/test_release_audit.py` | test | transform | `tests/test_backtest_artifact_safety.py`, `tests/test_project_files.py` | exact |
| `docs/operations.md` | documentation | batch | `docs/render_dashboard.md`, `docs/setup.md`, `docs/testing.md` | role-match |
| `docs/troubleshooting.md` | documentation | request-response | `docs/recovery.md`, `docs/render_dashboard.md` | role-match |
| `docs/release.md` or `docs/handoff.md` | documentation | transform | `.planning/phases/09-render-dashboard/09-07-SUMMARY.md`, `docs/AI-COLLABORATION.md` | role-match |
| `SECURITY_REVIEW.md` / release audit artifact | documentation | transform | `docs/safety.md`, `docs/licensing.md`, `docs/AI-COLLABORATION.md` | role-match |

## Pattern Assignments

### `.github/workflows/tests.yml` (config, batch)

**Analog:** `pyproject.toml` + `docs/testing.md`

**Project/test config pattern** (`pyproject.toml` lines 5-28):
```toml
[project]
name = "dahan-marketpilot"
version = "0.1.0"
requires-python = ">=3.11"

[tool.pytest.ini_options]
testpaths = ["tests"]
pythonpath = ["."]
addopts = "-q"
```

**Offline test command pattern** (`docs/testing.md` lines 5-18):
```markdown
Run the local suite with:

```powershell
python -m pytest
```

Tests must not require:
- Internet access.
- QuantConnect credentials.
- Telegram credentials.
- Render credentials.
- Broker credentials.
- Real market data.
```

**Use for Phase 10:** The main CI workflow should install Python 3.11, install `requirements-dev.txt`, and run `python -m pytest`. Do not require external services or secrets in the deterministic test job.

---

### `.github/workflows/quantconnect.yml` (config, batch)

**Analog:** `docs/setup.md` + `tests/test_quantconnect_verification_docs.py`

**External LEAN prerequisite pattern** (`docs/setup.md` lines 26-43):
```markdown
QuantConnect verification contracts are documented in
`docs/quantconnect_verification.md`.

External LEAN verification may require Docker, the LEAN CLI, `lean login`,
`lean init`, and QuantConnect organization access. These are user setup actions.
Keep credentials outside the repository and outside chat.

When prerequisites are available, the external compile check is:

```powershell
lean build
```

Run it only from a properly initialized LEAN workspace. If prerequisites are
missing, record the check as not run.
```

**Docs guard test pattern** (`tests/test_quantconnect_verification_docs.py` lines 18-34):
```python
def test_quantconnect_verification_doc_enforces_no_credentials_or_cloud_runs():
    text = VERIFICATION_DOC.read_text(encoding="utf-8")

    assert "does not require or authorize" in text
    assert "Repository-stored credentials" in text
    assert "Cloud backtest execution" in text
    assert "Paper Trading deployment" in text
    assert "Live deployment" in text
```

**Use for Phase 10:** QuantConnect sync/cloud-backtest workflow should be manually dispatched or scheduled with explicit `if:` guards around secret availability. Missing secrets must produce a documented `not_run`/skipped state, not fake pass claims.

---

### `.github/workflows/dashboard-health.yml` (config, request-response)

**Analog:** `render.yaml`, `tests/test_dashboard_render_config.py`, `docs/render_dashboard.md`

**Render YAML convention** (`render.yaml` lines 1-29):
```yaml
services:
  - type: web
    name: dahan-marketpilot-dashboard
    runtime: python
    buildCommand: pip install -r requirements.txt
    startCommand: streamlit run dashboard/app.py --server.address=0.0.0.0 --server.port=$PORT
    healthCheckPath: /
    envVars:
      - key: DASHBOARD_PASSWORD
        sync: false
      - key: QUANTCONNECT_API_TOKEN
        sync: false
```

**Secret reference test pattern** (`tests/test_dashboard_render_config.py` lines 36-44):
```python
def test_render_blueprint_uses_python_311_and_secret_references_only():
    service = _render_service()
    env_vars = {item["key"]: item for item in service["envVars"]}

    assert env_vars["PYTHON_VERSION"]["value"].startswith("3.11.")
    for name in SECRET_ENV_NAMES:
        assert name in env_vars
        assert env_vars[name]["sync"] is False
        assert "value" not in env_vars[name]
```

**Use for Phase 10:** Health workflow should verify the Render/dashboard surface without storing secrets in YAML. Prefer endpoint/status checks that can be skipped when the dashboard URL secret is absent.

---

### `scripts/*.py` CI/operator helpers (utility, batch)

**Analog:** `scripts/telegram_smoke.py`

**Operator-run script pattern** (lines 1-15):
```python
"""Send a safe Telegram smoke-test alert using local environment secrets.

This script is operator-run only. It loads `.env.local` if present, reads the
configured Telegram env vars, and sends a paper-only test message through the
same delivery boundary used by the application.
"""

from __future__ import annotations

import os
from pathlib import Path
```

**Secret loading and missing-secret output pattern** (lines 20-31, 52-61):
```python
def _load_env_file(path: Path) -> None:
    if not path.exists():
        return
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        if key and key not in os.environ:
            os.environ[key] = value

if config.missing_secret_names:
    print("Missing required Telegram secret environment variables:")
    for name in config.missing_secret_names:
        print(f"- {name}")
    return 2
```

**Use for Phase 10:** CI helper scripts should be explicit operator/CI tools, return nonzero for missing required inputs only when that job requires them, and print secret names but never values.

---

### `tests/test_ci_workflows.py` (test, batch)

**Analog:** `tests/test_dashboard_render_config.py`

**YAML parse pattern** (lines 1-22):
```python
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]

def _render_service() -> dict[str, object]:
    loaded = yaml.safe_load((ROOT / "render.yaml").read_text(encoding="utf-8"))
    services = loaded["services"]
    assert len(services) == 1
    return services[0]
```

**Dependency guard pattern** (lines 47-58):
```python
def test_runtime_dependencies_are_limited_to_approved_packages():
    requirements = (ROOT / "requirements.txt").read_text(encoding="utf-8")
    pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")

    assert "PyYAML>=6.0.2" in requirements
    assert "streamlit>=1.51,<2" in pyproject
    assert "requests" not in pyproject
    assert "httpx" not in pyproject
```

**Use for Phase 10:** Parse workflow YAML with `yaml.safe_load`, assert jobs use Python 3.11, deterministic test job runs pytest, and workflow files do not contain literal secret values or unsafe commands.

---

### `tests/test_security_release_gates.py` (test, transform)

**Analog:** `tests/test_safety.py`, `tests/test_dashboard_read_only.py`, `tests/test_paper_trading_safety.py`

**Central safety guard pattern** (`tests/test_safety.py` lines 7-33):
```python
def test_central_paper_trading_guard_is_true():
    assert PAPER_TRADING_ONLY is True

@pytest.mark.parametrize("key", [
    "real_broker_enabled",
    "live_money_enabled",
    "leverage_allowed",
    "margin_allowed",
    "short_selling_allowed",
    "options_allowed",
    "futures_allowed",
    "cryptocurrency_allowed",
    "forex_allowed",
    "manual_order_controls_enabled",
])
def test_unsafe_feature_classes_fail(key):
    with pytest.raises(SafetyValidationError):
        validate_safety_config({"paper_trading_only": True, key: True})
```

**Read-only dashboard scan pattern** (`tests/test_dashboard_read_only.py` lines 14-28, 74-92):
```python
FORBIDDEN_CONTROL_TERMS = [
    "submit order",
    "buy button",
    "sell button",
    "cancel button",
    "modify button",
    "manual trade entry",
    "telegram send",
    "paper mode switch",
    "recovery approval",
    "quantconnect mutation",
]

for forbidden in FORBIDDEN_CONTROL_TERMS:
    assert forbidden not in combined
```

**Paper deployment safety pattern** (`tests/test_paper_trading_safety.py` lines 22-37):
```python
def test_quantconnect_paper_module_never_executes_deployment_commands():
    text = (ROOT / "marketpilot" / "quantconnect_paper.py").read_text(encoding="utf-8")

    assert "subprocess" not in text
    assert "os.system" not in text
    assert ".run(" not in text
    assert "Popen" not in text
```

**Use for Phase 10:** Security/release gate tests should aggregate forbidden real-money, broker, dashboard mutation, subprocess deployment, and secret-exposure scans across workflows, scripts, docs, and source.

---

### `tests/test_release_audit.py` (test, transform)

**Analog:** `tests/test_backtest_artifact_safety.py`, `tests/test_project_files.py`

**Required file/disclaimer pattern** (`tests/test_project_files.py` lines 11-39):
```python
def test_required_foundation_files_exist():
    required = [
        "LICENSE",
        "NOTICE",
        "THIRD_PARTY_NOTICES.md",
        "DISCLAIMER.md",
        "README.md",
        "docs/safety.md",
        "docs/setup.md",
        "docs/configuration.md",
        "docs/testing.md",
        "docs/licensing.md",
    ]
    missing = [path for path in required if not (ROOT / path).is_file()]
    assert missing == []

def test_disclaimer_and_paper_guard_remain_visible():
    expected = "SIMULATED PAPER TRADING ONLY - NOT FINANCIAL ADVICE"
    assert expected in read("DISCLAIMER.md")
    assert expected in read("README.md")
```

**Artifact source and no-delivery pattern** (`tests/test_backtest_artifact_safety.py` lines 9-28):
```python
def test_supported_artifact_labels_are_explicit():
    assert {source.value for source in ArtifactSource} == {
        "real_quantconnect",
        "fixture",
        "schema",
        "example",
        "not_run",
    }

def test_backtest_artifact_code_has_no_external_delivery_or_order_submission():
    forbidden = ["submit_order", "market_order", "telegram", "brokerage", "api_key", "password"]
    assert not any(token in combined for token in forbidden)
```

**Use for Phase 10:** Final audit tests should assert release docs exist, safety phrase is visible, fake performance artifacts are absent, and generated/report artifacts use explicit source labels.

---

### `docs/operations.md` (documentation, batch)

**Analog:** `docs/render_dashboard.md`, `docs/setup.md`, `docs/testing.md`

**Render operations pattern** (`docs/render_dashboard.md` lines 19-30, 44-58):
```markdown
`render.yaml` defines one Python Web Service:

- Build command: `pip install -r requirements.txt`
- Start command: `streamlit run dashboard/app.py --server.address=0.0.0.0 --server.port=$PORT`
- Python version: `3.11.9`
- Health path: `/`

Set these values in Render as environment variables or Blueprint prompts. Store
real values only in Render or another approved external secret store:

- `DASHBOARD_PASSWORD`
- `QUANTCONNECT_USER_ID`
- `QUANTCONNECT_API_TOKEN`
```

**Use for Phase 10:** Operations docs should list exact commands, schedules, secret names, expected skipped states, and external user actions. Do not include real credential values.

---

### `docs/troubleshooting.md` (documentation, request-response)

**Analog:** `docs/recovery.md`, `docs/render_dashboard.md`

**Recovery authority pattern** (`docs/recovery.md` lines 1-5):
```markdown
# Recovery

Phase 6 restart recovery is modeled as a comparison between local audit mirror
state and a future QuantConnect snapshot. When they disagree, QuantConnect wins,
local state is marked mismatched, and a recovery event is emitted.
```

**Stale/error display pattern** (`docs/render_dashboard.md` lines 32-42):
```markdown
The dashboard cache is display-only. Cache TTL is 60 seconds. Stale warning
appears around 10 minutes, and a strong stale/error state appears around
30 minutes. Render cold starts or failed source reads must show source/cache
timestamps and stale/error labels when last-good display cache exists, or safe
`not_available`/`error` states when no cache exists.
```

**Use for Phase 10:** Troubleshooting should be symptom -> likely cause -> safe operator action. It must preserve QuantConnect authority, Render read-only status, and explicit recovery before resuming entries.

---

### `docs/release.md` or `docs/handoff.md` (documentation, transform)

**Analog:** `.planning/phases/09-render-dashboard/09-07-SUMMARY.md`, `docs/AI-COLLABORATION.md`

**Summary/frontmatter pattern** (`09-07-SUMMARY.md` lines 1-18):
```yaml
---
phase: 09-render-dashboard
plan: "07"
subsystem: dashboard-hardening
tags: [dashboard, cache, stale-data, fx, render, tests]
provides:
  - Cache/stale-state helpers.
  - Display-only USD/NIS FX helpers.
  - Final dashboard test hardening.
patterns-established: [display-only-cache, source-cache-timestamps]
---
```

**Verification summary pattern** (`09-07-SUMMARY.md` lines 94-110):
```markdown
## Verification

- `python -m pytest tests/test_dashboard_cache.py tests/test_dashboard_fx.py tests/test_dashboard_render_config.py tests/test_dashboard_read_only.py -q` - passed, 18 tests.
- `python -m pytest -q` - passed full suite.

## Next Phase Readiness

Phase 10 can add CI/CD, security/release review, dashboard health workflows,
operations docs, and final audit.
```

**Use for Phase 10:** Release/handoff artifact should include metadata, files changed, verification commands/results, user setup required, unresolved external dependencies, and explicit release limitations.

---

### `SECURITY_REVIEW.md` / release audit artifact (documentation, transform)

**Analog:** `docs/safety.md`, `docs/licensing.md`, `docs/AI-COLLABORATION.md`

**Safety boundary pattern** (`docs/safety.md` lines 154-167):
```markdown
## Dashboard Safety

The Render dashboard is password-protected with a single external
`DASHBOARD_PASSWORD` environment variable. No raw dashboard password may appear
in repository files, docs, tests, logs, reports, planning artifacts, or chat.

The dashboard action surface is limited to view, refresh, login, and logout.
It must remain Overview-first on mobile and read-only for every page.

Dashboard cache and FX display are display-only. Cached data must be labeled
with source/cache timestamps and stale status. NIS conversion is never an
accounting source; USD remains authoritative.
```

**Licensing pattern** (`docs/licensing.md` lines 6-17):
```markdown
The repository uses strict attribution from day one:

- `NOTICE` records project identity and direct-copy status.
- `THIRD_PARTY_NOTICES.md` records third-party source code, examples, snippets,
  or substantial logic reused by the project.
- Substantial third-party logic must not be copied until the source, license,
  reuse scope, attribution requirement, and affected files are recorded.
```

**Secret handling pattern** (`docs/AI-COLLABORATION.md` lines 99-107):
```markdown
When external credentials or subscriptions are needed, ask the user in Hebrew
to complete the action outside chat. Never ask the user to paste secrets into
chat. Use approved secret stores for:

- QuantConnect API credentials.
- GitHub Actions Secrets.
- Telegram bot token and chat ID.
- Render environment variables.
```

**Use for Phase 10:** Security review should be a written checklist plus tested evidence: no real-money path, no secret values, read-only dashboard, no fake performance, licensing/attribution current, and all external credentials delegated to approved stores.

## Shared Patterns

### Secret Placeholders Only

**Source:** `.env.example` lines 1-15 and `render.yaml` lines 16-29

```text
# DO_NOT_PASTE_SECRETS_HERE
# Store real secrets only in approved external secret stores.
QUANTCONNECT_USER_ID=
QUANTCONNECT_API_TOKEN=
TELEGRAM_BOT_TOKEN=
TELEGRAM_CHAT_ID=
DASHBOARD_PASSWORD=
```

Apply to all workflows, docs, scripts, and release artifacts. It is acceptable to name required environment variables; it is not acceptable to include values.

### Deterministic Offline Pytest

**Source:** `docs/testing.md` lines 5-18, `pyproject.toml` lines 25-28

```markdown
python -m pytest
```

Apply to GitHub Actions test workflow and release gates. External checks may be optional/skipped, but deterministic offline tests must remain credential-free.

### Paper-Only And No-Real-Money Safety

**Source:** `tests/test_safety.py` lines 7-33, `docs/safety.md` lines 109-124

Apply to CI scans, security review, and release audit. Workflows must not add hidden live-money switches, real broker adapters, leverage, margin, short selling, options, futures, cryptocurrency, Forex, or dashboard order controls.

### Read-Only Dashboard

**Source:** `tests/test_dashboard_read_only.py` lines 59-68 and `docs/safety.md` lines 156-163

```python
assert shell.controls == ("view", "refresh", "logout")
assert READ_ONLY_ALLOWED_ACTIONS == ("view", "refresh", "login", "logout")
```

Apply to dashboard health, release gates, and security review. Dashboard health may observe availability, but it must not mutate QuantConnect, Render, Telegram, or local portfolio state.

### No Fake Performance Artifacts

**Source:** `tests/test_backtest_artifact_safety.py` lines 9-16 and `docs/safety.md` lines 92-107

Apply to weekly validation, release audit, documentation, and handoff. Missing QuantConnect access is `not_run`; fake backtests, fake portfolios, and profitability claims remain prohibited.

## No Analog Found

| File | Role | Data Flow | Reason |
|------|------|-----------|--------|
| `.github/workflows/*.yml` | config | batch/request-response | No `.github` directory or existing GitHub Actions workflows exist yet. Use `pyproject.toml`, `render.yaml`, `docs/testing.md`, and static YAML tests as local pattern sources. |

## Metadata

**Analog search scope:** `.planning/`, `docs/`, `tests/`, `scripts/`, `pyproject.toml`, `render.yaml`, `.env.example`, `README.md`, `marketpilot/`, `dashboard/`
**Files scanned:** 120+ repository files via `rg --files` and targeted reads
**Pattern extraction date:** 2026-06-15
