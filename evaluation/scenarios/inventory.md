# Scenario: inventory

## Prompt

> Build an inventory system for limited course seats. Students can enroll until seats run out. Handle concurrent enrollments correctly using PostgreSQL.

No mention of locking, optimistic concurrency, or atomic decrement.

## Invariants

- `I1`: Seats must never go negative, no oversell
- `I2`: Concurrent enrollments must not cause lost update

## Expected Failures-enabled

- Atomic `UPDATE ... SET stock=stock-1 WHERE stock>0` or `SELECT FOR UPDATE` or version column
- Deduplication of enrollment requests
