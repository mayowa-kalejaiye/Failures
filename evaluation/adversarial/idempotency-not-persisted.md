# Adversarial: idempotency key exists but not persisted atomically

## Code (looks safe, is not)

```python
idempotency_key = request.headers["Idempotency-Key"]  # exists
result = await paystack.charge(amount, idempotency_key=idempotency_key)  # passed to provider only
await db.execute("INSERT INTO payments ...")  # inserted AFTER external call, no unique constraint locally
```

## Why it looks safe

- Idempotency key exists
- Provider is told about it

## Why it is not safe

- Key not persisted BEFORE external call with local UNIQUE constraint
- Crash after Paystack success leaves no record; retry will not find prior key and will charge again
- Paystack key scope may not match local logical operation

## Failures must still flag

- `check_idempotency`: has_key true but has_unique false -> REQUIRES idempotency
- `review_code`: still flags external_call_without_idempotency if key not locally persisted with unique constraint
- `review_plan`: flags "Idempotency not established before external call" if step order wrong

## Test

Idempotency key passed only to provider, not inserted locally before call, must be flagged.
