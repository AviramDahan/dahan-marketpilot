import pytest

from marketpilot.order_lifecycle import OrderLifecycleState, transition_order_state


def test_valid_lifecycle_transitions_return_audit_event():
    event = transition_order_state(
        idempotency_key="key",
        previous_state=OrderLifecycleState.PLANNED,
        next_state=OrderLifecycleState.SUBMITTED,
        reason="accepted by risk gate",
        payload={"token": "do-not-leak", "quantity": 10},
    )

    assert event.previous_state is OrderLifecycleState.PLANNED
    assert event.next_state is OrderLifecycleState.SUBMITTED
    assert event.payload["token"] == "[redacted]"


@pytest.mark.parametrize(
    ("previous", "next_"),
    [
        (OrderLifecycleState.SUBMITTED, OrderLifecycleState.PARTIALLY_FILLED),
        (OrderLifecycleState.SUBMITTED, OrderLifecycleState.FILLED),
        (OrderLifecycleState.FILLED, OrderLifecycleState.PROTECTIVE_ORDERS_PENDING),
        (OrderLifecycleState.PROTECTIVE_ORDERS_PENDING, OrderLifecycleState.OPEN),
        (OrderLifecycleState.OPEN, OrderLifecycleState.PARTIALLY_CLOSED),
        (OrderLifecycleState.PARTIALLY_CLOSED, OrderLifecycleState.CLOSED),
    ],
)
def test_allowed_transitions(previous, next_):
    event = transition_order_state(idempotency_key="key", previous_state=previous, next_state=next_, reason="test")

    assert event.next_state is next_


@pytest.mark.parametrize(
    ("previous", "next_"),
    [
        (OrderLifecycleState.CLOSED, OrderLifecycleState.OPEN),
        (OrderLifecycleState.REJECTED, OrderLifecycleState.FILLED),
        (OrderLifecycleState.CANCELED, OrderLifecycleState.FILLED),
    ],
)
def test_forbidden_transitions_raise(previous, next_):
    with pytest.raises(ValueError, match="cannot transition"):
        transition_order_state(idempotency_key="key", previous_state=previous, next_state=next_, reason="bad")
