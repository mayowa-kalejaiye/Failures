# Consistency

> What happens when replicas or caches disagree?

## Question
Can readers see stale or conflicting state?

## Failure Mode
- Read from replica that hasn't replicated write
- Cache stale after write

## Controls
- Read-your-writes, linearizable reads where needed
- Cache invalidation or write-through
- Version checks
