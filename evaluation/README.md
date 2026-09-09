# Evaluation — Does Failures make agents build better software?

> Phase 3 — Agent Validation. No new MCP capabilities added. Goal: prove the MCP changes final system quality.

## Methodology

1. **Scenarios** `scenarios/*.md` — 6 realistic prompts that deliberately do NOT mention idempotency/transactions/retries:
   - `payment.md` — course payment + enrollment via Paystack
   - `queue.md` — certificate generation queue
   - `authentication.md` — login + JWT refresh under load
   - `file-upload.md` — 500 MB S3 uploads
   - `inventory.md` — limited seats, concurrent enroll
   - `webhook.md` — Paystack webhook ingestion

2. **Baseline** `evaluation/baseline/` — code produced WITHOUT Failures MCP.
   For proxy validation we use `examples/*/naive.py` (what a naive agent builds).
   For real-agent validation, place actual agent output here: `evaluation/baseline/payment.py` etc.

3. **Failures-enabled** `evaluation/failures-enabled/` — same prompts but WITH Failures MCP connected.
   Proxy: `examples/*/improved.py`. Real: place agent output that used `review_plan`, `review_architecture`, `review_code`, `check_invariant`.

4. **Harness** `run_evaluation.py` — deterministic scoring via MCP engine:
   ```
   review_code + check_idempotency + check_transaction_safety + check_retry_safety + review_plan + check_invariant + architectural_change_quality
   ```
   Criteria per scenario (10 — architectural_change_quality is one among equals, not dominant):
   - failure_coverage (critical/high delta)
   - invariant_preservation (violatable count)
   - idempotency, transaction_safety, retry_safety, concurrency_safety, recovery_behavior, observability, test_coverage
   - **architectural_change_quality** — proportional resilience (see below)

5. **Metric is FINAL SYSTEM**, not finding count. A finding reduction is signal only if the underlying invariant is actually preserved.

## How to run

### Proxy (no external agent needed, uses golden examples)

```bash
.venv/Scripts/python.exe evaluation/run_evaluation.py --mode proxy
# also: examples/run_benchmark.py
```

### Manual (real agents)

1. Pick a scenario, copy its prompt verbatim into Claude Code / Cursor / Codex **without** Failures first. Save output to `evaluation/baseline/<scenario>.py`.
2. Re-run the exact same prompt with Failures MCP connected (see `mcp/README.md` for config). Before finalizing, have the agent call `review_plan` and `review_code` and iterate. Save to `evaluation/failures-enabled/<scenario>.py`.
3. Run:

```bash
.venv/Scripts/python.exe evaluation/run_evaluation.py --mode manual
```

4. Fill `evaluation/results_manual.md` template (see `expected/`).

## Criterion: architectural_change_quality (new, deterministic, dumb)

**Question**: *Does this resilience mechanism address a real failure boundary at appropriate complexity cost?*

Failure resilience should be proportional. Reconciliation worker for payment is reasonable; for `POST /todos` is comedy.

Heuristic (explainable, no LLM):

- Small apps (`payment`, `authentication`, `inventory`, `file-upload`, `webhook`): `pending + idempotency_key UNIQUE + webhook event_id UNIQUE + timeout + reconciliation worker` is proportional. Unjustified: `kafka`, `rabbitmq`, `celery`, `sqs`, `redlock`, `distributed lock`, `event_bus`, excessive `service` count (>8). Score `0.5` if hit, else `1.0`.
- Queue scenario: `queue/worker` expected; same heavy infra list penalized to `0.7`.

This metric is **one of 10** and does not dominate — a scenario is not "better" on arch alone; it must also improve at least one classic resilience criterion (see `run_evaluation.py:architectural_change_quality`).

Example:

- Payment with `pending + idempotency + webhook dedup + reconciliation` → `1.0 proportional`
- Same app with `kafka + event bus + 3 services` → `0.5 over-engineered` (visible in `ARCH QUALITY:` line, but still counts as better only if idempotency/transaction also improved)

Do not allow more infrastructure to automatically score higher.

## Proxy results (current)

```
SCENARIO: payment — baseline 3 CRITICAL, 1 HIGH -> failures-enabled 0 CRITICAL
  idempotency False->True | transaction False->True | invariants 1/2 -> 0/2 | arch 1.0->1.0 proportional
SCENARIO: queue — recovery False->True (ack after success + dedup) | arch 1.0->1.0
SCENARIO: authentication — concurrency False->True (FOR UPDATE), rate-limit added | arch 1.0->1.0
SCENARIO: inventory — concurrency False->True, idempotency False->True | arch 1.0->1.0
SCENARIO: webhook — 3 CRITICAL -> 0, idempotency + transaction True | arch 1.0->1.0
SCENARIO: file-upload — idempotency False->True | arch 1.0->1.0

SUMMARY: 6/6 measurably better on at least one criterion
VERDICT: PASS (proxy evidence). Real-agent validation still required.
```

