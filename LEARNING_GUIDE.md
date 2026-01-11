# 🎓 Backend Engineering - Learn By Building

Welcome! This is a **hands-on** learning project. No copy-paste solutions - you'll build everything yourself.

## 📖 Philosophy

> "I hear and I forget. I see and I remember. I do and I understand." - Confucius

Reading code ≠ understanding code. You need to **write it yourself** to truly learn.

## 🗺️ Learning Path

### Week 1: Database Failures
**File:** `exercises/ex1_db_starter.py`

What you'll build from scratch:
- [ ] Connection pool class
- [ ] Acquire/release connection logic
- [ ] Slow query simulator  
- [ ] Pool exhaustion detection
- [ ] Health check endpoint

**Time:** 2-3 hours

**You'll learn:**
- Why databases have connection limits
- What happens when pools fill up
- How to monitor resource usage
- Common production database issues

### Week 2: Network Failures  
**File:** `exercises/ex2_network_starter.py`

What you'll build:
- [ ] Flaky API simulator
- [ ] Retry logic with exponential backoff
- [ ] Timeout handling
- [ ] Cascading failure demonstration

**Time:** 2-3 hours

**You'll learn:**
- Why services fail randomly
- How to make systems resilient
- Exponential backoff algorithm
- When to stop retrying

### Week 3: Rate Limiting
**File:** `exercises/ex3_ratelimit_starter.py`

What you'll build:
- [ ] Token bucket algorithm
- [ ] Token refill logic
- [ ] Protected API endpoint
- [ ] Rate limit headers

**Time:** 2-3 hours

**You'll learn:**
- How APIs prevent abuse
- Token bucket algorithm
- HTTP 429 status code
- Rate limit strategies

### Week 4-5: Advanced Patterns
Build from scratch:
- Circuit breaker pattern
- Resource monitoring
- Memory leak detection
- Graceful degradation

## 🎯 How To Use This Project

### 1. Start With Exercise 1

```bash
cd c:\Users\kalej\Documents\Failures
code exercises/ex1_db_starter.py
```

### 2. Read The Comments

Every file has:
- ✅ What you need to build
- 💡 Hints to guide you
- 🧪 Testing instructions
- 🏆 Bonus challenges

### 3. Don't Look At Solutions (Yet!)

The `db_failures.py`, `network_failures.py` etc are REFERENCE solutions.
- Try solving it yourself first
- Get stuck? That's good - Google it, debug it
- Still stuck after 30 minutes? Then peek at the solution
- Understand it, then delete your code and write it again from memory

### 4. Test Everything

Run your server and break it! Learn by seeing failures.

```bash
# Run your exercise
uvicorn exercises.ex1_db_starter:app --reload --port 8000

# In another terminal, test it
curl http://localhost:8000/slow-query
```

### 5. Debug Like A Pro

When something doesn't work:
1. **Read the error** - it tells you what's wrong
2. **Add print statements** - see what's happening
3. **Test small pieces** - don't write everything at once
4. **Google the error** - you're not the first to see it

## 📚 Learning Resources

### Connection Pools
- Google: "database connection pool explained"
- Think of it like: Restaurant tables (limited seats)

### Rate Limiting  
- Google: "token bucket algorithm"
- Watch: YouTube "rate limiting explained"

### Retries & Backoff
- Google: "exponential backoff algorithm"
- Real example: Your phone retrying to send a text

### Circuit Breaker
- Google: "circuit breaker pattern martin fowler"
- Real example: Electrical circuit breaker in your house

## 🎓 Backend Engineering Skills You'll Learn

### 1. Resource Management
- Pools, quotas, limits
- When to acquire, when to release
- Preventing resource leaks

### 2. Error Handling
- Try/except patterns
- Graceful failures
- Error propagation

### 3. Async Programming
- async/await syntax
- Concurrent requests
- Non-blocking operations

### 4. System Design Patterns
- Circuit breaker
- Rate limiting
- Retry with backoff
- Bulkhead pattern

### 5. API Design
- HTTP status codes
- Response headers
- Error messages

### 6. Testing
- Load testing
- Failure scenarios
- Edge cases

## ✅ Success Metrics

You know you're learning when:
- ✅ You can explain WHY something works, not just that it works
- ✅ You can predict what will break before running it
- ✅ You modify code and understand the consequences
- ✅ You can solve similar problems without looking at examples

## 🚫 Common Mistakes To Avoid

### Mistake #1: Copy-Pasting Solutions
❌ Copy code → It works → Move on
✅ Understand logic → Write from scratch → Debug issues

### Mistake #2: Not Testing
❌ Write all code → Run once → Hope it works
✅ Write small piece → Test it → Write next piece

### Mistake #3: Skipping Fundamentals
❌ Jump to advanced patterns
✅ Master basics first (pooling, timeouts, retries)

### Mistake #4: Not Breaking Things
❌ Make it work once → Done
✅ Make it work → Break it → Fix it → Understand limits

## 🏆 Challenge Yourself

After each exercise, try:

### Make it break
- What happens with 100 concurrent requests?
- What if timeout is 0.1 seconds?
- What if the pool has 1 connection?

### Make it better  
- Add logging
- Add metrics
- Add better error messages

### Make it real
- Use actual database (SQLite)
- Call real APIs
- Add authentication

## 📊 Track Your Progress

Create a learning journal:

```markdown
# Day 1 - Connection Pools
- Built ConnectionPool class
- Struggled with: async/await syntax
- Learned: Why databases limit connections
- Tomorrow: Add connection timeout

# Day 2 - Pool Exhaustion  
- Simulated pool exhaustion
- Discovered: Slow queries break everything
- Tested: 6 concurrent requests
- Next: Automatic connection cleanup
```

## 🤝 When To Ask For Help

1. **Try yourself first** - 15-30 minutes of struggle
2. **Google it** - Someone else had this problem
3. **Check reference solution** - Understand, don't copy
4. **Ask specific questions** - "Why does X happen?" not "Fix my code"

## 🎯 Your First Session (Start Here!)

**Time: 30 minutes**

1. Open `exercises/ex1_db_starter.py`
2. Read all the TODOs
3. Implement the `ConnectionPool.__init__` method
4. Test it with print statements
5. Move to next TODO

```python
# Your first code - just this!
class ConnectionPool:
    def __init__(self, max_connections: int = 5):
        self.max_connections = max_connections
        self.available_connections = max_connections
        print(f"Pool created with {max_connections} connections")

# Test it
pool = ConnectionPool(3)
print(f"Available: {pool.available_connections}")
```

That's it! Small steps. Build up.

## 🚀 Ready?

Open [exercises/ex1_db_starter.py](exercises/ex1_db_starter.py) and start coding!

Remember: **Struggle = Learning**. Embrace it! 💪
