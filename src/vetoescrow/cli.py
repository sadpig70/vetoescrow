"""VetoEscrow command line interface."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .audit import entry_from_dict, verify_ledger
from .market import render_markdown, run_clearing
from .validate import has_errors


def sample_batch() -> dict:
    return {
        "batch_id": "ve-demo-001",
        "gate_threshold": 0.62,
        "source": "agentops_gateway",
        "decisions": [
            {"id": "d1", "agent": "claims-agent", "action": "deny $42k claim", "risk_class": "critical", "impact": 92, "confidence": 0.61, "stake": 1200, "timestamp": "2026-06-10T09:00:00Z"},
            {"id": "d2", "agent": "ops-agent", "action": "reroute warehouse order", "risk_class": "medium", "impact": 35, "confidence": 0.82, "stake": 300, "timestamp": "2026-06-10T09:00:10Z"},
            {"id": "d3", "agent": "sec-agent", "action": "revoke vendor credential", "risk_class": "high", "impact": 80, "confidence": 0.58, "stake": 900, "timestamp": "2026-06-10T09:00:20Z"},
            {"id": "d4", "agent": "pricing-agent", "action": "raise regional price", "risk_class": "high", "impact": 55, "confidence": 0.77, "stake": 500, "timestamp": "2026-06-10T09:00:30Z"},
        ],
        "bids": [
            {"id": "b1", "decision_id": "d1", "supervisor": "legal-desk", "right_type": "veto", "max_price": 2100, "timestamp": "2026-06-10T09:01:00Z", "rationale": "claim denial requires human legal review"},
            {"id": "b2", "decision_id": "d3", "supervisor": "security-lead", "right_type": "modify", "max_price": 1300, "timestamp": "2026-06-10T09:01:05Z", "rationale": "scope credential revocation"},
            {"id": "b3", "decision_id": "d4", "supervisor": "revenue-ops", "right_type": "modify", "max_price": 50, "timestamp": "2026-06-10T09:01:10Z", "rationale": "too cheap, should not clear"},
        ],
        "metadata": {"schema_version": "vetoescrow.batch.v0.1"},
    }


def cmd_sample(args: argparse.Namespace) -> int:
    path = Path(args.output)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(sample_batch(), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {path}")
    return 0


def cmd_run(args: argparse.Namespace) -> int:
    batch = json.loads(Path(args.input).read_text(encoding="utf-8"))
    report = run_clearing(batch)
    if args.markdown:
        output = render_markdown(report)
    else:
        payload = report.to_dict() if args.full else report.summary_dict()
        output = json.dumps(payload, ensure_ascii=False, indent=2)
    if args.output:
        Path(args.output).parent.mkdir(parents=True, exist_ok=True)
        Path(args.output).write_text(output + "\n", encoding="utf-8")
        print(f"wrote {args.output}")
    else:
        print(output)
    return 1 if has_errors(report.issues) else 0


def cmd_verify_ledger(args: argparse.Namespace) -> int:
    data = json.loads(Path(args.input).read_text(encoding="utf-8"))
    entries = [entry_from_dict(e) for e in data.get("ledger", [])]
    genesis = data.get("batch_id", "GENESIS")
    issues = verify_ledger(entries, genesis=genesis)
    if issues:
        print(f"TAMPERED - {len(issues)} issue(s):")
        for issue in issues:
            print(f"  [{issue.severity}] {issue.code} {issue.message}")
        return 1
    print(f"intact - {len(entries)} ledger entries verify against head")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="vetoescrow", description="Interruptible clearing gate for high-risk AI decisions.")
    sub = parser.add_subparsers(dest="command", required=True)
    p_sample = sub.add_parser("sample", help="write a sample decision/bid batch")
    p_sample.add_argument("-o", "--output", default="examples/decision_batch.json")
    p_sample.set_defaults(func=cmd_sample)
    p_run = sub.add_parser("run", help="clear a decision/bid batch")
    p_run.add_argument("-i", "--input", required=True)
    p_run.add_argument("-o", "--output", default=None)
    p_run.add_argument("--full", action="store_true", help="include awards, ledger, and evidence")
    p_run.add_argument("--markdown", action="store_true", help="render a markdown report")
    p_run.set_defaults(func=cmd_run)
    p_verify = sub.add_parser("verify-ledger", help="verify a full JSON report ledger")
    p_verify.add_argument("-i", "--input", required=True)
    p_verify.set_defaults(func=cmd_verify_ledger)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
