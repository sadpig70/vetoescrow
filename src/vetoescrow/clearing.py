"""Interruptible clearing gate logic."""

from __future__ import annotations

from .models import RISK_WEIGHT, RIGHT_PRIORITY, ClearingAward, DecisionIntent, SupervisorBid


def risk_score(decision: DecisionIntent) -> float:
    """Risk score in [0, 1], combining class weight, impact, and uncertainty."""
    base = RISK_WEIGHT.get(decision.risk_class, RISK_WEIGHT["medium"])
    impact_component = min(1.0, decision.impact / 100.0)
    uncertainty = 1.0 - decision.confidence
    return round(min(1.0, (base * 0.62) + (impact_component * 0.25) + (uncertainty * 0.13)), 6)


def clearing_price(decision: DecisionIntent, score: float) -> float:
    """Price a human interruption right from the agent's autonomy stake."""
    uncertainty = 1.0 - decision.confidence
    price = decision.stake * (0.35 + score) * (1.0 + uncertainty * 0.4)
    return round(price, 6)


def _best_bid(decision_id: str, price: float, bids: list[SupervisorBid]) -> SupervisorBid | None:
    eligible = [b for b in bids if b.decision_id == decision_id and b.max_price >= price]
    if not eligible:
        return None
    return sorted(
        eligible,
        key=lambda b: (-RIGHT_PRIORITY.get(b.right_type, 0), -b.max_price, b.timestamp, b.bid_id),
    )[0]


def clear(decisions: list[DecisionIntent], bids: list[SupervisorBid], gate_threshold: float) -> list[ClearingAward]:
    """Clear decisions into released, held, modify-right, or veto-right outcomes.

    Deterministic: sorting uses input timestamps and IDs only. Every decision yields
    exactly one award. A human bid must meet the computed price to interrupt.
    """
    awards: list[ClearingAward] = []
    for decision in sorted(decisions, key=lambda d: (d.timestamp, d.record_id)):
        score = risk_score(decision)
        price = clearing_price(decision, score)
        if score < gate_threshold:
            awards.append(ClearingAward(
                decision.record_id, decision.agent, decision.action, score, 0.0, "",
                "", "", "released", decision.timestamp,
            ))
            continue
        bid = _best_bid(decision.record_id, price, bids)
        if bid is None:
            awards.append(ClearingAward(
                decision.record_id, decision.agent, decision.action, score, price, "",
                "", "", "held_unclaimed", decision.timestamp,
            ))
            continue
        outcome = "veto_right_sold" if bid.right_type == "veto" else "modify_right_sold"
        awards.append(ClearingAward(
            decision.record_id, decision.agent, decision.action, score, price, bid.bid_id,
            bid.supervisor, bid.right_type, outcome, max(decision.timestamp, bid.timestamp),
        ))
    return awards
