# Failures — Build for failure, not just success.

A deterministic MCP server that makes coding agents reason about failure modes — via AST checks with line evidence and confidence scores, not prompts. Zero tokens, zero hallucination.

Coding agents write happy-path code because their training data is happy-path tutorials. Failures gives them 11 engineering invariants (atomicity, idempotency, timeout/ambiguous outcome, concurrency, ordering, consistency, availability, resource exhaustion, recovery, observability, retry safety) checked deterministically before code ships.

Live on PyPI: `pipx install failures-mcp` — see [INSTALL.md](INSTALL.md).

## Failures MCP

Install it and your agent starts asking:

- What happens if the provider succeeds but the response is lost?
- Can this be retried safely? What if it happens twice?
- What if two requests modify this record concurrently?

```bash
pipx install failures-mcp
failures-mcp
```

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

13 tools: `get_principles`, `review_architecture`, `analyze_component`, `generate_failure_cases`, `review_code`, `generate_failure_tests`, `check_idempotency`, `check_retry_safety`, `check_transaction_safety`, `review_plan`, `check_invariant`, `review_code_semantic`, `list_failures`.

Knowledge base: [principles/](principles/) · [patterns/](patterns/) · [failures/](failures/) · [FAILURES_SPEC.md](FAILURES_SPEC.md) · [mcp/README.md](mcp/README.md)

## Benchmark (reproducible)

24 adversarial scenarios + 6 blind agent evaluations. Reproduce:

```bash
python examples/run_benchmark.py          # naive vs improved, ALL PASS
python evaluation/run_evaluation.py --mode proxy
```

- Harness: [examples/run_benchmark.py](examples/run_benchmark.py), [evaluation/run_evaluation.py](evaluation/run_evaluation.py)
- Adversarial cases: [evaluation/adversarial/](evaluation/adversarial/)
- Results + methodology: [evaluation/README.md](evaluation/README.md)

## Main folders

- [mcp_server/](mcp_server/) + [mcp/](mcp/) MCP server for coding agents
- [principles/](principles/) failure dimensions (human docs)
- [patterns/](patterns/) engineering patterns (idempotency-key, outbox, circuit breaker)
- [failures/](failures/) concrete failure scenarios
- [evaluation/](evaluation/) blind evaluation harness (baseline vs Failures-enabled)
- [examples/](examples/) golden benchmark (naive vs improved)
- [website/](website/) docs site + interactive labs
- [docs/](docs/) guides, roadmap, and progress notes
- [exercises/](exercises/) the original hands-on learning path these principles were distilled from
- [components/](components/) system-building phase
- [reference/](reference/) finished examples
- [tools/](tools/) scripts for running and testing the project

## The learning path (where the principles came from)

The exercises below are the original hands-on path — kept because the MCP's principles were distilled from them, not as the product itself:

Phase 1: learn the basics

1. Database connection pools
2. Network retries and timeouts
3. Rate limiting

Phase 2: build a small system

1. Authentication system
2. More components, only if you want to keep going

## Simple way to begin

```bash
pip install -r requirements.txt
code exercises/ex1_db_starter.py
```

Work through the TODOs, one method at a time, and run the file often.

Start here:

1. [docs/START_HERE.md](docs/START_HERE.md)
2. [docs/LEARNING_GUIDE.md](docs/LEARNING_GUIDE.md)
3. [exercises/README.md](exercises/README.md)

## Helpful commands

```bash
python tools/launcher.py
python tools/test_scenarios.py
code docs/ROADMAP.md
code docs/MY_PROGRESS.md
```

## If you feel stuck

That is normal. Read the error, make one small change, and try again. The goal is steady progress, not speed.
