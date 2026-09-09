# Idempotency

> What happens if the same operation happens twice?

## Question
Can the client or infrastructure retry and cause duplicate side effects?

## Failure Mode
- Network timeout causes client retry → duplicate charge
- Webhook delivered twice → duplicate record
- Queue redelivery → duplicate processing

## Required Invariant
One logical operation produces at most one effect, no matter how many times it is executed.

## Controls
- Idempotency keys (client-supplied, server-persisted)
- Unique constraints on logical operation ID
- State machine: pending → completed, ignore completed
- Dedup table

## Tests
- same request sent twice
- same idempotency key with different payload
- retry after timeout

## Severity
CRITICAL for any operation with side effects crossing network boundary.
