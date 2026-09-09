# Adversarial: lock exists but covers wrong critical section

## Code

```python
async with lock:
    user = await db.fetch_one("SELECT stock FROM inventory WHERE id=%s", (item_id,))
# lock released before update
await db.execute("UPDATE inventory SET stock=%s", (user["stock"] - qty,))
```

## Looks safe: lock present

## Not safe: read and write not within same critical section

Engine currently checks `FOR UPDATE` or `version` keyword; this code has `lock` word but not `FOR UPDATE`/`version`, so `race_condition_read_modify_write` still flags (correct). If it used `FOR UPDATE` but released before update, engine would false-negative — noted as limitation.

