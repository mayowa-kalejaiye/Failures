# Availability

> What happens when a dependency disappears?

## Question
Can the system degrade gracefully?

## Failure Mode
- DB down → 500 for all requests
- External API slow → thread pool exhaustion → cascade

## Controls
- Circuit breaker
- Bulkhead isolation
- Fallback / degraded response
- Retry with jitter + timeout

## Tests
- dependency returns 500
- dependency times out
- dependency slow (2-5s)
