# Audit Journal

Phase 6 uses an append-only JSONL audit journal for local trace and recovery
context. It records intents, decisions, lifecycle events, config version
placeholders, strategy version placeholders, timestamps, correlation IDs, and
sanitized payloads.

The audit journal is not an authoritative portfolio database. QuantConnect
remains authoritative for Paper cash, holdings, orders, fills, and positions.
