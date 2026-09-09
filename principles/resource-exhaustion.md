# Resource Exhaustion

> What happens when capacity is exceeded?

## Failure Mode
- Connection pool exhausted
- Rate limit not enforced → DB overwhelmed
- Unbounded queue → OOM

## Controls
- Bounded pools, queues
- Rate limiting (token bucket)
- Backpressure
- Load shedding

## Tests
- burst 100 req/s
- pool exhaustion
