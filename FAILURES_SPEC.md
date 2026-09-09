# Failures Specification — Engineering Model Contract

> Version 0.2.0 | Status: Draft | Contract for all of Failures (principles, MCP, website, labs, examples)

This document is the single source of truth for what Failures means. Code, MCP tools, and documentation must conform to it. If they disagree, this spec wins.

---

## 1. What is a Failure?

A **failure** is any deviation where the system cannot guarantee that an operation's intended effect happened exactly once and the system is in a valid state.

We distinguish:

- **Hard failure**: operation reported failed (500, exception, timeout)
- **Ambiguous outcome**: caller does not know if side effect happened (timeout, crash before ack, network partition) — the most dangerous kind
- **Partial success**: some steps succeeded, others did not
- **Duplicate execution**: same logical operation executed twice (retry, redelivery, replay)

Failures reasons about failures across **failure dimensions** (see §5).

## 2. What is a Principle?

A **principle** is a named, testable engineering invariant about how to survive a class of failures.

```
Principle { id, name, question, invariant, applies_to[], failure_modes[], patterns[], tests[] }
```

Example:

```json
{
  "id": "idempotency",
  "name": "Idempotency",
  "question": "What happens if this operation executes more than once?",
  "invariant": "One logical operation produces at most one effect regardless of executions.",
  "applies_to": ["payments", "webhooks", "queues", "mutating POSTs", "external APIs"],
  "failure_modes": ["duplicate_side_effect", "duplicate_record", "double_charge"],
  "patterns": ["idempotency-key"],
  "tests": ["retry_after_timeout", "duplicate_request"]
}
```

All principles are deterministic concepts. An LLM may help interpret user input, but principles themselves are explicit.

Current principles (11): `atomicity`, `idempotency`, `ordering`, `concurrency`, `availability`, `timeout`, `consistency`, `resource_exhaustion`, `recovery`, `observability`, `retry_safety`.

## 3. What is an Invariant?

An **invariant** is a predicate that must hold under **any** failure in §1.

- `invariant.payment.not_double_charged`: A payment is charged at most once per logical operation.
- `invariant.enrollment.requires_successful_payment`: Student enrolled only if payment verified.
- `invariant.queue.at_least_once_without_duplicate_effect`: Message may be delivered twice but processed effect is once.

The system violates the contract if an invariant can be broken by any failure scenario.

`check_invariant` tool reasons: given invariants + architecture/plan/code, can a failure violate them? If yes, provide counter-scenario.

## 4. What is a Finding?

A **finding** is the unit of output for all analysis tools.

```json
{
  "id": "external_call_without_idempotency",
  "dimension": "idempotency",
  "severity": "CRITICAL",
  "confidence": 0.91,
  "mode": "STATIC FAILURE CHECK",
  "title": "External side-effect without idempotency key",
  "why": "...",
  "evidence": {"excerpt": "await stripe.charge(...)", "lines": "42-43", "note": "no idempotency_key in call path"},
  "risk": "Retry after ambiguous timeout may duplicate charge",
  "required": ["persist idempotency key BEFORE external call", "..."],
  "optional": ["reconciliation worker"],
  "tests": ["retry_after_provider_success", "..."]
}
```

### 4.1 Severity

- **CRITICAL**: data loss, double charge, unrecoverable invalid state
- **HIGH**: partial state, lost update, cascade risk, duplicate processing
- **MEDIUM**: degraded correctness under load/order/retry storm
- **LOW**: observability / diagnosability gap

### 4.2 Confidence

Float 0.0–1.0. Rule-based heuristics carry honest confidence:

- `0.95+` deterministic syntactic proof (e.g., two `execute` without `BEGIN`)
- `0.75–0.94` strong heuristic (external call without `idempotency_key`)
- `<0.75` weaker signal — still surfaced but labeled Medium confidence

All heuristic outputs are labeled `STATIC FAILURE CHECK — Potential violation detected. Confidence: X` — never `BUG PROVEN` unless deterministic.

### 4.3 Evidence

Every finding must include evidence: code excerpt, component name, or architecture text that triggered the rule, plus why that evidence matters.

## 5. Failure Dimensions

Each dimension defines a question the builder must answer:

| id | question |
|---|---|
| atomicity | Can operations partially succeed? |
| idempotency | What happens if the same operation happens twice? |
| ordering | What if events arrive out of order? |
| concurrency | What if two actors modify the same state? |
| availability | What happens when a dependency disappears? |
| timeout | What happens when you don't know whether it succeeded? |
| consistency | What happens when replicas disagree? |
| resource_exhaustion | What happens when capacity is exceeded? |
| recovery | How does the system return to valid state? |
| observability | How do we know what happened? |
| retry_safety | What happens when retried? |

See `principles/*.md` and `mcp_server/knowledge/principles.json`.

## 6. Knowledge Graph

```
Principle ── failure_modes ──> FailureMode ── mitigation ──> Pattern ── verified_by ──> Test
    │ invariants
    └─ applies_to ──> ComponentType
```

Implemented as JSON today (`mcp_server/knowledge/principles.json`, `rules.json`, `dimensions.json`), extensible to a real graph later.

## 7. Controls & Patterns

Catalog in `patterns/*.md` — e.g., `idempotency-key`, `transactional-outbox`, `circuit-breaker`, `optimistic-locking`. Findings must reference applicable patterns.

## 8. Tools Contract

All tools are deterministic first; LLM is optional post-processing only.

- `get_principles(filter?)` — returns principles+dimensions
- `review_architecture(system, components[], flows[], dependencies[])` — findings[]
- `analyze_component(component_type, description, dependencies[])` — findings[]
- `review_plan(feature, plan[], context?)` — plan-step findings, reordering suggestions
- `check_invariant(invariants[], architecture|plan|code, context?)` — violated? + counter-scenario
- `generate_failure_cases(system, components[], focus?)` — cases[]
- `review_code(code, language)` — findings[] with evidence/confidence, labeled STATIC FAILURE CHECK
- `generate_failure_tests(system, component?, language)` — tests[]
- `check_idempotency / check_retry_safety / check_transaction_safety` — decision + checks + required controls
- `list_failures(filter?)` — rules + failure_docs

Outputs are concise, actionable, and include both human text and `--- JSON ---` machine block. Severity-sorted, with `questions` the agent should answer (architecture tools) and `SUGGESTED TESTS` (code tools).

## 9. Test Recommendations

Every finding maps to tests:

- `retry_after_timeout`, `duplicate_request`, `crash_between_writes`, `concurrent_update`, `dependency_timeout`, `queue_duplicate_delivery`, `crash_before_ack`, `out_of_order`, `burst_rate_limit`, etc.

Golden benchmarks in `examples/*/` define `naive.py` -> expected failures and `improved.py` -> reduced findings. The suite is the regression test for the MCP.

## 10. Evolution Policy

- Spec changes require version bump.
- New principles/dimensions added only after they have: question, invariant, at least one failure_mode, one pattern, one test.
- Tool output shape is additive — new fields allowed, existing fields not removed without major version.

---

**Build for failure, not just success.**
