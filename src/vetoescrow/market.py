"""Pipeline: validate -> normalize -> clear -> audit -> report."""

from __future__ import annotations

from collections import Counter
from typing import Any

from .adapters import normalize_bid, normalize_decision
from .audit import build_ledger, ledger_head, verify_ledger
from .clearing import clear
from .models import EvidenceItem, EscrowReport, RISK_WEIGHT, RIGHT_PRIORITY
from .validate import validate_batch


def _evidence(gate_threshold: float) -> list[EvidenceItem]:
    rows = [EvidenceItem("gate.threshold", gate_threshold, "risk_score", "minimum score that locks a decision")]
    rows.extend(EvidenceItem(f"risk.{k}.weight", v, "weight", f"risk weight for {k}") for k, v in RISK_WEIGHT.items())
    rows.extend(EvidenceItem(f"right.{k}.priority", v, "priority", f"clearing priority for {k} right") for k, v in RIGHT_PRIORITY.items())
    return rows


def run_clearing(batch: dict[str, Any]) -> EscrowReport:
    batch_id = str(batch.get("batch_id", "vetoescrow-batch"))
    gate_threshold = float(batch.get("gate_threshold", 0.62))
    issues = validate_batch(batch)
    decisions_raw = batch.get("decisions", []) if isinstance(batch.get("decisions", []), list) else []
    bids_raw = batch.get("bids", []) if isinstance(batch.get("bids", []), list) else []
    source = str(batch.get("source", "decision_gateway"))
    decisions = [normalize_decision(e, source, i) for i, e in enumerate(decisions_raw) if isinstance(e, dict)]
    bids = [normalize_bid(e, i) for i, e in enumerate(bids_raw) if isinstance(e, dict)]
    awards = clear(decisions, bids, gate_threshold=gate_threshold)
    ledger = build_ledger(awards, genesis=batch_id)
    issues.extend(verify_ledger(ledger, genesis=batch_id))
    counts = dict(Counter(a.outcome for a in awards))
    locked = sum(1 for a in awards if a.outcome != "released")
    total = sum(a.clearing_price for a in awards if a.outcome.endswith("_sold"))
    return EscrowReport(
        batch_id=batch_id,
        gate_threshold=gate_threshold,
        decision_count=len(decisions),
        bid_count=len(bids),
        locked_count=locked,
        released_count=counts.get("released", 0),
        count_by_outcome={k: counts.get(k, 0) for k in ("released", "held_unclaimed", "modify_right_sold", "veto_right_sold")},
        total_clearing_price=total,
        ledger_head=ledger_head(ledger, genesis=batch_id),
        awards=awards,
        ledger=ledger,
        evidence=_evidence(gate_threshold),
        issues=issues,
    )


def render_markdown(report: EscrowReport) -> str:
    lines: list[str] = []
    lines.append(f"# VetoEscrow Clearing Report — `{report.batch_id}`")
    lines.append("")
    lines.append(f"- Decisions: **{report.decision_count}**  |  Bids: **{report.bid_count}**  |  Gate threshold: **{report.gate_threshold:.2f}**")
    lines.append(f"- Locked decisions: **{report.locked_count}**  |  Released: **{report.released_count}**")
    lines.append(f"- Total interruption price: **{report.total_clearing_price:.4f}**")
    lines.append(f"- Ledger head: `{report.ledger_head}`")
    lines.append("")
    lines.append("## Outcomes")
    lines.append("")
    lines.append("| Outcome | Count |")
    lines.append("|---|---:|")
    for key in ("released", "held_unclaimed", "modify_right_sold", "veto_right_sold"):
        lines.append(f"| {key} | {report.count_by_outcome.get(key, 0)} |")
    lines.append("")
    lines.append("## Awards")
    lines.append("")
    lines.append("| Decision | Risk | Price | Right | Supervisor | Outcome |")
    lines.append("|---|---:|---:|---|---|---|")
    for a in report.awards:
        lines.append(f"| {a.decision_id} | {a.risk_score:.3f} | {a.clearing_price:.2f} | {a.right_type or '-'} | {a.supervisor or '-'} | {a.outcome} |")
    lines.append("")
    errors = [i for i in report.issues if i.severity == "error"]
    lines.append(f"## Integrity: {'TAMPERED' if errors else 'intact'}")
    lines.append("")
    if report.issues:
        for issue in report.issues:
            lines.append(f"- [{issue.severity}] `{issue.code}` {issue.message}")
    else:
        lines.append("- No validation issues; ledger verifies intact.")
    lines.append("")
    lines.append("> Indicative AI-control clearing and evidence trail, not a legal exchange, broker-dealer, insurer, or production access-control system.")
    lines.append("")
    return "\n".join(lines)
