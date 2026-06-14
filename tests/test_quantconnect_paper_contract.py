import pytest

from marketpilot.quantconnect_paper import (
    QUANTCONNECT_PAPER_BROKERAGE,
    QuantConnectPaperPrerequisites,
    QuantConnectPaperStatusCode,
    evaluate_quantconnect_paper_status,
    render_operator_deployment_command,
    validate_quantconnect_paper_brokerage,
)


def test_quantconnect_paper_trading_is_the_only_allowed_deployment_target():
    assert validate_quantconnect_paper_brokerage(QUANTCONNECT_PAPER_BROKERAGE) == QUANTCONNECT_PAPER_BROKERAGE

    with pytest.raises(ValueError, match="QuantConnect Paper Trading"):
        validate_quantconnect_paper_brokerage("Interactive Brokers")


def test_missing_quantconnect_prerequisites_return_not_configured():
    status = evaluate_quantconnect_paper_status(QuantConnectPaperPrerequisites())

    assert status.status_code is QuantConnectPaperStatusCode.NOT_CONFIGURED
    assert status.executed is False
    assert status.deployment_id is None
    assert status.allowed_brokerage_target == QUANTCONNECT_PAPER_BROKERAGE
    assert set(status.missing_prerequisites) == {
        "quantconnect_account",
        "organization_access",
        "paper_live_node",
        "project_id",
        "api_credentials",
        "data_provider",
    }


def test_configured_prerequisites_still_report_not_run_until_operator_runs_deployment():
    status = evaluate_quantconnect_paper_status(
        QuantConnectPaperPrerequisites(
            quantconnect_account=True,
            organization_access=True,
            paper_live_node=True,
            project_id=True,
            api_credentials=True,
            data_provider=True,
        )
    )

    assert status.status_code is QuantConnectPaperStatusCode.NOT_RUN
    assert status.executed is False
    assert status.deployment_id is None
    assert status.reasons == ("operator_deployment_not_run",)


def test_command_renderer_returns_operator_metadata_without_executing_cli():
    status = render_operator_deployment_command(
        QuantConnectPaperPrerequisites(
            quantconnect_account=True,
            organization_access=True,
            paper_live_node=True,
            project_id=True,
            api_credentials=True,
            data_provider=True,
        )
    )

    assert status.status_code is QuantConnectPaperStatusCode.CONFIGURED_OPERATOR_ACTION_REQUIRED
    assert status.executed is False
    assert status.deployment_id is None
    assert "lean cloud live deploy" in status.command_text
    assert "$QUANTCONNECT_PROJECT_ID" in status.command_text
    assert "$QUANTCONNECT_API_TOKEN" not in status.command_text
    assert "secret" not in status.command_text.lower()


def test_command_renderer_reports_missing_prerequisites_without_fake_deployment():
    status = render_operator_deployment_command(QuantConnectPaperPrerequisites(project_id=True))

    assert status.status_code is QuantConnectPaperStatusCode.NOT_CONFIGURED
    assert status.command_text is None
    assert status.executed is False
    assert status.deployment_id is None
    assert "api_credentials" in status.missing_prerequisites
