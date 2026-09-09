# Pattern: Idempotency Key

```
Client -> POST /payments {idempotency_key: uuid, amount}
Server: INSERT INTO idempotency_keys (key, status, response) ON CONFLICT DO NOTHING
        If exists and completed: return cached response
        Else: process, store response, return
```

Required: unique constraint, atomic check-and-set, persisted response.
