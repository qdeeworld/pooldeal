# PoolDeal

PoolDeal remembers a jointly signed contribution obligation from an earlier team purchase and uses it in a genuinely fresh session to change the next exact split. For the validation scenario, member A previously covered an extra 25 cents, so the next one-dollar purchase changes from 50/50 to 25/75.

This repository began after the official build window opened on September 1, 2026. It is currently a bounded eligibility spike, not a finished submission.

## Memory call sites

Judges can inspect the full Sibyl integration in under two minutes:

- write: `src/pooldeal/memory.py`, `ObligationMemory.write`
- fresh-session recall: `src/pooldeal/memory.py`, `ObligationMemory.recall`
- correction/consumption: `src/pooldeal/memory.py`, `ObligationMemory.consume`
- deletion: `src/pooldeal/memory.py`, `ObligationMemory.delete`
- decision change: `src/pooldeal/allocation.py`, `allocate_with_obligation`

Only the signed structured fields affect allocation. Human notes are display-only. Missing, expired, unsigned, altered, consumed, or group-mismatched memory refuses a history-aware split.

## Local validation

```bash
python3 -m venv .venv
.venv/bin/pip install -e '.[dev]'
.venv/bin/python scripts/run_memory_gate.py
.venv/bin/pytest
cd contracts && forge test -vv
```

For the bounded integrated validation surface, provide two Base Sepolia-only prepared wallet keys through `POOLDEAL_MEMBER_A_KEY` and `POOLDEAL_MEMBER_B_KEY`, then run `.venv/bin/pooldeal-web`. The browser journey writes and recalls through separate CLI subprocesses. The live settlement endpoint is capped by `POOLDEAL_MAX_SETTLEMENTS` and must never receive production keys.

The memory gate launches session one and session two as different OS processes. Session two receives only the database path, authenticated group members, and obligation identifier; it does not receive the remembered amount or meaning. The ablation run uses the identical session-two request against an empty Sibyl store and must refuse.

## Public Base evidence

The bounded Base Sepolia spike is recorded in [`evidence/base-sepolia-2026-09-01.md`](evidence/base-sepolia-2026-09-01.md). It proves exact 25/75 settlement, obligation-digest consumption, unanimous cancellation, and contributor-claimed refunds with public receipts. It remains E2 founder-operated evidence until the same action is available through the public product.

## Safety boundary

Sibyl stores the social meaning of the obligation. It never stores private keys and never authorizes transfers, custody, cancellation, or refunds. Wallet signatures authenticate the obligation. The Base contract independently prevents digest replay and owns settlement/refund state.
