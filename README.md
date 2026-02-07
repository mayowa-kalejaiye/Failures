# Backend Failure Simulations 🔥

**Learn by building!** Write code yourself to understand real-world backend problems, then build production-ready systems.

## 🎯 Start Here

### 👉 **[docs/START_HERE.md](docs/START_HERE.md)** 👈

New to this project? Read START_HERE.md for your complete getting started guide!

## 📁 Project Structure

```
Failures/
├── 📖 docs/              # All documentation & guides
│   ├── START_HERE.md           # Your first step
│   ├── ROADMAP.md              # Complete learning path
│   ├── QUICKSTART.md           # Get running in 5 min
│   └── ...                     # More guides
│
├── 🎓 exercises/         # Phase 1: Learn failure patterns (TODOs)
│   ├── ex1_db_starter.py       # Connection pools
│   ├── ex2_network_starter.py  # Retry logic
│   └── ex3_ratelimit_starter.py # Rate limiting
│
├── 🏗️ components/        # Phase 2: Build production systems
│   ├── common/                 # Reusable code
│   ├── auth_system/            # Authentication (starter)
│   └── ...                     # More components coming
│
├── 🔧 reference/         # Complete working examples
│   ├── db_failures.py          # Database patterns
│   ├── network_failures.py     # Network patterns
│   └── ...                     # More examples
│
└── 🛠️ tools/            # Utilities & test scripts
    ├── launcher.py             # Interactive launcher
    └── test_scenarios.py       # Automated tests
```

## 🎓 Learning Approach

This is a **two-phase hands-on learning project**:

### Phase 1: Learn Failure Patterns (Exercises)
1. **Read** [docs/START_HERE.md](docs/START_HERE.md) - Your roadmap
2. **Code** [exercises/ex1_db_starter.py](exercises/ex1_db_starter.py) - Build connection pools
3. **Test** `python exercises/test_ex1.py` - Verify your work
4. **Repeat** for network retries and rate limiting

### Phase 2: Build Production Systems (Components)
1. **Read** [docs/BUILDING_SYSTEMS.md](docs/BUILDING_SYSTEMS.md) - System building guide
2. **Build** [components/auth_system/](components/auth_system/) - Complete auth system
3. **Apply** all failure patterns you learned
4. **Deploy** production-ready code

### Quick Reference:
- 📖 [docs/LEARNING_GUIDE.md](docs/LEARNING_GUIDE.md) - Philosophy & approach
- 📝 [docs/CHEATSHEET.md](docs/CHEATSHEET.md) - Quick pattern reference  
- 🗺️ [docs/ROADMAP.md](docs/ROADMAP.md) - Complete learning journey
- ✅ [exercises/SOLUTIONS.md](exercises/SOLUTIONS.md) - Hints when stuck

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Choose Your Path

**Path A - Learning Mode (Phase 1):**
```bash
# Open your first exercise
code exercises/ex1_db_starter.py

# Read the TODOs, implement the code, then run:
uvicorn exercises.ex1_db_starter:app --reload --port 8000
```

**Path B - Building Systems (Phase 2):**
```bash
# After completing exercises, build real systems
code components/auth_system/README.md

# Implement production-ready components
code cReference Examples

Complete working implementations in `reference/` folder:

### 1. Database Failures ([reference/db_failures.py](reference/db_failures.py))
**Port 8000** - Learn how databases fail in production

- **Connection Pool Exhaustion**: Too many concurrent requests
- **Slow Queries**: Missing indexes, full table scans
- **Query Timeouts**: Long-running queries
- **Deadlocks**: Concurrent transaction conflicts
- **Connection Drops**: Network issues mid-query

**Try This:**
```bash
# Start server
uvicorn reference.db_failures:app --reload --port 8000

# Hit these endpoints
curl http://localhost:8000/query/slow
curl http://localhost:8000/query/deadlock
curl http://localhost:8000/stats
```

### 2. Network Issues ([reference/network_failures.py](reference/network_failures.py)
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
uvicorn reference.network_failures:app --reload --port 8001

# Test retry logic
curl http://localhost:8001/api/retry

# See cascading failures
curl http://localhost:8001/api/cascade
```

### 3. Rate Limiting ([reference/rate_limiting.py](reference/rate_limiting.py))
**Port 8002** - Protect your API from overload

- **Token Bucket**: Allows bursts, smooth rate limiting
- **Fixed Window**: Simple but has edge cases
- **Sliding Window**: Most accurate
- **Tiered Limits**: Different limits for different users

**Try This:**
```bash
uvicorn reference.rate_limiting:app --reload --port 8002

# Hit endpoint 15 times quickly to trigger rate limit
for i in {1..15}; do curl http://localhost:8002/api/token-bucket; echo ""; done

# Check your rate limit status
curl http://localhost:8002/rate-limit/status
```

### 4. Circuit Breaker ([reference/circuit_breaker.py](reference/circuit_breaker.py))
**Port 8003** - Prevent cascading failures

- **Closed State**: Normal operation
- **Open State**: Failing, reject fast
- **Half-Open State**: Testing recovery
- **Automatic Recovery**: Self-healing system

