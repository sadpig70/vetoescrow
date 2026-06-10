# VERIFY - VetoEscrow

## Commands

```text
python -m pytest -q
=> 19 passed in 0.19s

$env:PYTHONPATH='src'
python -m vetoescrow sample -o examples/decision_batch.json
=> wrote examples\decision_batch.json

python -m vetoescrow run -i examples/decision_batch.json --full -o examples/clearing_report.json
=> wrote examples/clearing_report.json

python -m vetoescrow run -i examples/decision_batch.json --markdown -o examples/clearing_report.md
=> wrote examples/clearing_report.md

python -m vetoescrow verify-ledger -i examples/clearing_report.json
=> intact - 4 ledger entries verify against head

[xml]$doc = Get-Content -Raw -LiteralPath assets\VetoEscrow_infographic.svg
=> svg ok
```

## Acceptance

- Every decision yields exactly one clearing award.
- Low-risk decisions release without price.
- High-risk decisions lock; underpriced bids do not clear.
- Veto rights outrank modify rights at equal price.
- Hash-chain ledger verifies intact and detects tampering.
- CLI smoke covers sample, run, markdown, and verify-ledger.

## Architecture

DESIGN modules map directly to `src/vetoescrow`: `models`, `adapters`,
`clearing`, `audit`, `validate`, `market`, and `cli`.

## Verdict

Passed. Runtime is stdlib-only and deterministic from input timestamps. CLI smoke
requires either editable install or `PYTHONPATH=src` when run directly from the source tree.
