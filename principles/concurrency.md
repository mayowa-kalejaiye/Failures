# Concurrency

> What if two actors modify the same state simultaneously?

## Question
Is the read-modify-write safe?

## Failure Mode
- Lost update: two requests read balance 100, both subtract 10, final 90 instead of 80
- Double spend

## Controls
- Pessimistic locking (SELECT FOR UPDATE)
- Optimistic locking (version column)
- Atomic operations (increment/decrement, CAS)

## Tests
- parallel requests touching same record
- concurrent idempotency key insertion
