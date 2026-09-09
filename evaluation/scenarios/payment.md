# Scenario: payment

## Prompt (realistic, no failure hints)

> Build a course payment and enrollment system using FastAPI, PostgreSQL and Paystack. A student pays for a course and should automatically receive access after successful payment.

Constraints: none of the following words appear: idempotency, transaction, retry, timeout, failure mode, webhook deduplication.

## Invariants

- `I1`: A student must never be enrolled without a successful payment
- `I2`: A payment must never be charged twice

## Architecture expectations (Failures-connected agent should produce)

```
Payment
  |
  +-- pending (durable, idempotency_key unique)
  |
  v
Paystack
  |
  +-- success
  +-- failure
  +-- ambiguous (timeout)
        |
        v
    reconciliation (poll Paystack or webhook)
        |
        v
    verified payment
        |
        v
    enrollment (idempotent, gated on verified)
```

Must handle: duplicate webhook, retry after timeout, server crash after Paystack success, concurrent enrollment.

## Failure checklist (9 items)

1. duplicate request
2. ambiguous external outcome (Paystack timeout)
3. crash between state transitions (Paystack success -> enrollment)
4. duplicate webhook delivery
5. concurrent execution (two enrollments)
6. retry (student retries after timeout)
7. dependency timeout (Paystack hangs)
8. partial failure (DB down after Paystack success)
9. data consistency (payment vs enrollment state)

## Expected file structure

- `adapter/paystack.py` calls Paystack with `timeout` and `Idempotency-Key`
- `models/payment.py` has `idempotency_key UNIQUE`, `status pending/completed`
- `webhook/handler.py` deduplicates via `event_id UNIQUE`
- `jobs/reconcile.py` reconciles pending

## Adversarial pitfalls

- `adversarial/idempotency-not-persisted.md`
- `adversarial/transaction-wrong-boundary.md`
