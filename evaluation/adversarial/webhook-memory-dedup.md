# Adversarial: webhook deduplication in memory

## Code

```python
seen = set()
@app.post("/webhook/paystack")
async def webhook(event):
    if event["event_id"] in seen:
        return {"already_processed": True}
    seen.add(event["event_id"])
    await db.execute("UPDATE payments SET status='completed' ...")
```

## Looks safe: dedup check exists

## Not safe: in-memory set lost on restart; not durable

Engine checks `unique|on conflict|upsert|dedup` — this has `seen` but not `unique` or `dedup table`, but also not persisted. `check_idempotency` will see `idempotency`? No. It looks for `unique|on conflict|upsert|dedup` — this code has no `unique`, so it correctly fails. If it had `dedup` variable name, it would false-pass — limitation noted.