**Try This:**
```bash
uvicorn reference.circuit_breaker:app --reload --port 8003

# Call unreliable service until circuit opens
for i in {1..10}; do curl http://localhost:8003/api/unreliable; echo ""; sleep 1; done

# Check circuit breaker status
curl http://localhost:8003/circuit-breaker/status
```

### 5. Resource Issues ([reference/resource_failures.py](reference/resource_failures.py))
**Port 8004** - Memory leaks and resource exhaustion

- **Memory Leaks**: Memory not released
- **CPU-Intensive Tasks**: Blocking operations
- **Background Tasks**: Task queue exhaustion
- **System Monitoring**: Track resource usage

**Try This:**
```bash
uvicorn reference.resource_failures:app --reload --port 8004

# Simulate memory leak
curl http://localhost:8004/resource/memory-leak?size_mb=50

# Check system status
curl http://localhost:8004/resource/system
```

## 🧪 Automated Testing

Run the test script to see all scenarios in action:

```bash
python tools/test_scenarios.py
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

### Phase 1: Learn Failure Patterns (Exercises)
1. **Database Failures** - Connection pools ([exercises/ex1_db_starter.py](exercises/ex1_db_starter.py))
2. **Network Issues** - Retries and timeouts ([exercises/ex2_network_starter.py](exercises/ex2_network_starter.py))
3. **Rate Limiting** - Token bucket algorithm ([exercises/ex3_ratelimit_starter.py](exercises/ex3_ratelimit_starter.py))

**Time:** ~6-8 hours total

### Phase 2: Build Production Systems (Components)
1. **Authentication System** - Login, JWT, security ([components/auth_system/](components/auth_system/))
2. **Payment Processing** - Transactions, idempotency (coming soon)
3. **File Upload Service** - Streaming, resumable uploads (coming soon)
4. **Notification System** - Queues, retries (coming soon)
5. **API Gateway** - Routing, load balancing (coming soon)

**Time:** ~40-50 hours total

See [docs/ROADMAP.md](docs/ROADMAP.md) for the complete learning journey!

## 📝 Best Practices

1. **Always set timeouts** - Never wait forever
2. **Implement retry logic** - With exponential backoff
3. **Use circuit breakers** - For external dependencies
4. **Monitor everything** - Metrics are crucial
5. **Rate limit APIs** - Protect against abuse
6. **Pool connections** - But monitor pool health
7. **Fail fast** - Don't let errors cascade

## � Documentation

All guides are in the [docs/](docs/) folder:

- **Getting Started**: [START_HERE.md](docs/START_HERE.md), [QUICKSTART.md](docs/QUICKSTART.md)
- **Learning**: [LEARNING_GUIDE.md](docs/LEARNING_GUIDE.md), [STUDENT_GUIDE.md](docs/STUDENT_GUIDE.md)
- **Building Systems**: [BUILDING_SYSTEMS.md](docs/BUILDING_SYSTEMS.md), [SYSTEMS_QUICKSTART.md](docs/SYSTEMS_QUICKSTART.md)
- **Reference**: [CHEATSHEET.md](docs/CHEATSHEET.md), [ROADMAP.md](docs/ROADMAP.md)
- **Track Progress**: [MY_PROGRESS.md](docs/MY_PROGRESS.md)

## 🛠️ Tools

- **[tools/launcher.py](tools/launcher.py)** - Interactive menu to run any scenario
- **[tools/test_scenarios.py](tools/test_scenarios.py)** - Automated tests for all patterns

## 🤝 Contributing

This is a learning project! Experiment, break things, and learn from failures.

## ⚠️ Warning

These simulations can affect system performance. Don't run all scenarios simultaneously on limited hardware.

## 📞 Quick Reference

| What | Where | Command |
|------|-------|---------|
| **Phase 1 Exercises** | [exercises/](exercises/) | `code exercises/ex1_db_starter.py` |
| **Phase 2 Components** | [components/](components/) | `code components/auth_system/` |
| **Reference Code** | [reference/](reference/) | `uvicorn reference.db_failures:app --port 8000` |
| **Documentation** | [docs/](docs/) | `code docs/START_HERE.md` |
| **Tools** | [tools/](tools/) | `python tools/launcher.py` |

### Reference Scenarios by Port

| Scenario | Port | File | Key Endpoint |
|----------|------|------|--------------|
| Database | 8000 | [reference/db_failures.py](reference/db_failures.py) | `/stats` |
| Network | 8001 | [reference/network_failures.py](reference/network_failures.py) | `/api/retry` |
| Rate Limit | 8002 | [reference/rate_limiting.py](reference/rate_limiting.py) | `/rate-limit/status` |
| Circuit Breaker | 8003 | [reference/circuit_breaker.py](reference/circuit_breaker.py) | `/circuit-breaker/status` |
| Resources | 8004 | [reference/resource_failures.py](reference/resource_failures.py) | `/resource/system` |

---

**Ready to start?** → [docs/START_HERE.md](docs/START_HERE.md)

Happy Learning! 🚀
