# Phase 1: Foundation and Safety - Research

## Research Status

Completed inline because automatic subagent spawning is restricted in this Codex runtime unless the user explicitly requests subagents. The plan still follows the GSD role sequence: research, plan creation, and plan quality checks.

## Scope

This research is limited to Phase 1 foundations: repository skeleton, licensing, attribution, safety/config validation, Python packaging/testing, minimal non-trading QuantConnect compile path, and minimal static Streamlit shell. It does not design trading strategies, dynamic universe selection, order lifecycle, Telegram delivery, QuantConnect Paper Trading deployment, or Render deployment.

## Official Sources Checked

- QuantConnect LEAN CLI documentation - LEAN CLI supports local and cloud workflows and requires `lean init` in a workspace after login.
- QuantConnect LEAN CLI Getting Started - official flow says to install the CLI, run `lean login`, then `lean init` in an empty directory to create an organization workspace.
- QuantConnect LEAN CLI Project Management - official docs state project scaffolding exists and that use of the CLI requires membership in an organization on a paid tier.
- QuantConnect `lean build` API reference - `lean build` compiles LEAN in Docker images. This makes Docker availability and LEAN workspace setup part of the external verification boundary.
- Streamlit authentication and secrets documentation - secrets should be handled with native secrets management or environment variables, and app credentials must not be committed.
- Streamlit `config.toml` documentation - Streamlit configuration is TOML, and app config can suppress client error detail when appropriate.
- Python Packaging User Guide - `pyproject.toml` is the recommended central configuration file for build systems and tool configuration.
- pytest documentation - pytest supports configuration in repository-root config files, including `pyproject.toml`, and `testpaths`/pythonpath settings can keep test discovery deterministic.
- PyYAML documentation - use safe loading patterns (`safe_load`) for YAML configuration.

## Planning Implications

- Use `pyproject.toml` for project metadata, pytest config, and local package/test settings.
- Use a shared `marketpilot/` package for safety constants, configuration validation, FX seed logic, and domain models.
- Keep `lean/main.py` minimal and non-trading. It may subscribe to SPY and QQQ as benchmark symbols, but must not submit orders or create strategies.
- Treat real LEAN compile as a required Phase 1 verification target, but separate it from ordinary offline unit tests because it may require Docker, `lean` CLI, QuantConnect login, an organization workspace, and possibly a paid tier.
- Keep Streamlit Phase 1 shell static, read-only, and explicitly disconnected from live data.
- Add `.streamlit/secrets.toml` and other secret-bearing files to `.gitignore`; never create real secret files in the repo.
- Use MIT for project license and maintain attribution docs from day one.

## Risks And Constraints For Planner

- Do not make unit tests depend on internet, QuantConnect credentials, Telegram credentials, Render credentials, or real market data.
- Do not write fake Backtest results, fake holdings, fake portfolio values, or mock P&L artifacts.
- Do not add real broker settings or any live-money switch.
- Do not create placeholder strategy modules, order modules, or risk lifecycle modules in Phase 1.
- If LEAN compile cannot be executed by the agent due to missing external setup, Phase 1 execution must document the unexecuted manual verification command and reason.

## References

- https://www.quantconnect.com/docs/v2/lean-cli
- https://www.quantconnect.com/docs/v2/lean-cli/key-concepts/getting-started
- https://www.quantconnect.com/docs/v2/lean-cli/projects/project-management
- https://www.quantconnect.com/docs/v2/lean-cli/api-reference/lean-build
- https://docs.streamlit.io/develop/concepts/connections/authentication
- https://docs.streamlit.io/develop/concepts/connections/secrets-management
- https://docs.streamlit.io/develop/api-reference/configuration/config.toml
- https://packaging.python.org/en/latest/guides/writing-pyproject-toml/
- https://docs.pytest.org/en/stable/reference/customize.html
- https://docs.pytest.org/en/stable/explanation/goodpractices.html
- https://pyyaml.org/wiki/PyYAMLDocumentation
