# Failures MCP

Engineering constraints for AI-built software — deterministic failure checks for coding agents.

## What it does

Makes coding agents reason about what happens **when things fail**, not just when they work.

Deterministic, no LLM needed for core checks.

## Tools (12)

- `get_principles` — list failure dimensions/principles (filterable)
- `review_architecture` — system + components/flows -> severity-ranked failure review
- `analyze_component` — deep dive for one component (payment/queue/db/api/auth/cache/storage/worker)
- `review_plan` — **NEW** analyze ordered implementation plan steps before code exists (catches external-before-pending, enrollment-before-verify)
- `check_invariant` — **NEW** declare invariants ("never enrolled without payment") -> counter-scenarios that violate them
- `generate_failure_cases` — concrete ambiguous/partial failure scenarios
- `review_code` — STATIC FAILURE CHECK with confidence + evidence (idempotency, transactions, timeouts, races, retries)
- `generate_failure_tests` — failure-oriented test cases
- `check_idempotency` — is operation safe to execute twice? (confidence + evidence)
- `check_retry_safety` — can retry duplicate side effects?
- `check_transaction_safety` — partial commit / crash safety?
- `list_failures` — known rules + failure docs

Resources:
- `failures://principles/{id}` — e.g. `failures://principles/idempotency`

## Run locally

```bash
# from repo root
.venv/Scripts/python.exe mcp_server/server.py        # stdio (for MCP clients)
# or
.venv/Scripts/python.exe mcp/server.py

# test a tool directly
.venv/Scripts/python.exe -c "import asyncio, sys; sys.path.insert(0,'mcp_server'); import server; print(asyncio.run(server.mcp.call_tool('get_principles', {'filter':'timeout'})))"
```

Requirements: `mcp`, `pydantic`, `anyio`, `starlette`, `uvicorn` (installed in .venv).

## Agent config

Claude Code / Cursor (`mcp.json` or `~/.config/...`):

```json
{
  "mcpServers": {
    "failures": {
      "command": "failures-mcp",
      "args": []
    }
  }
}
```

Install via `pipx install failures-mcp` (see [INSTALL.md](../INSTALL.md)). From a checkout, use `python -m mcp_server.server` instead.

Alternative (npx style after packaging):
```json
{
  "mcpServers": {
    "failures": {
      "command": "failures-mcp",
      "args": []
    }
  }
}
```

## Examples

**Architecture review**
```json
{
  "tool": "review_architecture",
  "args": {
    "system": "Payment API with FastAPI + PostgreSQL + Stripe",
    "components": [{"name":"payment","description":"charges via Stripe then updates DB","dependencies":["stripe","postgres"]}],
    "flows": ["client -> API -> Stripe -> DB"]
  }
}
```

**Code review (bad payment handler)**
```json
{
  "tool": "review_code",
  "args": {
    "code": "@app.post(\"/payments\")\nasync def pay(payment: Payment):\n    result = await stripe.charge(payment.amount)\n    await db.execute(\"UPDATE accounts SET balance = balance - %s\", payment.amount)\n    return result",
    "language": "python"
  }
}
```
Returns CRITICAL: missing idempotency key, external charge before DB transaction, no timeout, etc., with required controls and tests.

## Knowledge base

- `principles/*.md` — human docs (11 dimensions)
- `patterns/*.md` — idempotency-key, transactional-outbox, circuit-breaker, optimistic-locking
- `failures/*.md` — concrete failure docs
- `mcp_server/knowledge/*.json` — structured source (principles now enriched: applies_to, failure_modes, patterns, tests graph)
- `FAILURES_SPEC.md` — contract: what a failure/principle/invariant/finding is, severity, confidence, evidence

## Golden benchmark

Proves the MCP has teeth:

```bash
.venv/Scripts/python.exe examples/run_benchmark.py
# payment naive: 3 CRITICAL, 1 HIGH -> improved: 0 CRITICAL (all examples pass)
```

See `examples/payment/naive.py` vs `improved.py` and `examples/README.md`.

## Design constraint

No LLM wrapper for core checks. Principles are explicit and composable; an LLM may help interpret arbitrary input but checks remain deterministic.
Outputs are labeled `STATIC FAILURE CHECK — Potential violation detected. Confidence: 0.91` with evidence excerpts, not `BUG PROVEN`.
