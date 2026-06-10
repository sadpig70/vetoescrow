"""Hash-chained ledger for clearing outcomes."""

from __future__ import annotations

import hashlib
import json

from .models import ClearingAward, LedgerEntry, ValidationIssue

GENESIS = "GENESIS"


def _hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _payload(index: int, decision_id: str, outcome: str, supervisor: str,
             clearing_price: float, timestamp: str) -> str:
    return json.dumps(
        {
            "index": index,
            "decision_id": decision_id,
            "outcome": outcome,
            "supervisor": supervisor,
            "clearing_price": round(clearing_price, 6),
            "timestamp": timestamp,
        },
        sort_keys=True,
        ensure_ascii=False,
    )


def build_ledger(awards: list[ClearingAward], genesis: str = GENESIS) -> list[LedgerEntry]:
    entries: list[LedgerEntry] = []
    prev_hash = _hash(genesis)
    for index, award in enumerate(awards):
        payload = _payload(index, award.decision_id, award.outcome, award.supervisor,
                           award.clearing_price, award.timestamp)
        entry_hash = _hash(prev_hash + payload)
        entries.append(LedgerEntry(
            index=index,
            decision_id=award.decision_id,
            outcome=award.outcome,
            supervisor=award.supervisor,
            clearing_price=award.clearing_price,
            timestamp=award.timestamp,
            prev_hash=prev_hash,
            entry_hash=entry_hash,
        ))
        prev_hash = entry_hash
    return entries


def ledger_head(entries: list[LedgerEntry], genesis: str = GENESIS) -> str:
    return entries[-1].entry_hash if entries else _hash(genesis)


def verify_ledger(entries: list[LedgerEntry], genesis: str = GENESIS) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    prev_hash = _hash(genesis)
    for i, entry in enumerate(entries):
        if entry.index != i:
            issues.append(ValidationIssue("LEDGER_INDEX", "error", f"entry at {i} has index {entry.index}", entry.decision_id))
        if entry.prev_hash != prev_hash:
            issues.append(ValidationIssue("LEDGER_PREV", "error", f"entry {i} prev_hash does not chain", entry.decision_id))
        payload = _payload(entry.index, entry.decision_id, entry.outcome, entry.supervisor,
                           entry.clearing_price, entry.timestamp)
        expected = _hash(entry.prev_hash + payload)
        if entry.entry_hash != expected:
            issues.append(ValidationIssue("LEDGER_HASH", "error", f"entry {i} hash mismatch", entry.decision_id))
        prev_hash = entry.entry_hash
    return issues


def entry_from_dict(data: dict) -> LedgerEntry:
    return LedgerEntry(
        index=int(data["index"]),
        decision_id=str(data["decision_id"]),
        outcome=str(data["outcome"]),
        supervisor=str(data["supervisor"]),
        clearing_price=float(data["clearing_price"]),
        timestamp=str(data["timestamp"]),
        prev_hash=str(data["prev_hash"]),
        entry_hash=str(data["entry_hash"]),
    )
