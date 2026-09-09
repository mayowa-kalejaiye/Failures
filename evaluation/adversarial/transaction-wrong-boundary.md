# Adversarial: transaction exists but external side effect outside it

## Code

```python
async with db.transaction():
    await db.execute("INSERT INTO payments ... status='pending'")

result = await paystack.charge(...)  # OUTSIDE transaction

async with db.transaction():
    await db.execute("UPDATE payments SET status='completed'")
```

## Why it looks safe

- Transactions are present

## Why it is not safe

- External effect cannot be rolled back; if second transaction fails, money charged but not recorded
- Correct: pending record BEFORE external call in first transaction, external call OUTSIDE transaction by necessity, but reconciliation + idempotency needed

## Failures must flag

- `charge_then_db_update` should flag when charge occurs without pending record BEFORE it, even if some transaction exists nearby
- `check_invariant`: payment never charged twice is violatable if pending not before charge