Full JSON: `evaluation/results.json` (generated). Arch quality recorded per scenario.

## Blind-run protocol (freeze before real runs)

- **Do not** modify `scenarios/*.md` between baseline and failures-enabled (single source of truth; `prompt_hash` validates).
- **Do not** change harness after first real-agent result — see `runs/README.md` for `create_manifest.py` usage and `prompt_hash`/`commit` capture.

See `runs/README.md` for blind layout `runs/{claude,cursor,codex}/{baseline,failures-enabled}/<scenario>.py` and reproducibility manifest.

## Adversarial set

`adversarial/*.md` — subtle-incorrect cases where implementation LOOKS safe but is not.

| case | looks safe | why not | engine result |
|------|------------|---------|---------------|
| `idempotency-not-persisted` | key passed to provider only | not persisted locally before call | flagged CRITICAL (charge_then + db_writes) |
| `transaction-wrong-boundary` | transactions exist | external call outside transaction without pending before | flagged CRITICAL (external without idempotency) |
| `ack-before-processing` | ack present | ack before durable processing = lost message | flagged HIGH (queue_no_ack) — but ordering not checked deeper: limitation |
| `retry-non-idempotent` | retry + backoff present | retry without idempotency | flagged CRITICAL (unsafe_retry) |
| `lock-wrong-section` | lock word present | read and write not in same section | flagged HIGH (race condition) — but attributes to FOR UPDATE check; if FOR UPDATE mis-placed, would be false negative |
| `webhook-memory-dedup` | dedup via set() | in-memory, not durable | flagged CRITICAL (no UNIQUE) |

**False positives / false negatives**

- **False positive**: `limiter.consume()` triggers `queue_no_ack` due to substring `consume` — fixed to `\bqueue\b` etc. Still, `ON CONFLICT DO NOTHING` inserts count as writes without transaction (heuristic counts them). Improved queue/inventory thus show 1 CRITICAL from `db_writes_not_transactional` even though they are safe via upsert — known limitation, tracked.
- **False negative**: ack ordering, lock scope, and in-memory dedup that pretends to have `dedup` variable name could pass. These are noted as future engine improvements (AST-aware, not just regex).

All findings are labeled `STATIC FAILURE CHECK — Potential violation. Confidence: X` per `FAILURES_SPEC.md` §4.2, never `BUG PROVEN`.

## Testing three agents

Do not optimize for one agent. For each scenario, run:

- Claude Code (with Failures MCP)
- Cursor (with Failures MCP)
- Codex / other

Compare `results.json` deltas. If one agent improves significantly more with Failures, investigate prompt sensitivity.

## Limitations

- Proxy uses hand-written naive/improved, not live agent output — necessary for CI but not sufficient for product validation.
- Heuristics are regex, not AST/data-flow — subtle wrong-boundary cases may be missed (see adversarial limitations).
- File-upload and auth have less dramatic CRITICAL deltas; improvement shows via idempotency/concurrency criteria, not just count.
- Real-agent runs require human-in-the-loop (agent must be instructed to call Failures tools before finalizing).

## Conclusions (Phase 3)

- **Model valid**: Principles -> FailureModes -> Patterns -> Invariants -> Tests graph is sufficient; no new principle needed yet.
- **Signal present**: Payment path `pending -> Paystack -> ambiguous -> reconciliation -> verified -> enrollment` now emerges from `review_plan` without explicit failure hints, and naive 3 CRITICAL -> improved 0 CRITICAL is reproducible.
- **Next**: Run manual real-agent validation for the payment scenario exactly as described in the prompt ("Build a course payment system using Paystack. After payment, automatically enroll the student.") — if the Failures-connected agent produces the expected state machine + duplicate-webhook + retry + crash handling without being asked, package.

## Expected template

`expected/payment.json` etc. define `max_critical`, `expected_findings_absent`, and `invariants` for automated checks. See `examples/expected.json` and `evaluation/expected/`.

## Checklist for the question that matters

> "Does connecting Failures to a coding agent measurably improve the failure resilience of the software it produces?"

Proxy answers **yes** for 6/6 scenarios on at least one resilience criterion. Real-agent answer is **pending manual runs** — use `run_evaluation.py --mode manual` after placing agent outputs.
