"""
EXERCISE 2: Network Failures & Retries
======================================

YOUR MISSION: See how network problems break systems and fix them with retries!

CONCEPTS TO LEARN:
- Timeouts (waiting too long)
- Retries with exponential backoff
- Cascading failures (one failure causes more)
- Circuit breakers (stopping the bleeding)

RUN: uvicorn exercises.ex2_network_starter:app --reload --port 8001
"""

from fastapi import FastAPI, HTTPException
import asyncio
import random
import time
from datetime import datetime

app = FastAPI(title="Network Failures Exercise")


# STEP 1: Simulate an unreliable external API
# ===========================================

async def call_external_api():
    """
    TODO: Simulate calling an external service that sometimes fails
    
    - 50% of the time: sleep 3 seconds and return success
    - 50% of the time: raise an exception "Service unavailable"
    
    HINT: Use random.random() < 0.5 to flip a coin
    """
    pass


@app.get("/")
async def home():
    return {
        "message": "Network Failure Simulator",
        "endpoints": {
            "/flaky-api": "Call unreliable external service (no retry)",
            "/retry-logic": "Same but with retries!",
            "/timeout": "Test timeout handling",
            "/cascade": "Watch one failure cause many"
        }
    }


@app.get("/flaky-api")
async def flaky_api():
    """
    TODO: Call the external API (no retry)
    
    - Try to call call_external_api()
    - If it fails, return error
    - If it succeeds, return success
    """
    return {"status": "TODO: Implement me!"}


@app.get("/retry-logic")
async def with_retry():
    """
    TODO: Implement retry logic with exponential backoff
    
    Algorithm:
    1. Try calling call_external_api()
    2. If it fails, wait 1 second and try again
    3. If it fails again, wait 2 seconds
    4. If it fails again, wait 4 seconds
    5. After 3 total attempts, give up
    
    Return how many attempts it took
    
    HINTS:
    - Use a for loop: for attempt in range(1, 4):
    - Wait time = 2 ** (attempt - 1)
    - Use try/except to catch failures
    """
    return {"status": "TODO: Implement me!"}


@app.get("/timeout")
async def timeout_example():
    """
    TODO: Simulate a timeout
    
    - Start a timer
    - Try to call a slow service
    - If it takes > 2 seconds, cancel it and return timeout error
    
    HINT: Use asyncio.wait_for(your_function(), timeout=2.0)
    """
    return {"status": "TODO: Implement me!"}


@app.get("/cascade")  
async def cascade_failure():
    """
    CHALLENGE: Demonstrate cascading failure
    
    Scenario: You need to call 3 services (A, B, C) in sequence
    - Each service has 30% failure rate
    - If A fails, you can't call B
    - If B fails, you can't call C
    
    TODO: 
    - Show how one failure stops everything
    - Track which service failed
    - Return the cascade effect
    """
    return {"status": "TODO: Implement me!"}


# ============================================================================
# TESTING INSTRUCTIONS
# ============================================================================
#
# 1. Run: uvicorn exercises.ex2_network_starter:app --reload --port 8001
#
# 2. Test flaky API - run multiple times, see random failures:
#    curl http://localhost:8001/flaky-api
#
# 3. Test retry logic - should eventually succeed:
#    curl http://localhost:8001/retry-logic
#
# 4. Test timeout:
#    curl http://localhost:8001/timeout
#
# ============================================================================
# BONUS CHALLENGES  
# ============================================================================
#
# 1. Add jitter to retries (random wait time to avoid thundering herd)
# 2. Track success rate over last 10 requests
# 3. Implement circuit breaker (stop calling after 5 failures)
# 4. Add request deduplication (don't retry same request twice)
#
# ============================================================================
