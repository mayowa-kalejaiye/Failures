# Failures-enabled outputs (with Failures)

Place agent output here for manual mode.

Workflow:
1. Give the exact same scenario prompt to the agent, but with Failures MCP connected (see `mcp/README.md`).
2. Ask the agent to call `review_plan` before coding and `review_code` + `check_invariant` iterations before finalizing.
3. Save the final system to `payment.py` etc.

Proxy mode uses `../../examples/payment/improved.py`.
