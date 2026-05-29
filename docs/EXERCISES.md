# Backend Failure Simulation - Hands-On Exercises

Learn by building! Complete these exercises in order to understand real-world backend problems.

---

## Exercise 1: Database Connection Pool Exhaustion

**File:** `db_failures.py`

### What You'll Learn

- How connection pools work
- What happens when pools are exhausted
- How to simulate slow queries

### Your Tasks

1. Create a FastAPI app with a connection pool (simulate with a list)
2. Add an endpoint `/slow-query` that holds a connection for 5 seconds
3. Implement `/healthy` endpoint that checks available connections
4. Add `/exhaust-pool` that takes all connections

### Test It

```bash
# Start multiple slow queries in different terminals
curl http://localhost:8000/slow-query &
curl http://localhost:8000/slow-query &
curl http://localhost:8000/healthy  # Should show low availability
```

### Hints

- Use `asyncio.sleep()` to simulate slow queries
- Track available connections with a counter or semaphore
- Return connection count in health endpoint

---

## Exercise 2: Network Timeouts & Retries

**File:** `network_failures.py`

### What You'll Learn

- How timeouts affect user experience
- Implementing retry logic with exponential backoff
- Cascading failure patterns

### Your Tasks

1. Create endpoint `/external-api` that calls a slow external service
2. Implement `/timeout` that randomly times out (50% chance)
3. Add `/retry-logic` with exponential backoff (3 retries)
4. Create `/cascade` that calls multiple services

### Test It

```bash
curl http://localhost:8001/timeout  # Try multiple times
curl http://localhost:8001/retry-logic  # Watch retry attempts
```

### Hints

- Use `httpx` or `requests` with timeout parameter
- For retries: wait 1s, 2s, 4s between attempts
- Use `random.random()` to simulate failures

---

## Exercise 3: Rate Limiting

**File:** `rate_limiting.py`

### What You'll Learn

- Token bucket algorithm
- Fixed window vs sliding window
- How to protect your API

### Your Tasks

1. Implement a token bucket rate limiter (10 requests/minute)
2. Create `/api/resource` endpoint that uses your rate limiter
3. Add `/check-limit` to see remaining tokens
4. Return HTTP 429 when limit exceeded

### Test It

```bash
# Make 15 rapid requests
for i in {1..15}; do curl http://localhost:8002/api/resource; done
```

### Hints

- Store: `{tokens: int, last_refill: datetime}`
- Refill rate: 10 tokens per 60 seconds
- Decrease token count on each request

---

## Exercise 4: Circuit Breaker Pattern

**File:** `circuit_breaker.py`

### What You'll Learn

- Preventing cascading failures
- Circuit states: Closed, Open, Half-Open
- Automatic recovery

### Your Tasks

1. Implement a circuit breaker with 3 states
2. Create `/unreliable-service` (fails 70% of the time)
3. Wrap it with `/protected-call` using your circuit breaker
4. Add `/circuit-status` endpoint

### Circuit Breaker Logic

- **Closed**: Allow requests, count failures
- **Open** (after 5 failures): Block all requests for 30s
- **Half-Open** (after 30s): Try 1 request to test recovery

### Test It

```bash
# Make repeated calls to trip the circuit
for i in {1..10}; do curl http://localhost:8003/protected-call; sleep 1; done
```

### Hints

- Track: `{state, failures, last_failure_time}`
- Use enum for states: `CLOSED`, `OPEN`, `HALF_OPEN`
- Check time elapsed for state transitions

---

## Exercise 5: Resource Exhaustion

**File:** `resource_failures.py`

### What You'll Learn

- Memory leaks in web apps
- CPU-intensive operations
- Graceful degradation

### Your Tasks

1. Create `/memory-leak` that accumulates data in memory
2. Implement `/cpu-intensive` that performs heavy computation
3. Add `/memory-status` showing current usage
4. Create `/cleanup` to free memory

### Test It

```bash
# Watch memory grow
curl http://localhost:8004/memory-leak  # Call multiple times
curl http://localhost:8004/memory-status

# Test CPU load
curl http://localhost:8004/cpu-intensive
```

### Hints

- Use `psutil` to get memory/CPU stats
- Store data in a global list for "leak" simulation
- Use `time.sleep()` or math operations for CPU load

---

## Bonus Challenges

### Challenge 1: Distributed Rate Limiter

Modify rate limiting to work across multiple instances using a shared counter

### Challenge 2: Circuit Breaker with Metrics

Add success rate tracking and adjustable failure threshold

### Challenge 3: Database Deadlock Simulation

Simulate two transactions waiting for each other's locks

### Challenge 4: Bulkhead Pattern

Isolate different resource pools so one failure doesn't affect others

---

## Learning Resources

- **Circuit Breaker**: <https://martinfowler.com/bliki/CircuitBreaker.html>
- **Rate Limiting Algorithms**: Token Bucket, Leaky Bucket, Sliding Window
- **Connection Pools**: How databases manage concurrent connections
- **Cascading Failures**: How one failure triggers others

---

## Completion Checklist

- [ ] Exercise 1: Database failures
- [ ] Exercise 2: Network timeouts
- [ ] Exercise 3: Rate limiting
- [ ] Exercise 4: Circuit breaker
- [ ] Exercise 5: Resource exhaustion
- [ ] Bonus: Pick one advanced challenge

---

## Tips

1. **Start Simple**: Get basic endpoint working first
2. **Test Incrementally**: Test each feature as you build it
3. **Use Print Statements**: Debug by printing state changes
4. **Read Errors**: Error messages tell you what's wrong
5. **Google It**: Looking up solutions is part of learning!

Good luck!
