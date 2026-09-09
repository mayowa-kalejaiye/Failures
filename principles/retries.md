# Retries & Retry Safety

> What happens when the same operation is attempted again?

## Question
Is it safe to retry? Under what conditions?

## Failure Mode
- Blind retry doubles side effect
- Retry storm overwhelms dependency

## Controls
- Exponential backoff + jitter
- Retry budget / circuit breaker
- Only retry idempotent or safe operations
- Distinguish retryable (timeout/503) vs non-retryable (400/422)

## Tests
- retry after 503 succeeds
- retry after 400 should NOT retry
- retry amplification under load
