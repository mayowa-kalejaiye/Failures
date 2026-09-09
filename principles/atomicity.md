# Atomicity

> Can an operation partially succeed?

## Question
If the system crashes mid-operation, what state survives?

## Failure Mode
Partial success leaves data in an inconsistent state:
- debit succeeds, but transaction record not marked complete
- file uploaded but metadata not saved
- message processed but not acknowledged

## Required Invariant
An operation must either fully succeed or fully fail. No intermediate state should be visible.

## Controls
- Database transactions (BEGIN/COMMIT/ROLLBACK)
- Transactional outbox
- Saga pattern for distributed transactions
- Compensating actions

## Tests
- crash between steps
- DB failure after first write
- process killed mid-transaction

## Related Patterns
- transactional-outbox
- saga

## Severity If Violated
CRITICAL — partial state causes data loss or double effects.
