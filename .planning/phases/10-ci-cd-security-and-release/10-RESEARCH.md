# Phase 10: CI/CD, Security and Release - Research

**Researched:** 2026-06-15  
**Domain:** GitHub Actions CI/CD, secret handling, QuantConnect/Render release safety, security review, documentation, release audit  
**Confidence:** HIGH for repository-specific scope; MEDIUM for external workflow APIs

## User Constraints

### Phase Scope

Prepare the project for safe operation with CI/CD, security review, documentation, recovery procedures, and final release audit. [VERIFIED: user prompt]

### Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| CI-01 | GitHub Actions run deterministic unit tests without requiring QuantConnect, Telegram, Render, broker credentials, internet, or real market access. [VERIFIED: .planning/REQUIREMENTS.md] | Main CI must install repo dependencies and run `python -m pytest -q`; current suite has 351 collected tests and passes locally. [VERIFIED: pytest collect/run] |
| CI-02 | GitHub Actions include test, QuantConnect sync, cloud backtest, weekly validation, and dashboard health workflows when implementation reaches those phases. [VERIFIED: .planning/REQUIREMENTS.md] | Add separate workflows with default offline CI and guarded optional QuantConnect/Render jobs. [VERIFIED: repo docs + CITED: https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax] |
| CI-03 | Documentation covers purpose, architecture, responsibilities, safety, strategy rules, scoring, risk, lifecycle, assumptions, backtesting, bias risks, activation gates, setup, operations, recovery, troubleshooting, limitations, licensing, and disclaimer. [VERIFIED: .planning/REQUIREMENTS.md] | Existing docs cover most domains; Phase 10 should add release-facing `docs/operations.md`, `docs/troubleshooting.md`, and `docs/release.md`. [VERIFIED: docs/*.md grep] |
| CI-04 | Security review verifies secret handling, read-only dashboard behavior, and absence of real-money trading paths. [VERIFIED: .planning/REQUIREMENTS.md] | Add a written security review plus static tests aggregating existing safety, dashboard, Telegram, Paper Trading, workflow, and docs scans. [VERIFIED: tests/test_safety.py + tests/test_dashboard_read_only.py + tests/test_paper_trading_safety.py] |
| CI-05 | Release preparation verifies automated tests, operational documentation, attribution, no fake performance artifacts, and no profitability claims. [VERIFIED: .planning/REQUIREMENTS.md] | Add release audit artifact and tests for required files, artifact labels, no fake results, no unverified profitability language, and licensing/notice state. [VERIFIED: tests/test_project_files.py + tests/test_backtest_artifact_safety.py] |
| CI-06 | Git status and change summaries distinguish executed checks from unexecuted checks. [VERIFIED: .planning/REQUIREMENTS.md] | Release and summary templates must list commands with `passed`, `failed`, `skipped`, or `not_run`, never imply skipped external checks passed. [VERIFIED: Phase 8/9 summaries] |

## Summary

Phase 10 should add workflow infrastructure and release gates without changing trading behavior. The repository currently has no `.github` workflow directory, uses Python `>=3.11`, declares `PyYAML>=6.0.2`, `streamlit>=1.51,<2`, and `pytest>=8.0`, and has a full deterministic offline pytest suite that passed locally on 2026-06-15. [VERIFIED: rg .github + pyproject.toml + requirements*.txt + pytest]

Default CI must be secret-free and deterministic. Optional QuantConnect and Render workflows should be separate, manually dispatchable or scheduled, explicitly guarded by secret availability, and should emit `not_run`/skipped evidence when credentials or external setup are unavailable. [VERIFIED: docs/testing.md + docs/quantconnect_verification.md + CITED: https://docs.github.com/actions/security-guides/using-secrets-in-github-actions]

**Primary recommendation:** Add four workflows: `tests.yml`, `quantconnect.yml`, `weekly-validation.yml`, and `dashboard-health.yml`, plus `docs/operations.md`, `docs/troubleshooting.md`, `docs/release.md`, `SECURITY_REVIEW.md`, static CI/security/release tests, and a final release audit that traces every v1 requirement. [VERIFIED: .planning/ROADMAP.md + .planning/phases/10-ci-cd-security-and-release/10-PATTERNS.md]

## Project Constraints (from AGENTS.md)

- Communicate with the user in Hebrew; write all project files, code, tests, docs, and GSD artifacts in English. [VERIFIED: AGENTS.md]
- Read `.planning/PROJECT.md`, `.planning/REQUIREMENTS.md`, `.planning/ROADMAP.md`, `.planning/STATE.md`, and `docs/AI-COLLABORATION.md` before phase work. [VERIFIED: AGENTS.md]
- Do not modify completed phases without a change plan. [VERIFIED: AGENTS.md]
- Use focused commits only when explicitly asked by the user; this research task should write only the research file. [VERIFIED: AGENTS.md + user prompt]
- Never invent QuantConnect APIs, LEAN classes, Cloud API endpoints, package behavior, tutorial details, backtest results, Paper Trading results, portfolio values, or profitability claims. [VERIFIED: AGENTS.md]
- Keep the product simulated Paper Trading only; do not add real-broker code, real-money credentials, leverage, margin, short selling, options, futures, cryptocurrency, or hidden live-trading switches. [VERIFIED: AGENTS.md]
- Keep Render read only and never add dashboard order-entry controls. [VERIFIED: AGENTS.md]
- QuantConnect remains the source of truth for simulated cash, equity, holdings, orders, fills, Paper Trading state, algorithm status, and QuantConnect Backtest results. [VERIFIED: AGENTS.md]
- Telegram failures must remain independent from trading safety, and Telegram secrets must never appear in logs, docs, tests, reports, or chat. [VERIFIED: AGENTS.md]
- Never bypass failing tests, expose credentials, or write secrets into repository files. [VERIFIED: AGENTS.md]
- If credentials or paid setup are required, request user action outside chat and do not ask the user to paste secrets into chat. [VERIFIED: AGENTS.md]

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|--------------|----------------|-----------|
| Deterministic unit tests | GitHub Actions | Python test suite | CI owns repeatable execution; repo tests own behavior coverage. [VERIFIED: docs/testing.md] |
| QuantConnect sync/backtest workflow | GitHub Actions | QuantConnect Cloud | Actions should orchestrate only; QuantConnect owns cloud project/backtest state and results. [CITED: https://www.quantconnect.com/docs/v2/lean-cli/api-reference/lean-cloud-backtest] |
| QuantConnect Paper deploy safety | QuantConnect Cloud/operator | GitHub Actions | Paper live deploy is an interactive brokerage-selection path; CI must not silently deploy or select non-Paper brokerages. [CITED: https://www.quantconnect.com/docs/v2/lean-cli/live-trading/brokerages/quantconnect-paper-trading] |
| Render dashboard deploy/health | Render | GitHub Actions | Render owns service runtime and health checks; Actions can trigger a secret deploy hook and read a health URL. [CITED: https://render.com/docs/deploy-hooks] |
| Secret handling | GitHub/Render/QuantConnect secret stores | Repo config names only | Repo files may name variables but must not contain values. [VERIFIED: .env.example + render.yaml + CITED: https://render.com/docs/blueprint-spec] |
| Security review | Repository docs/tests | GitHub Actions | Security gate should be source-controlled evidence plus automated scans. [VERIFIED: tests/test_safety.py + tests/test_dashboard_read_only.py] |
| Release audit | Repository docs/tests | GSD planning artifacts | Final release gate must trace requirements and distinguish executed checks from skipped/not-run checks. [VERIFIED: .planning/REQUIREMENTS.md + Phase 8/9 summaries] |

## Standard Stack

### Core

| Library / Tool | Version / Ref | Purpose | Why Standard |
|----------------|---------------|---------|--------------|
| GitHub Actions | Workflow YAML in `.github/workflows` | CI/CD orchestration | GitHub requires workflow files in `.github/workflows`; supports `push`, `pull_request`, `schedule`, and `workflow_dispatch`. [CITED: https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax] |
| `actions/checkout` | Pin to full commit SHA during implementation; official examples currently show `@v6` through setup-python README | Checkout repository for jobs | GitHub-owned action; secure-use docs recommend full SHA pinning for immutable releases. [CITED: https://github.com/actions/setup-python] [CITED: https://docs.github.com/en/actions/reference/security/secure-use] |
| `actions/setup-python` | Pin to full commit SHA during implementation; official README currently shows `@v6` | Install Python in CI | Official action installs Python and supports pip caching; README recommends explicit `python-version`. [CITED: https://github.com/actions/setup-python] |
| Python | `3.11.9` for release workflow | Runtime and test baseline | Repo requires Python `>=3.11`, and Render blueprint uses `PYTHON_VERSION=3.11.9`. [VERIFIED: pyproject.toml + render.yaml] |
| pytest | Repo declares `pytest>=8.0`; latest PyPI shown as `9.1.0`; local installed `7.3.1` | Test runner | Existing test config uses pytest and full local suite passes. [VERIFIED: pyproject.toml + pip index + pytest] |
| PyYAML | Repo declares `PyYAML>=6.0.2`; latest PyPI shown as `6.0.3` | YAML parsing for config/static tests | Existing tests parse YAML with `yaml.safe_load`. [VERIFIED: pyproject.toml + pip index + tests/test_dashboard_render_config.py] |

### Supporting

| Tool | Version / Ref | Purpose | When to Use |
|------|---------------|---------|-------------|
| LEAN CLI `lean` | Latest PyPI shown/local installed `1.0.225` | Optional QuantConnect sync/backtest/Paper operator workflow | Use only in guarded QuantConnect workflows with secrets and operator approval; missing setup must be `not_run`. [VERIFIED: pip index + lean --version + CITED: https://www.quantconnect.com/docs/v2/lean-cli/key-concepts/getting-started] |
| Render deploy hook | Secret URL in `RENDER_DEPLOY_HOOK_URL` | Optional dashboard deploy trigger | Use after tests pass and only when hook secret exists. [CITED: https://render.com/docs/deploy-hooks] |
| `curl` / `curl.exe` | Local `curl.exe 8.19.0`; GitHub runners include curl by default in typical hosted images [ASSUMED] | Trigger Render deploy hook or dashboard health URL | Prefer shell `curl` over third-party deploy actions. [VERIFIED: curl.exe --version] |
| Streamlit | Repo declares `streamlit>=1.51,<2`; latest PyPI shown as `1.58.0` | Dashboard runtime | Do not add auth/database/cache add-ons in Phase 10. [VERIFIED: pyproject.toml + pip index + tests/test_dashboard_render_config.py] |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| GitHub-owned actions only | Third-party CI/security/deploy actions | Avoid for v1 release unless there is a package/action legitimacy checkpoint; GitHub docs require auditing action source and recommend SHA pinning. [CITED: https://docs.github.com/en/actions/reference/security/secure-use] |
| Render deploy hook via `curl` | Render CLI or third-party deploy action | Existing project intentionally did not add Render CLI; deploy hook is officially documented and can be stored as a GitHub secret. [VERIFIED: docs/render_dashboard.md + CITED: https://render.com/docs/deploy-hooks] |
| Optional QuantConnect workflow | Always-on cloud sync/backtest in CI | Always-on external jobs would require credentials/subscription and could mutate cloud projects; use guarded manual/scheduled jobs. [CITED: https://www.quantconnect.com/docs/v2/lean-cli/api-reference/lean-cloud-push] |

**Installation:**

```bash
python -m pip install -r requirements-dev.txt
```

No new Python runtime dependency is recommended for Phase 10. [VERIFIED: package audit + repo dependency scan]

## Package And Action Legitimacy Audit

| Package / Action | Registry / Source | Current Signal | Verdict | Disposition |
|------------------|-------------------|----------------|---------|-------------|
| `PyYAML` | PyPI | Exists, latest `6.0.3`; seam flagged `SUS` for unknown download telemetry. [VERIFIED: pip index + gsd package-legitimacy] | SUS | Existing approved repo dependency; do not bump without checkpoint. |
| `streamlit` | PyPI | Exists, latest `1.58.0`; seam flagged `SUS` for recent release and unknown download telemetry. [VERIFIED: pip index + gsd package-legitimacy] | SUS | Existing approved Phase 9 dependency; do not change range in Phase 10. |
| `pytest` | PyPI | Exists, latest `9.1.0`; seam flagged `SUS` for recent release and unknown download telemetry. [VERIFIED: pip index + gsd package-legitimacy] | SUS | Existing dev dependency; CI should install from `requirements-dev.txt`. |
| `lean` | PyPI | Exists/local installed `1.0.225`; seam flagged `SUS` for unknown download telemetry. [VERIFIED: pip index + lean --version + gsd package-legitimacy] | SUS | Optional QuantConnect workflow only; planner must add human verification before installing or pinning in CI. |
| `actions/checkout` | GitHub-owned action | Official action family; exact SHA must be verified at implementation. [CITED: https://docs.github.com/en/actions/reference/security/secure-use] | OK with SHA pin | Use only GitHub-owned action, pinned to full SHA. |
| `actions/setup-python` | GitHub-owned action | Official README documents Python install and pip caching; exact SHA must be verified at implementation. [CITED: https://github.com/actions/setup-python] | OK with SHA pin | Use only GitHub-owned action, pinned to full SHA. |

**Packages removed due to SLOP verdict:** none. [VERIFIED: gsd package-legitimacy]  
**Packages flagged as suspicious SUS:** `PyYAML`, `streamlit`, `pytest`, `lean`; existing dependencies may remain, but any install/version-bump plan must include a human verification checkpoint. [VERIFIED: gsd package-legitimacy]

## Architecture Patterns

### System Architecture Diagram

```text
Developer push / PR
  -> GitHub Actions tests.yml
     -> checkout repo
     -> setup Python 3.11.9
     -> install requirements-dev.txt
     -> run deterministic pytest and static release/security scans
     -> pass/fail evidence

Manual dispatch / schedule
  -> quantconnect.yml
     -> verify required GitHub secrets exist by name
     -> if missing: write not_run evidence
     -> if present: optional lean cloud push/backtest only on approved branch/input
     -> QuantConnect Cloud remains authority for results

Manual dispatch / post-test branch gate
  -> dashboard-health.yml / render-deploy job
     -> if RENDER_DEPLOY_HOOK_URL missing: skipped/not_run
     -> if present: curl deploy hook or dashboard health URL
     -> Render remains dashboard runtime

Release audit
  -> security/release tests + SECURITY_REVIEW.md + docs/release.md
     -> trace v1 requirements
     -> list executed, skipped, and not_run checks
```

### Recommended Project Structure

```text
.github/workflows/
├── tests.yml                 # offline deterministic pytest and static gates
├── quantconnect.yml          # guarded manual/scheduled QC sync/backtest
├── weekly-validation.yml     # scheduled validation/report audit, no fake results
└── dashboard-health.yml      # guarded Render dashboard health/deploy hook checks
docs/
├── operations.md             # operator procedures and workflow schedule
├── troubleshooting.md        # symptom -> safe action runbook
└── release.md                # release checklist and handoff
tests/
├── test_ci_workflows.py
├── test_security_release_gates.py
└── test_release_audit.py
SECURITY_REVIEW.md
```

### Pattern 1: Secret-Free Default CI

**What:** `tests.yml` runs only deterministic offline tests and static scans; it must not reference QuantConnect, Telegram, Render, dashboard, or broker secrets. [VERIFIED: docs/testing.md]  
**When to use:** Every push/PR. [CITED: https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax]  
**Example:**

```yaml
# Source: GitHub workflow syntax + setup-python README
name: tests
on:
  push:
  pull_request:
  workflow_dispatch:
permissions:
  contents: read
jobs:
  pytest:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@<FULL_COMMIT_SHA>
      - uses: actions/setup-python@<FULL_COMMIT_SHA>
        with:
          python-version: "3.11.9"
          cache: "pip"
          cache-dependency-path: "requirements-dev.txt"
      - run: python -m pip install -r requirements-dev.txt
      - run: python -m pytest -q
```

### Pattern 2: Guarded External Workflow

**What:** Optional external workflow checks secret presence before running, records skipped/not-run evidence when unavailable, and avoids printing secret values. [VERIFIED: docs/setup.md + docs/quantconnect_verification.md]  
**When to use:** QuantConnect sync/backtest, Render deploy hook, dashboard health against private URLs. [CITED: https://docs.github.com/actions/security-guides/using-secrets-in-github-actions]  
**Example:**

```yaml
# Source: GitHub secrets docs + QuantConnect LEAN CLI docs
if: ${{ secrets.QUANTCONNECT_USER_ID != '' && secrets.QUANTCONNECT_API_TOKEN != '' }}
env:
  QUANTCONNECT_USER_ID: ${{ secrets.QUANTCONNECT_USER_ID }}
  QUANTCONNECT_API_TOKEN: ${{ secrets.QUANTCONNECT_API_TOKEN }}
run: |
  echo "::add-mask::$QUANTCONNECT_USER_ID"
  echo "::add-mask::$QUANTCONNECT_API_TOKEN"
  lean cloud backtest "$QUANTCONNECT_PROJECT_ID" --push
```

### Pattern 3: Release Evidence Format

**What:** Release artifacts list each command as `passed`, `failed`, `skipped`, or `not_run`; external missing prerequisites are not success. [VERIFIED: Phase 8/9 summaries + docs/backtesting.md]  
**When to use:** `docs/release.md`, plan summaries, security review, UAT/release handoff. [VERIFIED: CI-06 in .planning/REQUIREMENTS.md]

### Anti-Patterns to Avoid

- **Tag-only actions:** Use full SHA pins for actions instead of mutable tags when release security matters. [CITED: https://docs.github.com/en/actions/reference/security/secure-use]
- **Default write token:** Do not grant broad `GITHUB_TOKEN` permissions; set `permissions: contents: read` unless a job needs more. [CITED: https://docs.github.com/actions/reference/authentication-in-a-workflow]
- **Secret echo/debug:** Do not print env dumps or structured secrets; GitHub warns that masking happens only when runner sees a secret and exposed values need rotation. [CITED: https://docs.github.com/en/actions/reference/security/secure-use]
- **Unconditional `lean cloud push`:** QuantConnect documents that cloud push can delete cloud files not present locally and overwrite cloud config values. [CITED: https://www.quantconnect.com/docs/v2/lean-cli/api-reference/lean-cloud-push]
- **Fake external success:** Missing QuantConnect/Render/Telegram access must be `not_run` or skipped, never represented as passed. [VERIFIED: docs/backtesting.md + docs/safety.md]
- **Dashboard health mutation:** Health checks may read availability only; dashboard remains view/refresh/login/logout only. [VERIFIED: tests/test_dashboard_read_only.py]

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| CI orchestration | Custom shell scheduler | GitHub Actions workflows | Native triggers, permissions, secrets, logs, and environments exist. [CITED: https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax] |
| Secret store | Repo `.env`, docs examples, encrypted blobs in git | GitHub Actions Secrets, Render env vars, QuantConnect credentials outside repo | Official docs support secret stores and repo policy forbids values in files/chat. [VERIFIED: AGENTS.md + CITED: https://render.com/docs/configure-environment-variables] |
| Render deploy integration | Third-party deploy action | Render deploy hook stored as `RENDER_DEPLOY_HOOK_URL` | Render officially documents deploy hooks for GitHub Actions and treats hook URLs as secrets. [CITED: https://render.com/docs/deploy-hooks] |
| QuantConnect API signing | Ad hoc copied snippets in CI logs | LEAN CLI or a reviewed helper with no logged token | QuantConnect REST authentication uses timestamped token hashing and Basic auth headers. [CITED: https://www.quantconnect.com/docs/v2/cloud-platform/api-reference/authentication] |
| Release traceability | Manual checklist only | Static release tests plus `docs/release.md` | Existing project uses tests to guard required files, docs, artifact labels, and safety language. [VERIFIED: tests/test_project_files.py + tests/test_backtest_artifact_safety.py] |

**Key insight:** Phase 10 should automate evidence collection and guardrails, not add new execution authority. [VERIFIED: project constraints + Phase 10 success criteria]

## Common Pitfalls

### Pitfall 1: CI Requires External Credentials
**What goes wrong:** Default CI fails for contributors or PRs because it expects QuantConnect, Telegram, Render, market data, or broker credentials. [VERIFIED: docs/testing.md]  
**How to avoid:** Keep `tests.yml` offline and secret-free; put external checks in separate guarded workflows. [VERIFIED: docs/testing.md + CITED: GitHub secrets docs]  
**Warning signs:** Default workflow references `secrets.QUANTCONNECT_*`, `TELEGRAM_*`, `RENDER_*`, or real health URLs. [VERIFIED: .env.example]

### Pitfall 2: QuantConnect Workflow Mutates Cloud State Unexpectedly
**What goes wrong:** `lean cloud push` may create projects, update files, delete cloud files absent locally, or overwrite cloud config. [CITED: https://www.quantconnect.com/docs/v2/lean-cli/api-reference/lean-cloud-push]  
**How to avoid:** Use manual dispatch with explicit input confirmation for push/backtest, branch guards, concurrency, and `not_run` records when prerequisites are missing. [VERIFIED: repo safety policy + GitHub workflow syntax]

### Pitfall 3: Render Deploy Hook Leaks
**What goes wrong:** A deploy hook URL in YAML/docs/logs can trigger deployments. [CITED: https://render.com/docs/deploy-hooks]  
**How to avoid:** Store `RENDER_DEPLOY_HOOK_URL` only as a GitHub secret, mask it, and never print the URL. [CITED: https://docs.github.com/actions/security-guides/using-secrets-in-github-actions + https://render.com/docs/deploy-hooks]

### Pitfall 4: Release Claims Outrun Evidence
**What goes wrong:** Release notes imply profitability, backtest success, Paper deployment, or dashboard health when checks were not executed. [VERIFIED: docs/safety.md + docs/backtesting.md]  
**How to avoid:** Use a release evidence table with command, environment, status, output summary, artifact path, and `not_run` reason. [VERIFIED: CI-06]

### Pitfall 5: Action Supply Chain Drift
**What goes wrong:** Mutable action tags move after release. [CITED: https://docs.github.com/en/actions/reference/security/secure-use]  
**How to avoid:** Pin actions to full commit SHAs and record the verified upstream tag/repo in `docs/operations.md` or comments. [CITED: https://docs.github.com/en/actions/reference/security/secure-use]

## Code Examples

### Static Workflow Test

```python
# Source: tests/test_dashboard_render_config.py pattern
from pathlib import Path
import yaml

ROOT = Path(__file__).resolve().parents[1]

def workflow(name: str) -> dict:
    return yaml.safe_load((ROOT / ".github" / "workflows" / name).read_text(encoding="utf-8"))

def test_default_ci_is_secret_free_and_python_311():
    ci = workflow("tests.yml")
    combined = (ROOT / ".github" / "workflows" / "tests.yml").read_text(encoding="utf-8")
    assert "python-version: \"3.11.9\"" in combined
    assert "python -m pytest -q" in combined
    assert "secrets.QUANTCONNECT" not in combined
    assert "secrets.TELEGRAM" not in combined
    assert "secrets.RENDER" not in combined
```

### Release Evidence Table

```markdown
| Check | Command | Status | Evidence | Notes |
|-------|---------|--------|----------|-------|
| Offline tests | `python -m pytest -q` | passed | 351 collected tests | Python 3.11 CI required |
| QuantConnect cloud backtest | `lean cloud backtest ...` | not_run | missing secrets | No fake results |
| Render health | `curl -fsS $DASHBOARD_HEALTH_URL` | skipped | missing URL secret | No URL logged |
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Pin actions to major tags | Pin release-critical actions to full commit SHA | Current GitHub secure-use docs | Immutable action refs reduce supply-chain drift. [CITED: https://docs.github.com/en/actions/reference/security/secure-use] |
| Always run external deployment from CI | Guard external workflows by secrets, branch, manual dispatch, and environment approvals | Current GitHub/Render/QuantConnect docs | Missing external setup becomes `not_run`, not failure or fake success. [CITED: https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax + https://render.com/docs/deploy-hooks + https://www.quantconnect.com/docs/v2/lean-cli/api-reference/lean-cloud-backtest] |
| Store deployment config values in repo | Store secret values in GitHub/Render/QuantConnect secret stores; repo stores names only | Current repo safety policy and Render docs | Prevents credentials from entering git history. [VERIFIED: .env.example + render.yaml + CITED: Render env docs] |

**Deprecated/outdated:**

- Mutable action tags without verification are not acceptable for release gates. [CITED: https://docs.github.com/en/actions/reference/security/secure-use]
- Always-on QuantConnect mutation workflows are unsafe for this repo because QuantConnect remains authoritative and push can mutate cloud projects. [VERIFIED: project constraints + CITED: QuantConnect cloud push docs]
- Any fake backtest/Paper/portfolio/profitability artifact is prohibited. [VERIFIED: docs/safety.md]

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | GitHub-hosted Ubuntu runners include `curl` by default. [ASSUMED] | Standard Stack | If unavailable, Render hook/health jobs need an explicit install or Python stdlib HTTP helper. |

## Open Questions

1. **Should QuantConnect workflows run automatically on schedule or only manually at first?**  
   - What we know: GitHub supports `schedule` and `workflow_dispatch`; scheduled workflows run only on the default branch and can be delayed or dropped during high load. [CITED: https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows]  
   - What's unclear: User credential/subscription readiness and tolerance for cloud-project mutation. [VERIFIED: .planning/PROJECT.md External Actions]  
   - Recommendation: Start with `workflow_dispatch`; add weekly schedule only after a successful manual run is documented. [VERIFIED: safety constraints]

2. **Should actions be pinned immediately to full SHAs or initially to official major tags with a follow-up pin task?**  
   - What we know: GitHub says full SHA is the immutable release option. [CITED: https://docs.github.com/en/actions/reference/security/secure-use]  
   - What's unclear: The planner may need live GitHub tag/SHA lookup during implementation. [VERIFIED: current research did not pin exact SHAs]  
   - Recommendation: Plan a checkpoint to resolve and record full SHAs before merging workflows. [CITED: https://docs.github.com/en/actions/reference/security/secure-use]

3. **What public/secret dashboard health URL should CI use?**  
   - What we know: Render health checks accept HTTP paths and `render.yaml` uses `/`. [VERIFIED: render.yaml + CITED: https://render.com/docs/health-checks]  
   - What's unclear: The deployed Render URL is not present in repo files. [VERIFIED: rg docs/render.yaml]  
   - Recommendation: Use `DASHBOARD_HEALTH_URL` as a GitHub secret/variable and skip health checks when absent. [CITED: https://docs.github.com/actions/security-guides/using-secrets-in-github-actions]

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|-------------|-----------|---------|----------|
| Python | Local tests, CI baseline | Partial | Local `3.10.10`; project requires `>=3.11` | CI must use Python `3.11.9`. [VERIFIED: python --version + pyproject.toml + render.yaml] |
| pip | Dependency install | Yes | `25.2` local | GitHub setup-python environment. [VERIFIED: pip --version] |
| pytest | Test runner | Yes | `7.3.1` local; repo declares `pytest>=8.0` | CI install from `requirements-dev.txt`. [VERIFIED: pytest --version + requirements-dev.txt] |
| git | Workflow/source control | Yes | `2.45.2.windows.1` | GitHub runner git. [VERIFIED: git --version] |
| gh CLI | Optional GitHub secret/admin inspection | No | Not found | Use GitHub UI or avoid requiring `gh` in workflows. [VERIFIED: command probe] |
| LEAN CLI | Optional QuantConnect workflow | Yes local | `1.0.225` | Mark QuantConnect checks `not_run` when unavailable in CI. [VERIFIED: lean --version] |
| Docker | Optional local LEAN engine | No | Not found | Use QuantConnect Cloud or mark local LEAN checks `not_run`. [VERIFIED: command probe + CITED: QuantConnect install docs] |
| curl | Render deploy/health | Yes local as `curl.exe` | `8.19.0` | Python stdlib HTTP helper if shell curl absent. [VERIFIED: curl.exe --version] |

**Missing dependencies with no fallback:** none for default offline CI. [VERIFIED: pytest passed]  
**Missing dependencies with fallback:** Docker missing; use QuantConnect Cloud/not-run records. `gh` missing; use GitHub UI/manual secret setup. [VERIFIED: command probes]

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest; local installed `7.3.1`, repo dev dependency `pytest>=8.0`. [VERIFIED: pytest --version + requirements-dev.txt] |
| Config file | `pyproject.toml` with `testpaths = ["tests"]`, `pythonpath = ["."]`, `addopts = "-q"`. [VERIFIED: pyproject.toml] |
| Quick run command | `python -m pytest tests/test_ci_workflows.py tests/test_security_release_gates.py tests/test_release_audit.py -q` [VERIFIED: repo pattern] |
| Full suite command | `python -m pytest -q` [VERIFIED: pyproject.toml + local run] |

### Phase Requirements -> Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|--------------|
| CI-01 | Offline deterministic CI does not require external services/secrets. [VERIFIED: requirements] | unit/static | `python -m pytest tests/test_ci_workflows.py -q` | Missing, Wave 0 |
| CI-02 | Workflows exist for tests, QuantConnect, weekly validation, dashboard health with guards. [VERIFIED: requirements] | static YAML | `python -m pytest tests/test_ci_workflows.py -q` | Missing, Wave 0 |
| CI-03 | Operations/recovery/troubleshooting/setup/licensing/disclaimer/limitations docs complete. [VERIFIED: requirements] | docs/static | `python -m pytest tests/test_release_audit.py -q` | Missing, Wave 0 |
| CI-04 | Secret handling, read-only dashboard, no real-money path verified. [VERIFIED: requirements] | security/static | `python -m pytest tests/test_security_release_gates.py -q` | Missing, Wave 0 |
| CI-05 | Release audit checks tests/docs/attribution/no fake artifacts/no profitability claims. [VERIFIED: requirements] | release/static | `python -m pytest tests/test_release_audit.py -q` | Missing, Wave 0 |
| CI-06 | Git status and summaries distinguish executed from not-run checks. [VERIFIED: requirements] | docs/static | `python -m pytest tests/test_release_audit.py -q` | Missing, Wave 0 |

### Sampling Rate

- **Per task commit:** targeted tests for touched workflow/docs/security files plus `python -m pytest tests/test_safety.py tests/test_dashboard_read_only.py tests/test_paper_trading_safety.py -q`. [VERIFIED: existing test patterns]
- **Per wave merge:** `python -m pytest -q`. [VERIFIED: local full-suite run]
- **Phase gate:** Full suite green, workflow static tests green, `SECURITY_REVIEW.md` complete, release evidence table complete, and git status recorded. [VERIFIED: CI-04/CI-05/CI-06]

### Wave 0 Gaps

- [ ] `tests/test_ci_workflows.py` covers CI-01 and CI-02. [VERIFIED: missing file]
- [ ] `tests/test_security_release_gates.py` covers CI-04. [VERIFIED: missing file]
- [ ] `tests/test_release_audit.py` covers CI-03, CI-05, CI-06. [VERIFIED: missing file]
- [ ] `.github/workflows/tests.yml` covers default CI. [VERIFIED: no .github dir]
- [ ] `.github/workflows/quantconnect.yml`, `weekly-validation.yml`, and `dashboard-health.yml` cover guarded optional workflows. [VERIFIED: no .github dir]

## Security Domain

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|------------------|
| V2 Authentication | yes | Dashboard single-password auth from external `DASHBOARD_PASSWORD`; no data before login. [VERIFIED: dashboard/auth.py + tests/test_dashboard_auth.py] |
| V3 Session Management | partial | Streamlit session/auth state must not expose secrets; Phase 10 only audits existing behavior. [VERIFIED: dashboard/app.py + tests/test_dashboard_auth.py] |
| V4 Access Control | yes | Dashboard actions limited to view/refresh/login/logout; workflows use least-privilege `GITHUB_TOKEN`. [VERIFIED: tests/test_dashboard_read_only.py + CITED: GitHub token docs] |
| V5 Input Validation | yes | YAML loaded with `yaml.safe_load`; workflow/static tests should parse YAML rather than string-only validation. [VERIFIED: tests/test_dashboard_render_config.py] |
| V6 Cryptography / Secrets | yes | Use GitHub/Render/QuantConnect secret stores; do not store plaintext secrets in workflows or repo files. [VERIFIED: AGENTS.md + CITED: GitHub secrets docs + Render env docs] |
| V7 Error Handling / Logging | yes | Mask sensitive values, redact diagnostics, and rotate exposed secrets if leaked. [VERIFIED: dashboard/redaction.py + CITED: GitHub secure use reference] |
| V8 Data Protection | yes | No credentials, tokens, portfolio fake authority, or unverified performance artifacts in git. [VERIFIED: docs/safety.md] |
| V12 Security Configuration | yes | Workflow permissions, SHA-pinned actions, guarded external jobs, and Render `sync:false` env vars. [CITED: https://docs.github.com/en/actions/reference/security/secure-use + https://render.com/docs/blueprint-spec] |
| V13 API / Web Service | yes | QuantConnect/Render calls are external API boundaries and must be read-only or explicitly operator-gated. [CITED: https://www.quantconnect.com/docs/v2/cloud-platform/api-reference/authentication + https://render.com/docs/deploy-hooks] |
| V15 Business Logic | yes | No real-money path, no dashboard mutation, no fake profitability, no fake external success. [VERIFIED: docs/safety.md + requirements] |

### Known Threat Patterns for Phase 10

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Workflow logs leak secret values | Information Disclosure | Use GitHub Secrets, `::add-mask::`, no env dumps, rotate leaked values. [CITED: https://docs.github.com/en/actions/reference/security/secure-use] |
| Mutable action tag changes behavior | Tampering | Pin action refs to full commit SHA and record upstream repo/tag. [CITED: https://docs.github.com/en/actions/reference/security/secure-use] |
| QuantConnect cloud push overwrites/deletes cloud files | Tampering | Manual dispatch, branch/input guard, concurrency, explicit operator docs, no default push. [CITED: https://www.quantconnect.com/docs/v2/lean-cli/api-reference/lean-cloud-push] |
| Render deploy hook exposed | Elevation of Privilege | Store hook URL as GitHub secret only; never log URL. [CITED: https://render.com/docs/deploy-hooks] |
| Dashboard health check becomes dashboard action | Elevation of Privilege | Health workflow may GET health endpoint only; no dashboard order/recovery/Telegram paths. [VERIFIED: docs/dashboard.md] |
| Skipped external checks reported as passed | Repudiation | Release evidence table must record `not_run` reason. [VERIFIED: CI-06 + Phase 8/9 summary pattern] |
| Fake backtest/Paper/profitability artifacts enter release | Tampering/Repudiation | Static release audit scans and source labels: real, fixture, schema, example, not_run. [VERIFIED: tests/test_backtest_artifact_safety.py] |

## Release Documentation Scope

| Document | Required Content | Source Basis |
|----------|------------------|--------------|
| `docs/operations.md` | CI commands, workflow triggers, secret names, QuantConnect/Render operator steps, expected skipped states. | [VERIFIED: docs/setup.md + docs/render_dashboard.md + docs/operator_setup_phase08.md] |
| `docs/troubleshooting.md` | Symptom, likely cause, safe action, what not to do, not-run rules. | [VERIFIED: docs/recovery.md + docs/safety.md] |
| `docs/release.md` | Release checklist, requirement trace, executed/not-run evidence, limitations, license/disclaimer status. | [VERIFIED: CI-03/CI-05/CI-06] |
| `SECURITY_REVIEW.md` | Secret handling, no real-money path, read-only dashboard, fake-performance/profitability audit, action/package audit. | [VERIFIED: CI-04] |

## Sources

### Primary (HIGH confidence)

- `AGENTS.md` - repo constraints and safety policy. [VERIFIED: repo read]
- `.planning/PROJECT.md`, `.planning/REQUIREMENTS.md`, `.planning/ROADMAP.md`, `.planning/STATE.md` - phase requirements and product scope. [VERIFIED: repo read]
- `pyproject.toml`, `requirements.txt`, `requirements-dev.txt`, `render.yaml`, `.env.example` - runtime/dependency/deployment state. [VERIFIED: repo read]
- `docs/*.md`, Phase 8/9 summaries, `10-PATTERNS.md` - existing docs and phase handoff. [VERIFIED: repo grep/read]
- `tests/test_*` relevant to safety, dashboard, Telegram, QuantConnect, Render, release artifacts. [VERIFIED: repo read/grep]
- Local commands: `python -m pytest -q` passed; `python -m pytest --collect-only -q` counted 351 tests; environment probes recorded Python/pip/pytest/lean/git/curl/Docker/gh state. [VERIFIED: command output]

### Secondary (MEDIUM confidence)

- GitHub Actions workflow syntax: https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax [CITED]
- GitHub Actions secrets: https://docs.github.com/actions/security-guides/using-secrets-in-github-actions [CITED]
- GitHub Actions secure use: https://docs.github.com/en/actions/reference/security/secure-use [CITED]
- GitHub `GITHUB_TOKEN` permissions: https://docs.github.com/actions/reference/authentication-in-a-workflow [CITED]
- `actions/setup-python` README: https://github.com/actions/setup-python [CITED]
- Render deploy hooks: https://render.com/docs/deploy-hooks [CITED]
- Render health checks: https://render.com/docs/health-checks [CITED]
- Render Blueprint `sync:false`: https://render.com/docs/blueprint-spec [CITED]
- Render environment variables: https://render.com/docs/configure-environment-variables [CITED]
- QuantConnect LEAN CLI cloud backtest: https://www.quantconnect.com/docs/v2/lean-cli/api-reference/lean-cloud-backtest [CITED]
- QuantConnect LEAN CLI cloud push: https://www.quantconnect.com/docs/v2/lean-cli/api-reference/lean-cloud-push [CITED]
- QuantConnect API authentication: https://www.quantconnect.com/docs/v2/cloud-platform/api-reference/authentication [CITED]
- QuantConnect Paper Trading CLI deploy: https://www.quantconnect.com/docs/v2/lean-cli/live-trading/brokerages/quantconnect-paper-trading [CITED]
- OWASP ASVS project: https://owasp.org/www-project-application-security-verification-standard/ [CITED]

### Tertiary (LOW confidence)

- GitHub-hosted Ubuntu runner `curl` availability is assumed for future workflow examples; local Windows has `curl.exe 8.19.0`. [ASSUMED] [VERIFIED: local command]

## Metadata

**Confidence breakdown:**

- Standard stack: HIGH for repo-local dependencies and commands; MEDIUM for current external action refs because exact SHAs must be resolved during implementation. [VERIFIED: repo + CITED: GitHub docs]
- Architecture: HIGH for repository boundaries; MEDIUM for optional external workflow behavior because user-managed QuantConnect/Render setup is not present. [VERIFIED: repo + CITED: external docs]
- Pitfalls: HIGH for repo safety risks; MEDIUM for GitHub/Render/QuantConnect operational details based on official docs. [VERIFIED: repo + CITED: official docs]

**Research date:** 2026-06-15  
**Valid until:** 2026-07-15 for repo-local guidance; 2026-06-22 for GitHub Actions/Render/QuantConnect exact action refs and CLI/API details. [ASSUMED]
