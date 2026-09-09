# Timeouts / Ambiguous Outcome

> What happens when you don't know whether the operation succeeded?

This is the most dangerous failure. Timeout != failure.

## Question
If the call times out, did it succeed?

## Failure Mode
- Payment provider charged card but response lost → retry creates duplicate
- DB commit succeeded but connection dropped

## Controls
- Separate timeout from failure
- Idempotency + reconciliation
- State: initiated → pending → confirmed
- Background reconciler that queries provider

## Tests
- provider succeeds then timeout
- DB commit then connection drop
