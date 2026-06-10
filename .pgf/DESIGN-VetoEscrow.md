# DESIGN - VetoEscrow

> Interruptible Clearing Gate - beachhead implementation.
> Source idea: `IDEA-014` (CIX-20260609-001 -> EVX-20260610-001, consensus rank after consumed winners).
> Lens stack: `L22_SequenceReorder` + `L2_PowerInversion`. Mechanism: clearing-market.

## Problem

High-risk AI actions often pass through either binary automation or vague human review.
That makes oversight a UX burden instead of a priced control surface. VetoEscrow turns
each risky AI decision into an escrowed autonomy claim: if the risk is high enough,
the decision is locked and human supervisors can buy a deterministic `modify` or
`veto` right before the action is released.

## Mechanism

| Lens | Move | In VetoEscrow |
|---|---|---|
| L22 SequenceReorder | reorder when action can happen | action becomes locked before release when risk crosses the threshold |
| L2 PowerInversion | force AI autonomy to pay for interruption | AI decisions carry an autonomy stake; humans can clear veto/modify rights against it |
| clearing-market | match scarce review attention to priced risk | bids clear only when they meet the computed interruption price |

Output is an indicative control/audit layer, not a real financial exchange or legal veto venue.

## Scope

Beachhead = batch decision book + supervisor bids -> risk score -> clearing price ->
outcome (`released`, `held_unclaimed`, `modify_right_sold`, `veto_right_sold`) ->
hash-chained ledger + markdown/JSON export. Stdlib only, deterministic from input timestamps.

## Gantree

```text
VetoEscrow // interruptible clearing gate for AI decisions (in-progress) @v:0.1
    Models // frozen decision, bid, award, report, ledger schemas (designing)
    Adapters // raw decision/bid events -> canonical records (designing)
    Clearing // risk score + interruption price + bid clearing (designing)
    Audit // hash-chained evidence ledger + tamper detection (designing)
    Validate // input validation and issue reporting (designing)
    Market // validate -> normalize -> clear -> audit -> report (designing)
    CLI // sample / run / verify-ledger commands (designing)
    Tests // pytest acceptance and invariants (designing)
    Docs // README, report, examples, SVG, CI (designing)
```

## PPR

```python
def risk_score(decision: DecisionIntent) -> float:
    # input: risk_class, impact, confidence
    # process: weighted risk + impact + uncertainty, clamped to [0,1]
    # criteria: critical > low; deterministic; no current-time dependency

def clear(decisions: list[DecisionIntent], bids: list[SupervisorBid], gate_threshold: float) -> list[ClearingAward]:
    # process:
    #   for decision sorted by timestamp/id:
    #       score = risk_score(decision)
    #       if score < threshold: outcome = released
    #       else price = clearing_price(decision, score)
    #       best bid = eligible max_price >= price sorted by veto priority, bid price, timestamp, id
    #       no eligible bid -> held_unclaimed
    #       eligible bid -> modify_right_sold or veto_right_sold
    # criteria:
    #   - every decision yields exactly one award
    #   - veto beats modify at equal price
    #   - underpriced bids never clear
    #   - same input -> same output

def run_clearing(batch: dict) -> EscrowReport:
    raw -> validate_batch -> normalize_decision/bid -> clear -> build_ledger -> report
    # acceptance_criteria:
    #   - report summary is JSON-serializable
    #   - ledger verifies intact and detects tampering
    #   - CLI sample/run/verify-ledger passes
```

## Acceptance Criteria

- `python -m vetoescrow sample -o examples/decision_batch.json` writes a valid batch.
- `python -m vetoescrow run -i examples/decision_batch.json --full` emits awards, evidence, and ledger.
- `python -m vetoescrow verify-ledger -i <report>` returns 0 for intact and 1 for tampered reports.
- `python -m pytest -q` passes.
- `dependencies = []`; all runtime behavior is deterministic from input fields.

## Non-Goals

- No production access-control enforcement, broker-dealer logic, legal settlement, network service, DB, or live authorization.
- No claim that clearing output is legally binding. It is an auditable control recommendation.
