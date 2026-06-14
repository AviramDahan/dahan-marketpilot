from dataclasses import dataclass
from decimal import Decimal

from marketpilot.risk import PortfolioSnapshot, RiskRejectionReason, evaluate_portfolio_risk


@dataclass(frozen=True)
class Candidate:
    symbol: str = "MSFT"
    primary_setup: str = "relative_strength_leader"
    classification: str = "BUY_CANDIDATE"


def test_portfolio_risk_accepts_valid_candidate_without_treating_classification_as_instruction():
    decision = evaluate_portfolio_risk(
        candidate=Candidate(),
        portfolio=PortfolioSnapshot(simulated_equity=Decimal("100000"), available_cash=Decimal("100000")),
        entry_price=100,
        stop_distance=5,
        reward_risk=2.5,
        sector="Technology",
    )

    assert decision.accepted is True
    assert decision.quantity == 150
    assert decision.evidence["classification_is_instruction"] is False


def test_max_open_positions_rejects():
    decision = evaluate_portfolio_risk(
        candidate=Candidate(),
        portfolio=PortfolioSnapshot(
            simulated_equity=Decimal("100000"),
            available_cash=Decimal("100000"),
            open_positions=10,
        ),
        entry_price=100,
        stop_distance=5,
        reward_risk=2.5,
    )

    assert decision.accepted is False
    assert RiskRejectionReason.MAX_OPEN_POSITIONS in decision.rejection_reasons


def test_max_daily_entries_rejects():
    decision = evaluate_portfolio_risk(
        candidate=Candidate(),
        portfolio=PortfolioSnapshot(
            simulated_equity=Decimal("100000"),
            available_cash=Decimal("100000"),
            new_entries_today=3,
        ),
        entry_price=100,
        stop_distance=5,
        reward_risk=2.5,
    )

    assert RiskRejectionReason.MAX_DAILY_ENTRIES in decision.rejection_reasons


def test_sector_exposure_cap_rejects():
    decision = evaluate_portfolio_risk(
        candidate=Candidate(),
        portfolio=PortfolioSnapshot(
            simulated_equity=Decimal("100000"),
            available_cash=Decimal("100000"),
            sector_exposure={"Technology": Decimal("25000")},
        ),
        entry_price=100,
        stop_distance=5,
        reward_risk=2.5,
        sector="Technology",
    )

    assert decision.accepted is False
    assert RiskRejectionReason.MAX_SECTOR_EXPOSURE in decision.rejection_reasons
