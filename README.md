# EvidenceResolver

Reusable GenLayer Intelligent Contract for resolving binary claims against live web evidence.

## Purpose
Locks a claim + source URLs at deployment. On `resolve()` it fetches evidence, extracts a structured outcome, and finalizes only when validators independently agree on the decision fields (`satisfied` + `confidence`).

Useful for escrow, parametric payouts, bounty verification, etc.

## Consensus
- Leader fetches sources and extracts JSON via LLM.
- Validators re-fetch and re-extract independently.
- Accept only if `satisfied` and `confidence` match exactly.
- Free-text `details` can differ.

Uses `gl.vm.run_nondet_unsafe`.

## Files
- `contracts/EvidenceResolver.py` — the contract
- Deploy with: claim (str), source_urls_json (JSON list string)
