# Adversarial: retry exists but retries non-idempotent operation

## Code

```python
for i in range(3):
    try:
        result = await paystack.charge(amount)  # no idempotency key
    except TimeoutError:
        await asyncio.sleep(2**i)
        continue
```

## Looks safe: has retry with backoff

## Not safe: retry without idempotency duplicates charge

Engine flags `unsafe_retry` (confidence 0.87) — this adversarial case validates that check.
