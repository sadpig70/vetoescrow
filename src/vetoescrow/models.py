"""Frozen domain models for the VetoEscrow clearing pipeline."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

RiskClass = Literal["low", "medium", "high", "critical"]
RightType = Literal["modify", "veto"]
Outcome = Literal["released", "held_unclaimed", "modify_right_sold", "veto_right_sold"]

RISK_WEIGHT: dict[str, float] = {
    "low": 0.20,
    "medium": 0.55,
    "high": 0.82,
    "critical": 1.00,
}

RIGHT_PRIORITY: dict[str, int] = {"veto": 2, "modify": 1}


@dataclass(frozen=True)
class ValidationIssue:
    code: str
    severity: str
    message: str
    record_id: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "code": self.code,
            "severity": self.severity,
            "message": self.message,
            "record_id": self.record_id,
        }


@dataclass(frozen=True)
class EvidenceItem:
    key: str
    value: float | str
    unit: str
    note: str

    def to_dict(self) -> dict[str, Any]:
        return {"key": self.key, "value": self.value, "unit": self.unit, "note": self.note}


@dataclass(frozen=True)
class DecisionIntent:
    record_id: str
    agent: str
    action: str
    risk_class: str
    impact: float
    confidence: float
    stake: float
    timestamp: str
    source: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "record_id": self.record_id,
            "agent": self.agent,
            "action": self.action,
            "risk_class": self.risk_class,
            "impact": self.impact,
            "confidence": self.confidence,
            "stake": self.stake,
            "timestamp": self.timestamp,
            "source": self.source,
        }


@dataclass(frozen=True)
class SupervisorBid:
    bid_id: str
    decision_id: str
    supervisor: str
    right_type: str
    max_price: float
    timestamp: str
    rationale: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "bid_id": self.bid_id,
            "decision_id": self.decision_id,
            "supervisor": self.supervisor,
            "right_type": self.right_type,
            "max_price": self.max_price,
            "timestamp": self.timestamp,
            "rationale": self.rationale,
        }


@dataclass(frozen=True)
class ClearingAward:
    decision_id: str
    agent: str
    action: str
    risk_score: float
    clearing_price: float
    winning_bid_id: str
    supervisor: str
    right_type: str
    outcome: str
    timestamp: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "decision_id": self.decision_id,
            "agent": self.agent,
            "action": self.action,
            "risk_score": self.risk_score,
            "clearing_price": self.clearing_price,
            "winning_bid_id": self.winning_bid_id,
            "supervisor": self.supervisor,
            "right_type": self.right_type,
            "outcome": self.outcome,
            "timestamp": self.timestamp,
        }


@dataclass(frozen=True)
class LedgerEntry:
    index: int
    decision_id: str
    outcome: str
    supervisor: str
    clearing_price: float
    timestamp: str
    prev_hash: str
    entry_hash: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "index": self.index,
            "decision_id": self.decision_id,
            "outcome": self.outcome,
            "supervisor": self.supervisor,
            "clearing_price": self.clearing_price,
            "timestamp": self.timestamp,
            "prev_hash": self.prev_hash,
            "entry_hash": self.entry_hash,
        }


@dataclass(frozen=True)
class EscrowReport:
    batch_id: str
    gate_threshold: float
    decision_count: int
    bid_count: int
    locked_count: int
    released_count: int
    count_by_outcome: dict[str, int]
    total_clearing_price: float
    ledger_head: str
    awards: list[ClearingAward]
    ledger: list[LedgerEntry]
    evidence: list[EvidenceItem]
    issues: list[ValidationIssue]

    def summary_dict(self) -> dict[str, Any]:
        return {
            "batch_id": self.batch_id,
            "gate_threshold": self.gate_threshold,
            "decision_count": self.decision_count,
            "bid_count": self.bid_count,
            "locked_count": self.locked_count,
            "released_count": self.released_count,
            "count_by_outcome": self.count_by_outcome,
            "total_clearing_price": round(self.total_clearing_price, 6),
            "ledger_head": self.ledger_head,
            "issues": [i.to_dict() for i in self.issues],
        }

    def to_dict(self) -> dict[str, Any]:
        data = self.summary_dict()
        data.update({
            "awards": [a.to_dict() for a in self.awards],
            "ledger": [e.to_dict() for e in self.ledger],
            "evidence": [e.to_dict() for e in self.evidence],
        })
        return data
