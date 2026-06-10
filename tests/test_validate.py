from __future__ import annotations

from vetoescrow.validate import has_errors, validate_batch


def test_validate_rejects_missing_decision_reference():
    issues = validate_batch({"decisions": [], "bids": [{"id": "b1", "decision_id": "x", "right_type": "veto"}]})
    assert has_errors(issues)
    assert any(i.code == "UNKNOWN_DECISION" for i in issues)


def test_validate_warns_unknown_risk_class():
    issues = validate_batch({"decisions": [{"id": "d1", "risk_class": "weird", "impact": 1, "confidence": 1, "stake": 1}], "bids": []})
    assert not has_errors(issues)
    assert any(i.code == "RISK_CLASS" for i in issues)


def test_validate_rejects_bad_right_type():
    issues = validate_batch({
        "decisions": [{"id": "d1", "risk_class": "high", "impact": 1, "confidence": 1, "stake": 1}],
        "bids": [{"id": "b1", "decision_id": "d1", "right_type": "pause"}],
    })
    assert any(i.code == "RIGHT_TYPE" for i in issues)
