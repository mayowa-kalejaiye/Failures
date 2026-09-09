# Adversarial: queue ack before durable processing

## Code

```python
msg = queue.get()
queue.ack(msg)  # ack BEFORE processing
process(msg)    # if crash here, message lost
```

## Why captured

- Ack present, so naive heuristic `has_ack` would pass
- But ordering wrong: ack must be AFTER success

## Engine must detect

Current `queue_no_ack_handling` checks `has_ack and has_idempotency` — this case has ack but wrong order, so should still be flagged by deeper check.
For Phase 3 we record this as a limitation (false negative) and propose improving engine to check ack ordering, not just presence.

This is tracked as a known limitation in evaluation/README.md.

