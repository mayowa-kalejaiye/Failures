# Backend Failure Simulations 🔥

**Learn by building!** Write code yourself to understand real-world backend problems.

## 🎯 Start Here

### 👉 **[START_HERE.md](START_HERE.md)** 👈

New to this project? Read START_HERE.md for your complete getting started guide!

## 🎓 Learning Approach

This is a **hands-on learning project** where YOU implement the code.

### Your Learning Path:
1. **Read** [START_HERE.md](START_HERE.md) - Your roadmap
2. **Code** [exercises/ex1_db_starter.py](exercises/ex1_db_starter.py) - Build connection pools
3. **Test** `python exercises/test_ex1.py` - Verify your work
4. **Learn** by doing, debugging, and iterating!

### Quick Reference:
- 📖 [LEARNING_GUIDE.md](LEARNING_GUIDE.md) - Philosophy & approach
- 📝 [STUDENT_GUIDE.md](STUDENT_GUIDE.md) - Patterns & cheat sheet  
- ✅ [exercises/SOLUTIONS.md](exercises/SOLUTIONS.md) - Hints when stuck

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Choose Your Path

**Path A - Learning Mode:**
```bash
# Open your first exercise
code exercises/ex1_db_starter.py

# Read the TODOs, implement the code, then run:
uvicorn exercises.ex1_db_starter:app --reload --port 8000
```

**Path B - Demo Mode:**
```bash
# Run completed examples
python launcher.py  # Interactive menu
```

## 📚 Scenarios

### 1. Database Failures (`db_failures.py`)
**Port 8000** - Learn how databases fail in production

- **Connection Pool Exhaustion**: Too many concurrent requests
- **Slow Queries**: Missing indexes, full table scans
- **Query Timeouts**: Long-running queries
- **Deadlocks**: Concurrent transaction conflicts
- **Connection Drops**: Network issues mid-query

**Try This:**
```bash
# Start server
uvicorn db_failures:app --reload --port 8000

# Hit these endpoints
curl http://localhost:8000/query/slow
curl http://localhost:8000/query/deadlock
curl http://localhost:8000/stats
```

### 2. Network Issues (`network_failures.py`)
**Port 8001** - Handle unreliable network connections

- **Slow Endpoints**: External APIs taking too long
- **Timeouts**: Request exceeds time limit
- **Intermittent Failures**: Random failures
- **Retry Logic**: Exponential backoff strategy
- **Cascading Failures**: One failure causes others

**Try This:**
```bash
uvicorn network_failures:app --reload --port 8001

# Test retry logic
curl http://localhost:8001/api/retry

# See cascading failures
curl http://localhost:8001/api/cascade
```

### 3. Rate Limiting (`rate_limiting.py`)
**Port 8002** - Protect your API from overload

- **Token Bucket**: Allows bursts, smooth rate limiting
- **Fixed Window**: Simple but has edge cases
- **Sliding Window**: Most accurate
- **Tiered Limits**: Different limits for different users

**Try This:**
```bash
uvicorn rate_limiting:app --reload --port 8002

# Hit endpoint 15 times quickly to trigger rate limit
for i in {1..15}; do curl http://localhost:8002/api/token-bucket; echo ""; done

# Check your rate limit status
curl http://localhost:8002/rate-limit/status
```

### 4. Circuit Breaker (`circuit_breaker.py`)
**Port 8003** - Prevent cascading failures

- **Closed State**: Normal operation
- **Open State**: Failing, reject fast
- **Half-Open State**: Testing recovery
- **Automatic Recovery**: Self-healing system

**Try This:**
```bash
uvicorn circuit_breaker:app --reload --port 8003

# Call unreliable service until circuit opens
for i in {1..10}; do curl http://localhost:8003/api/unreliable; echo ""; sleep 1; done

# Check circuit breaker status
curl http://localhost:8003/circuit-breaker/status
```

### 5. Resource Issues (`resource_failures.py`)
**Port 8004** - Memory leaks and resource exhaustion

