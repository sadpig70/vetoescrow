# PROJECT REPORT - VetoEscrow

## Origin

- Source idea: `IDEA-014` - Interruptible Clearing Gate
- Source pool: `CIX-20260609-001`
- Evaluation: `EVX-20260610-001`
- Lens stack: `L22_SequenceReorder` + `L2_PowerInversion`
- Mechanism: clearing-market

## Product Shape

VetoEscrow is the smallest runnable form of the idea: a batch clearing engine that
locks high-risk AI decisions and sells human `modify` or `veto` rights when a
supervisor bid clears the interruption price.

## Derivative Check

Existing siblings cover time-box reauthorization (`slotgate`), roaming jurisdiction
registration (`orbiroam`), and strategic reserve flow markets (`reserveflow`).
VetoEscrow is distinct because its primitive is not time, jurisdiction, or commodity
capacity. The primitive is a priced human interruption right over an individual AI
decision.

Risk noted: the current pool is clearing-market heavy. This project is intentionally
kept as one narrow clearing-gate materialization before steering away from this mechanism.

## Verification

The intended local verification path:

```bash
python -m pytest -q
python -m vetoescrow sample -o examples/decision_batch.json
python -m vetoescrow run -i examples/decision_batch.json --full -o examples/clearing_report.json
python -m vetoescrow verify-ledger -i examples/clearing_report.json
```

## R1-R3 Mitigation

- R1 regulatory confusion: README and reports state the output is not a real exchange,
  broker-dealer, insurer, settlement venue, or legal veto.
- R2 false safety: the MVP emits an audit recommendation only; it does not enforce live
  access control.
- R3 mechanism homogenization: project naming and scope avoid another `*mesh`; next
  IdeaFirst round should mark clearing-market saturation as overused.

## Next Steps

- Add policy-specific risk tables for healthcare, finance, and security operations.
- Add signed external attestations for supervisor bids.
- Add a service adapter only after the batch invariants are stable.
