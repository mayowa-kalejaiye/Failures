# Quick Start Guide

## Step 1: Install Dependencies

```powershell
pip install -r requirements.txt
```

## Step 2: Run Your First Scenario

Start with database failures:

```powershell
uvicorn db_failures:app --reload --port 8000
```

You should see:

```
INFO:     Uvicorn running on http://127.0.0.1:8000
INFO:     Application startup complete.
```

## Step 3: Open in Browser

Go to: <http://localhost:8000>

You'll see all available endpoints!

## Step 4: Try Some Endpoints

### Using Browser

- <http://localhost:8000/health>
- <http://localhost:8000/query/slow>
- <http://localhost:8000/stats>

### Using PowerShell

```powershell
# Test slow query
Invoke-WebRequest http://localhost:8000/query/slow

# Test connection pool exhaustion (run multiple times quickly)
1..10 | ForEach-Object { Invoke-WebRequest http://localhost:8000/query/pool-test }

# Check stats
Invoke-WebRequest http://localhost:8000/stats
```

## Step 5: Try Other Scenarios

Open new PowerShell terminals and run:

```powershell
# Terminal 2: Network failures
uvicorn network_failures:app --reload --port 8001

# Terminal 3: Rate limiting
uvicorn rate_limiting:app --reload --port 8002

# Terminal 4: Circuit breaker
uvicorn circuit_breaker:app --reload --port 8003
```

## What to Try

### Database Failures (Port 8000)

```powershell
# Slow query
Invoke-WebRequest http://localhost:8000/query/slow

# Deadlock simulation
1..10 | ForEach-Object { Invoke-WebRequest http://localhost:8000/query/deadlock }
```

### Rate Limiting (Port 8002)

```powershell
# Hit endpoint rapidly to trigger rate limit
1..15 | ForEach-Object { 
    Invoke-WebRequest http://localhost:8002/api/token-bucket
    Write-Host "Request $_"
}
```

### Circuit Breaker (Port 8003)

```powershell
# Keep calling unreliable service
1..10 | ForEach-Object { 
    try {
        Invoke-WebRequest http://localhost:8003/api/unreliable
        Write-Host "Request $_ succeeded" -ForegroundColor Green
    } catch {
        Write-Host "Request $_ failed: $($_.Exception.Message)" -ForegroundColor Red
    }
    Start-Sleep -Seconds 1
}
```

## Tips

1. **Check the root endpoint** (/) first to see what's available
2. **Use /stats endpoints** to see metrics
3. **Read the responses** - they contain educational explanations
4. **Run the test script**: `python test_scenarios.py`

## Common Issues

### "Module not found"

```powershell
pip install -r requirements.txt
```

### "Port already in use"

Change the port number:

```powershell
uvicorn db_failures:app --reload --port 8005
```

### "Address already in use"

Stop the previous server (Ctrl+C) or use a different port

## Next Steps

1. Read the detailed README.md
2. Look at the code comments in each file
3. Modify the failure rates to see different behaviors
4. Try the automated test script
5. Implement your own failure scenarios!

## Need Help?

Each endpoint returns helpful error messages explaining:

- What went wrong
- Why it happened
- How to fix it
- Prevention strategies

Example error response:

```json
{
  "error": "Rate limit exceeded",
  "message": "Too many requests",
  "suggestion": "Wait for tokens to refill",
  "retry_after": "30 seconds"
}
```

Enjoy learning!