- **Memory Leaks**: Memory not released
- **CPU-Intensive Tasks**: Blocking operations
- **Background Tasks**: Task queue exhaustion
- **System Monitoring**: Track resource usage

**Try This:**
```bash
uvicorn resource_failures:app --reload --port 8004

# Simulate memory leak
curl http://localhost:8004/resource/memory-leak?size_mb=50

# Check system status
curl http://localhost:8004/resource/system
```

## 🧪 Automated Testing

Run the test script to see all scenarios in action:

```bash
python test_scenarios.py
```

## 💡 Key Concepts Explained

### Connection Pooling
- Reuse database connections instead of creating new ones
- Limited pool size prevents resource exhaustion
- Requires proper connection lifecycle management

### Exponential Backoff
```python
delay = base_delay * (2 ** attempt)
# Attempt 1: 1s
# Attempt 2: 2s
# Attempt 3: 4s
# Attempt 4: 8s
```

### Rate Limiting Algorithms

**Token Bucket:**
- Tokens added at fixed rate
- Bucket has max capacity
- Request consumes token
- Allows bursts!

**Fixed Window:**
- Count requests in time window
- Reset at window boundary
- Simple but can allow bursts at edges

**Sliding Window:**
- Track individual request timestamps
- Remove old requests
- More accurate, more complex

### Circuit Breaker States

```
CLOSED → [failures] → OPEN → [timeout] → HALF_OPEN
   ↑                                          ↓
   └────────────── [success] ←───────────────┘
```

## 🔍 Real-World Applications

### When Database Pool Exhausts
```python
# Your API suddenly gets 1000 concurrent requests
# Pool has only 10 connections
# 990 requests wait (or timeout)
# Solution: Scale connections or add caching
```

### When External API is Slow
```python
# Payment gateway takes 10 seconds
# Without timeout: Your API waits forever
# With timeout: Fail fast, show error to user
# With retry: Try again with backoff
# With circuit breaker: Stop trying if it's down
```

### When Rate Limited
```python
# Attacker sends 10,000 requests/second
# Without rate limiting: Server crashes
# With rate limiting: Block excess requests
# Server stays healthy
```

## 🎓 Learning Path

1. **Start with Database Failures** - Most common in production
2. **Then Network Issues** - Learn timeouts and retries
3. **Add Rate Limiting** - Protect your services
4. **Implement Circuit Breaker** - Prevent cascades
5. **Monitor Resources** - Keep system healthy

## 📝 Best Practices

1. **Always set timeouts** - Never wait forever
2. **Implement retry logic** - With exponential backoff
3. **Use circuit breakers** - For external dependencies
4. **Monitor everything** - Metrics are crucial
5. **Rate limit APIs** - Protect against abuse
6. **Pool connections** - But monitor pool health
7. **Fail fast** - Don't let errors cascade

## 🛠️ Advanced Exercises

1. Add logging to track failure patterns
2. Implement metrics collection (Prometheus format)
3. Add health check endpoints
4. Create a monitoring dashboard
5. Implement graceful degradation
6. Add distributed tracing

## 📖 Further Reading

- **Retry Pattern**: Handling transient failures
- **Bulkhead Pattern**: Isolating resources
- **Timeout Pattern**: Setting time limits
- **Fallback Pattern**: Alternative responses
- **Health Check Pattern**: Monitoring service health

## 🤝 Contributing

This is a learning project! Experiment, break things, and learn from failures.

## ⚠️ Warning

These simulations can affect system performance. Don't run all scenarios simultaneously on limited hardware.

## 📞 Quick Reference

| Scenario | Port | Key Endpoint |
|----------|------|--------------|
| Database | 8000 | `/stats` |
| Network | 8001 | `/api/retry` |
| Rate Limit | 8002 | `/rate-limit/status` |
| Circuit Breaker | 8003 | `/circuit-breaker/status` |
| Resources | 8004 | `/resource/system` |

Happy Learning! 🚀
