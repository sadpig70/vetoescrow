"""Input validation for VetoEscrow batches."""

from __future__ import annotations

from typing import Any

from .models import RISK_WEIGHT, RIGHT_PRIORITY, ValidationIssue


def has_errors(issues: list[ValidationIssue]) -> bool:
    return any(i.severity == "error" for i in issues)


def validate_batch(batch: dict[str, Any]) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    if not isinstance(batch, dict):
        return [ValidationIssue("BATCH_TYPE", "error", "batch must be an object")]
    decisions = batch.get("decisions", [])
    bids = batch.get("bids", [])
    if not isinstance(decisions, list):
        issues.append(ValidationIssue("DECISIONS_TYPE", "error", "decisions must be a list"))
        decisions = []
    if not isinstance(bids, list):
        issues.append(ValidationIssue("BIDS_TYPE", "error", "bids must be a list"))
        bids = []
    seen_decisions: set[str] = set()
    for index, event in enumerate(decisions):
        if not isinstance(event, dict):
            issues.append(ValidationIssue("DECISION_TYPE", "error", "decision must be an object", str(index)))
            continue
        rid = str(event.get("id") or event.get("decision_id") or f"decision-{index}")
        if rid in seen_decisions:
            issues.append(ValidationIssue("DUP_DECISION", "error", "duplicate decision id", rid))
        seen_decisions.add(rid)
        if str(event.get("risk_class", "medium")).lower() not in RISK_WEIGHT:
            issues.append(ValidationIssue("RISK_CLASS", "warning", "unknown risk_class defaults to medium", rid))
        for key in ("impact", "confidence", "stake"):
            try:
                float(event.get(key, 0.0))
            except (TypeError, ValueError):
                issues.append(ValidationIssue("NUMERIC_FIELD", "error", f"{key} must be numeric", rid))
    for index, event in enumerate(bids):
        if not isinstance(event, dict):
            issues.append(ValidationIssue("BID_TYPE", "error", "bid must be an object", str(index)))
            continue
        bid_id = str(event.get("id") or event.get("bid_id") or f"bid-{index}")
        decision_id = str(event.get("decision_id") or "")
        if decision_id and decision_id not in seen_decisions:
            issues.append(ValidationIssue("UNKNOWN_DECISION", "error", "bid references missing decision", bid_id))
        if str(event.get("right_type", "modify")).lower() not in RIGHT_PRIORITY:
            issues.append(ValidationIssue("RIGHT_TYPE", "error", "right_type must be modify or veto", bid_id))
    return issues
