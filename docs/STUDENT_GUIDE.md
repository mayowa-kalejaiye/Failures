# Backend Failure Patterns - Student Cheat Sheet

## Quick Start (Your First 5 Minutes)

```bash
# 1. Open your first exercise
code exercises/ex1_db_starter.py

# 2. Run the template
uvicorn exercises.ex1_db_starter:app --reload --port 8000

# 3. Test it (it won't work yet - that's the point!)
curl http://localhost:8000/slow-query
```

## Exercise Roadmap

| Week | Exercise | File | What You'll Build |
|------|----------|------|------------------|
| 1 | Database Pools | `ex1_db_starter.py` | Connection pool from scratch |
| 2 | Network Issues | `ex2_network_starter.py` | Retry logic & timeouts |
| 3 | Rate Limiting | `ex3_ratelimit_starter.py` | Token bucket algorithm |

## Patterns You'll Implement

### Pattern 1: Resource Pool

```python
class ConnectionPool:
    def __init__(self, max_connections):
        self.max = max_connections
        self.available = max_connections
    
    async def acquire(self):
        if self.available > 0:
            self.available -= 1
            return True
        return False  # Pool exhausted!
    
    def release(self):
        self.available = min(self.available + 1, self.max)
```

**Used for:** Databases, HTTP connections, thread pools

---

### Pattern 2: Exponential Backoff

```python
async def retry_with_backoff(max_attempts=3):
    for attempt in range(1, max_attempts + 1):
        try:
            return await risky_operation()
        except Exception as e:
            if attempt == max_attempts:
                raise
            wait_time = 2 ** (attempt - 1)  # 1, 2, 4, 8...
            print(f"Attempt {attempt} failed, waiting {wait_time}s")
            await asyncio.sleep(wait_time)
```

**Used for:** API calls, network operations, retry logic

---

### Pattern 3: Token Bucket

```python
class TokenBucket:
    def __init__(self, capacity, refill_rate):
        self.capacity = capacity
        self.tokens = capacity
        self.refill_rate = refill_rate
        self.last_refill = time.time()
    
    def _refill(self):
        now = time.time()
        elapsed = now - self.last_refill
        new_tokens = elapsed * self.refill_rate
        self.tokens = min(self.tokens + new_tokens, self.capacity)
        self.last_refill = now
    
    def consume(self, tokens=1):
        self._refill()
        if self.tokens >= tokens:
            self.tokens -= tokens
            return True
        return False
```

**Used for:** Rate limiting, throttling, quota management

---

## FastAPI Essentials

### Create Endpoint

```python
from fastapi import FastAPI, HTTPException
import asyncio

app = FastAPI()

@app.get("/")
async def home():
    return {"message": "Hello!"}
```

### Handle Errors

```python
@app.get("/risky")
async def risky_endpoint():
    try:
        result = dangerous_operation()
        return {"result": result}
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Something broke: {str(e)}"
        )
```

### Async Sleep (Non-blocking!)

```python
@app.get("/slow")
async def slow_query():
    await asyncio.sleep(5)  # Doesn't block other requests
    return {"done": True}
```

---

## Testing Your Code

### Test Single Request

```bash
curl http://localhost:8000/endpoint
```

### Test Concurrent Requests (Windows PowerShell)

```powershell
# Send 10 requests at once
1..10 | ForEach-Object {
    Start-Job { Invoke-WebRequest http://localhost:8000/slow-query }
}
```

### Python Test Script

```python
import requests
import time

for i in range(20):
    start = time.time()
    r = requests.get('http://localhost:8000/endpoint')
    elapsed = time.time() - start
    print(f"{i+1}: {r.status_code} - {elapsed:.2f}s - {r.json()}")
    time.sleep(0.1)
```

---

## HTTP Status Codes

| Code | Name | When You'll Use It |
|------|------|-------------------|
| 200 | OK | Request succeeded |
| 400 | Bad Request | Invalid input |
| 429 | Too Many Requests | **Rate limit hit!** |
| 500 | Internal Server Error | Your code threw exception |
| 503 | Service Unavailable | **Pool exhausted!** |
| 504 | Gateway Timeout | External service too slow |

---

## Python Async Quick Reference

### Define Async Function

```python
async def fetch_data():
    await asyncio.sleep(1)
    return "data"
```

### Call Async Function (Must use await!)

```python
result = await fetch_data()  #  Correct
result = fetch_data()        #  Wrong! Returns coroutine object
```

