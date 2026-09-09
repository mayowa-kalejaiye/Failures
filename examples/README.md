# Golden Benchmark

Each example has `naive.py` (flawed) and `improved.py` (failure-aware) plus `expected.json`.

## Run

```bash
.venv/Scripts/python.exe examples/run_benchmark.py
```

## How it validates

`run_benchmark.py` calls `review_code` on naive vs improved and asserts:

- naive has >= expected CRITICAL/HIGH findings
- improved has 0 CRITICAL and fewer findings than naive

Also tests `review_plan` and `check_invariant` for payment example.

This is the regression suite for the MCP — the machine has teeth if naive fails loud and improved quiets it.

See `FAILURES_SPEC.md` for the contract.
