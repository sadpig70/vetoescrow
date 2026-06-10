from __future__ import annotations

from vetoescrow.audit import build_ledger, entry_from_dict, ledger_head, verify_ledger
from vetoescrow.clearing import clear
from vetoescrow.models import DecisionIntent, SupervisorBid


def _awards():
    d = DecisionIntent("d1", "agent", "act", "high", 80, 0.6, 1000, "2026-06-10T00:00:00Z", "test")
    b = SupervisorBid("b1", "d1", "human", "veto", 9999, "2026-06-10T00:00:01Z")
    return clear([d], [b], 0.62)


def test_ledger_verifies_intact():
    entries = build_ledger(_awards(), genesis="batch")
    assert verify_ledger(entries, genesis="batch") == []
    assert ledger_head(entries, genesis="batch") == entries[-1].entry_hash


def test_ledger_detects_price_tamper():
    entries = build_ledger(_awards(), genesis="batch")
    data = entries[0].to_dict()
    data["clearing_price"] = data["clearing_price"] + 1
    tampered = [entry_from_dict(data)]
    issues = verify_ledger(tampered, genesis="batch")
    assert any(i.code == "LEDGER_HASH" for i in issues)


def test_ledger_detects_prev_hash_break():
    entries = build_ledger(_awards(), genesis="batch")
    data = entries[0].to_dict()
    data["prev_hash"] = "bad"
    issues = verify_ledger([entry_from_dict(data)], genesis="batch")
    assert any(i.code == "LEDGER_PREV" for i in issues)
