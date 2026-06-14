from datetime import datetime, timezone

import pytest

from marketpilot.audit_journal import AppendOnlyJsonlAuditJournal, AuditJournalRecord


def test_audit_journal_appends_jsonl_records_in_order(tmp_path):
    journal = AppendOnlyJsonlAuditJournal(tmp_path / "audit.jsonl")
    journal.append(AuditJournalRecord("risk_decision", datetime(2026, 6, 14, tzinfo=timezone.utc), "a", {"quantity": 10}))
    journal.append(AuditJournalRecord("order_intent", datetime(2026, 6, 14, tzinfo=timezone.utc), "b", {"token": "secret"}))

    records = journal.read_records()

    assert [record["event_type"] for record in records] == ["risk_decision", "order_intent"]
    assert records[1]["payload"]["token"] == "[redacted]"


def test_audit_journal_rejects_invalid_record(tmp_path):
    journal = AppendOnlyJsonlAuditJournal(tmp_path / "audit.jsonl")

    with pytest.raises(ValueError, match="event_type"):
        journal.append(AuditJournalRecord("", datetime(2026, 6, 14, tzinfo=timezone.utc), "a", {}))