### Run Multiple Async Operations

```python
# Sequential (slow)
data1 = await fetch_data()
data2 = await fetch_data()

# Concurrent (fast!)
data1, data2 = await asyncio.gather(
    fetch_data(),
    fetch_data()
)
```

---

## Managing State

### Global Variable (Simple)

```python
request_count = 0

@app.get("/count")
async def count():
    global request_count
    request_count += 1
    return {"count": request_count}
```

### Class Instance (Better)

```python
class RateLimiter:
    def __init__(self):
        self.requests = {}
    
    def is_allowed(self, user_id):
        # Your logic
        pass

# Create global instance
limiter = RateLimiter()

@app.get("/protected")
async def protected():
    if not limiter.is_allowed("user123"):
        raise HTTPException(status_code=429)
    return {"data": "secret"}
```

---

## Debugging Techniques

### Print Debugging (Your Best Friend)

```python
print(f"DEBUG: tokens={self.tokens}, capacity={self.capacity}")
print(f"DEBUG: available connections: {self.available}")
```

### Check Timing

```python
import time

start = time.time()
await slow_operation()
elapsed = time.time() - start
print(f"Operation took {elapsed:.2f} seconds")
```

### Inspect Variables

```python
try:
    result = risky_function()
except Exception as e:
    print(f"Exception type: {type(e).__name__}")
    print(f"Exception message: {str(e)}")
    print(f"Variables at crash: x={x}, y={y}")
    raise
```

---

## When You Get Stuck

### Error: "coroutine was never awaited"

```python
#  Wrong
result = async_function()

#  Correct  
result = await async_function()
```

### Error: "RuntimeError: no running event loop"

```python
#  Don't call async functions from sync code
def sync_function():
    result = await async_function()  # Won't work!

#  Make the function async
async def async_function():
    result = await other_async_function()  # Works!
```

### Pool Never Releases Connections

```python
#  Forgot to release
async def query():
    await pool.acquire()
    await asyncio.sleep(5)
    return "done"  # Connection leaked!

#  Always release
async def query():
    await pool.acquire()
    try:
        await asyncio.sleep(5)
        return "done"
    finally:
        pool.release()  # Guaranteed to run
```

---

## Google These When Stuck

| Problem | Search Term |
|---------|-------------|
| Connection pools | "database connection pool explained" |
| Async/await | "python asyncio tutorial" |
| Rate limiting | "token bucket algorithm explained" |
| Retries | "exponential backoff python" |
| HTTP errors | "http 429 status code" |

---

## Completion Checklist

### Exercise 1: Database Pools

- [ ] Implement `ConnectionPool.__init__()`
- [ ] Implement `acquire_connection()`
- [ ] Implement `release_connection()`
- [ ] Implement `get_stats()`
- [ ] Create `/slow-query` endpoint
- [ ] Test pool exhaustion with 6 concurrent requests
- [ ] Add `/health` endpoint

### Exercise 2: Network Failures

- [ ] Create flaky API simulator
- [ ] Implement `/flaky-api` endpoint
- [ ] Add retry logic with exponential backoff
- [ ] Implement timeout handling
- [ ] Create cascade failure demo

### Exercise 3: Rate Limiting

- [ ] Implement `TokenBucket.__init__()`
- [ ] Implement `_refill()` method
- [ ] Implement `consume()` method
- [ ] Protect endpoint with rate limiter
- [ ] Return HTTP 429 when limit exceeded
- [ ] Add rate limit headers

---

## Pro Tips

1. **Start small** - Get one method working before moving on
2. **Test constantly** - Run your server after each change
3. **Use print()** - See what your code is actually doing
4. **Read errors carefully** - They tell you exactly what's wrong
5. **Google is your friend** - Everyone looks things up!

---

## Your First Steps (Right Now!)

```bash
# 1. Open exercise 1
code c:\Users\kalej\Documents\Failures\exercises\ex1_db_starter.py

# 2. Find the first TODO

# 3. Implement just the __init__ method:
class ConnectionPool:
    def __init__(self, max_connections: int = 5):
        self.max_connections = max_connections
        self.available_connections = max_connections
        print(f"Pool created with {max_connections} connections!")

# 4. Test it:
db_pool = ConnectionPool(5)

# 5. Run the server to see if it works
# uvicorn exercises.ex1_db_starter:app --reload --port 8000
```

That's it! One small step at a time.

---

**Remember:** The struggle is where the learning happens! Keep coding!
