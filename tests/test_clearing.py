from __future__ import annotations

from vetoescrow.clearing import clear, clearing_price, risk_score
from vetoescrow.models import DecisionIntent, SupervisorBid


def _decision(rid: str, risk: str = "high", impact: float = 80, confidence: float = 0.6, stake: float = 1000) -> DecisionIntent:
    return DecisionIntent(rid, "agent", "act", risk, impact, confidence, stake, "2026-06-10T00:00:00Z", "test")


def _bid(bid_id: str, decision_id: str, right: str, max_price: float, supervisor: str = "human") -> SupervisorBid:
    return SupervisorBid(bid_id, decision_id, supervisor, right, max_price, "2026-06-10T00:00:01Z")


def test_risk_score_is_bounded_and_critical_scores_higher():
    low = risk_score(_decision("a", "low", impact=10, confidence=0.95))
    critical = risk_score(_decision("b", "critical", impact=100, confidence=0.2))
    assert 0 <= low <= 1
    assert 0 <= critical <= 1
    assert critical > low


def test_low_risk_releases_without_price():
    award = clear([_decision("d1", "low", impact=10, confidence=0.95)], [], 0.62)[0]
    assert award.outcome == "released"
    assert award.clearing_price == 0


def test_locked_without_eligible_bid_is_held_unclaimed():
    d = _decision("d1")
    price = clearing_price(d, risk_score(d))
    award = clear([d], [_bid("b1", "d1", "modify", price - 0.01)], 0.62)[0]
    assert award.outcome == "held_unclaimed"
    assert award.winning_bid_id == ""


def test_veto_bid_beats_modify_at_same_price():
    d = _decision("d1")
    price = clearing_price(d, risk_score(d))
    bids = [_bid("b1", "d1", "modify", price + 10), _bid("b2", "d1", "veto", price + 10)]
    award = clear([d], bids, 0.62)[0]
    assert award.outcome == "veto_right_sold"
    assert award.winning_bid_id == "b2"


def test_higher_bid_breaks_same_right_tie():
    d = _decision("d1")
    price = clearing_price(d, risk_score(d))
    bids = [_bid("b1", "d1", "modify", price + 10), _bid("b2", "d1", "modify", price + 20)]
    award = clear([d], bids, 0.62)[0]
    assert award.winning_bid_id == "b2"


def test_every_decision_gets_one_award():
    decisions = [_decision("d1"), _decision("d2", "low", impact=5, confidence=0.9)]
    awards = clear(decisions, [], 0.62)
    assert [a.decision_id for a in awards] == ["d1", "d2"]
