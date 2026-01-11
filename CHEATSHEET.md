# Backend Failures Cheat Sheet 📝

## Quick Commands

### Start Servers
```powershell
# Database failures
uvicorn db_failures:app --reload --port 8000

# Network failures  
uvicorn network_failures:app --reload --port 8001

# Rate limiting
uvicorn rate_limiting:app --reload --port 8002

# Circuit breaker
uvicorn circuit_breaker:app --reload --port 8003

# Resource failures
uvicorn resource_failures:app --reload --port 8004
```

## Key Concepts

### 1. Connection Pool
```
Max Connections: 5
Active: 5 → NEW REQUEST → Timeout!
```
**Fix**: Scale pool size, add caching, use read replicas

### 2. Retry Logic
```
Attempt 1: Fail → Wait 1s
Attempt 2: Fail → Wait 2s  
Attempt 3: Fail → Wait 4s
Attempt 4: Success!
```
**Pattern**: Exponential backoff with jitter

### 3. Circuit Breaker
```
CLOSED (normal) 
  → 5 failures 
  → OPEN (reject all)
  → wait 30s
  → HALF_OPEN (test)
  → 2 successes
  → CLOSED
```

### 4. Rate Limiting
```
Token Bucket:
  - Capacity: 10 tokens
  - Refill: 1 token/second
  - Allows bursts up to capacity
  
Fixed Window:
  - 100 requests per minute
  - Resets every minute
  - Edge case: 200 requests in 2 seconds

Sliding Window:
  - 100 requests per 60 seconds
  - Tracks exact timestamps
  - More accurate
```

## Common Failures & Solutions

| Problem | Symptom | Solution |
|---------|---------|----------|
| **Slow Query** | Timeout after 30s | Add indexes, optimize query |
| **Pool Exhaustion** | "No connections available" | Increase pool size, check for leaks |
| **Memory Leak** | RAM usage keeps growing | Profile code, fix object references |
| **Cascading Failure** | Multiple services down | Circuit breakers, bulkheads |
| **Rate Limit Hit** | 429 Too Many Requests | Exponential backoff, upgrade tier |
| **Deadlock** | Transaction timeout | Reduce lock time, optimistic locking |

## HTTP Status Codes

```
200 OK - Success
429 Too Many Requests - Rate limited
500 Internal Server Error - Server failure
503 Service Unavailable - Overloaded/Circuit open
504 Gateway Timeout - Request took too long
```

## Testing Commands

### PowerShell - Rapid Fire
```powershell
# Hit endpoint 10 times
1..10 | ForEach-Object { Invoke-WebRequest http://localhost:8000/query/pool-test }
```

### PowerShell - With Delay
```powershell
1..10 | ForEach-Object { 
    Invoke-WebRequest http://localhost:8003/api/unreliable
    Start-Sleep -Seconds 1
}
```

### PowerShell - Check Response
```powershell
$response = Invoke-WebRequest http://localhost:8000/stats
$response.Content | ConvertFrom-Json | ConvertTo-Json -Depth 10
```

## Monitoring Endpoints

```
/health - Basic health check
/stats - Request statistics  
/rate-limit/status - Current rate limits
/circuit-breaker/status - CB state
/resource/system - System resources
```

## Reset Commands

```powershell
# Reset stats (POST request)
Invoke-WebRequest -Method POST http://localhost:8000/reset
Invoke-WebRequest -Method POST http://localhost:8002/reset
Invoke-WebRequest -Method POST http://localhost:8003/reset
```

## Real-World Scenarios

### Scenario 1: Database Down
```
Problem: Database unreachable
Response: Connection timeout
Time: 30 seconds wasted
Impact: User sees loading spinner, then error

Solution: 
- Set timeout to 5s
- Circuit breaker after 3 failures
- Return cached data or friendly error
```

### Scenario 2: External API Slow
```
Problem: Payment gateway takes 20s
Response: User's checkout hangs
Impact: Cart abandonment, lost sales

Solution:
- Timeout after 10s
- Show processing message
- Retry in background
- Email confirmation when complete
```

### Scenario 3: Sudden Traffic Spike
```
Problem: 10x normal traffic
Response: Server overloaded
Impact: All users affected, system crash

Solution:
- Rate limiting (protect server)
- Connection pooling (limit DB load)  
- Auto-scaling (add more servers)
- Caching (reduce DB queries)
```

## Pro Tips

1. **Always set timeouts** - Default infinity is dangerous
2. **Log everything** - You need data to debug
3. **Monitor proactively** - Fix before users complain
4. **Test failure modes** - Know how your system breaks
5. **Graceful degradation** - Partial service > no service
6. **Document incidents** - Learn from failures

## Debugging Checklist

- [ ] Check logs for errors
- [ ] Check resource usage (CPU, Memory, Disk)
- [ ] Check connection pool status
- [ ] Check rate limit status  
- [ ] Check circuit breaker state
- [ ] Check external dependencies
- [ ] Check network latency
- [ ] Check database query times

## Useful Metrics

- **Request Rate**: requests/second
- **Error Rate**: % of failed requests
- **Latency**: p50, p95, p99 response times
- **Saturation**: Resource usage %
- **Availability**: Uptime %

## Emergency Procedures

### Service is Down
1. Check health endpoint
2. Check logs
3. Restart service
4. Check dependencies
5. Scale up if needed

### Database Overloaded
1. Check slow query log
2. Check connection pool
3. Add read replicas
4. Enable caching
5. Optimize queries

### Memory Leak
1. Check memory usage trend
2. Restart service (temporary)
3. Profile memory usage
4. Fix leak in code
5. Deploy fix

## Learning Path

Week 1: Database failures, connection pooling
Week 2: Network issues, timeouts, retries
Week 3: Rate limiting algorithms
Week 4: Circuit breakers, bulkheads
Week 5: Monitoring, observability
Week 6: Build a resilient system!

---

**Remember**: Every production system fails. The goal is to fail gracefully! 💪
