from __future__ import annotations

import json

from vetoescrow.audit import verify_ledger
from vetoescrow.cli import main, sample_batch
from vetoescrow.market import render_markdown, run_clearing


def test_sample_batch_covers_all_outcomes():
    report = run_clearing(sample_batch())
    assert report.decision_count == 4
    assert report.count_by_outcome["released"] >= 1
    assert report.count_by_outcome["held_unclaimed"] >= 1
    assert report.count_by_outcome["modify_right_sold"] >= 1
    assert report.count_by_outcome["veto_right_sold"] >= 1


def test_report_is_deterministic():
    first = json.dumps(run_clearing(sample_batch()).to_dict(), sort_keys=True)
    second = json.dumps(run_clearing(sample_batch()).to_dict(), sort_keys=True)
    assert first == second


def test_report_summary_json_serializable():
    json.dumps(run_clearing(sample_batch()).summary_dict())


def test_ledger_verifies_from_report():
    report = run_clearing(sample_batch())
    assert verify_ledger(report.ledger, genesis=report.batch_id) == []


def test_markdown_renders_core_sections():
    md = render_markdown(run_clearing(sample_batch()))
    assert "# VetoEscrow Clearing Report" in md
    assert "## Outcomes" in md
    assert "Integrity:" in md


def test_cli_sample_run_verify(tmp_path):
    batch = tmp_path / "batch.json"
    report = tmp_path / "report.json"
    assert main(["sample", "-o", str(batch)]) == 0
    assert main(["run", "-i", str(batch), "--full", "-o", str(report)]) == 0
    assert main(["verify-ledger", "-i", str(report)]) == 0


def test_cli_verify_detects_tamper(tmp_path):
    batch = tmp_path / "batch.json"
    report = tmp_path / "report.json"
    main(["sample", "-o", str(batch)])
    main(["run", "-i", str(batch), "--full", "-o", str(report)])
    data = json.loads(report.read_text(encoding="utf-8"))
    data["ledger"][0]["outcome"] = "released"
    report.write_text(json.dumps(data), encoding="utf-8")
    assert main(["verify-ledger", "-i", str(report)]) == 1
