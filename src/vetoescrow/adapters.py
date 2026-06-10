"""Source adapters for decision and supervisor-bid events."""

from __future__ import annotations

from typing import Any

from .models import DecisionIntent, SupervisorBid


def _num(data: dict[str, Any], key: str, default: float) -> float:
    try:
        return float(data.get(key, default))
    except (TypeError, ValueError):
        return default


def normalize_decision(event: dict[str, Any], source: str, index: int) -> DecisionIntent:
    """Normalize one raw AI decision into the clearing schema."""
    return DecisionIntent(
        record_id=str(event.get("id") or event.get("decision_id") or f"decision-{index}"),
        agent=str(event.get("agent") or "unknown-agent"),
        action=str(event.get("action") or event.get("decision") or "unspecified action"),
        risk_class=str(event.get("risk_class") or "medium").lower(),
        impact=max(0.0, _num(event, "impact", 1.0)),
        confidence=min(1.0, max(0.0, _num(event, "confidence", 0.5))),
        stake=max(0.0, _num(event, "stake", 100.0)),
        timestamp=str(event.get("timestamp") or ""),
        source=source,
    )


def normalize_bid(event: dict[str, Any], index: int) -> SupervisorBid:
    """Normalize one human supervision bid."""
    return SupervisorBid(
        bid_id=str(event.get("id") or event.get("bid_id") or f"bid-{index}"),
        decision_id=str(event.get("decision_id") or ""),
        supervisor=str(event.get("supervisor") or "unknown-supervisor"),
        right_type=str(event.get("right_type") or "modify").lower(),
        max_price=max(0.0, _num(event, "max_price", 0.0)),
        timestamp=str(event.get("timestamp") or ""),
        rationale=str(event.get("rationale") or ""),
    )
