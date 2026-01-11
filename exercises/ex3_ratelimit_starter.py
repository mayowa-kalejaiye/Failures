"""
EXERCISE 3: Rate Limiting
=========================

YOUR MISSION: Protect your API from being overwhelmed!

CONCEPTS TO LEARN:
- Token bucket algorithm
- Fixed window rate limiting
- HTTP 429 (Too Many Requests)
- Rate limit headers

RUN: uvicorn exercises.ex3_ratelimit_starter:app --reload --port 8002
"""

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from datetime import datetime, timedelta
import time

app = FastAPI(title="Rate Limiting Exercise")


# STEP 1: Build a Token Bucket Rate Limiter
# =========================================

class TokenBucket:
    """
    Token Bucket Algorithm:
    - You have a bucket that holds tokens
    - Each request costs 1 token
    - Tokens refill at a constant rate
    - If bucket empty, request is denied
    """
    
    def __init__(self, capacity: int = 10, refill_rate: float = 1.0):
        """
        TODO: Initialize the token bucket
        
        Parameters:
        - capacity: Maximum tokens (e.g., 10 requests)
        - refill_rate: Tokens per second (e.g., 1.0 = 1 token/second)
        
        You need to track:
        - self.capacity (max tokens)
        - self.tokens (current tokens, start at capacity)
        - self.refill_rate (how fast tokens come back)
        - self.last_refill (when we last added tokens)
        """
        self.capacity = capacity
        self.tokens = capacity # starting full
        self.refill_rate = refill_rate
        self.last_refill = time.time()
    
    def _refill(self):
        """
        TODO: Add tokens based on time elapsed
        
        Algorithm:
        1. Calculate time since last_refill
        2. Calculate new tokens = time_elapsed * refill_rate
        3. Add them to self.tokens (but don't exceed capacity!)
        4. Update last_refill to now
        
        HINTS:
        - Use time.time() to get current time
        - Use min(tokens + new_tokens, capacity) to cap it
        """
        now = time.time()
        elapsed = now - self.last_refill

        new_tokens = elapsed * self.refill_rate
        self.tokens = min(self.capacity, self.tokens + new_tokens)
        self.last_refill = now


    
    def consume(self, tokens: int = 1) -> bool:
        """
        TODO: Try to consume tokens
        
        Algorithm:
        1. First, refill tokens based on time elapsed
        2. Check if we have enough tokens
        3. If yes: subtract tokens and return True
        4. If no: return False
        """
        self._refill()
        if self.tokens >= tokens:
            self.tokens -= tokens
            return True
        return False
    
    def get_info(self):
        """
        TODO: Return current bucket status
        
        Return dict with:
        - tokens (current)
        - capacity (max)
        - refill_rate
        """
        return {
            "tokens": self.tokens,
            "capacity": self.capacity,
            "refill_rate": self.refill_rate,
        }


# STEP 2: Create your rate limiter
# ================================
# TODO: Create global rate limiter: 10 requests max, refills at 2/second
# rate_limiter = TokenBucket(capacity=10, refill_rate=2.0)

rate_limiter = TokenBucket(capacity=10, refill_rate=2.0)

@app.get("/")
async def home():
    return {
        "message": "Rate Limiting Exercise",
        "endpoints": {
            "/api/resource": "Protected endpoint with rate limiting",
            "/status": "Check rate limit status",
            "/unlimited": "No rate limiting (for comparison)"
        }
    }


@app.get("/api/resource")
async def protected_resource():
    """
    TODO: Protect this endpoint with rate limiting
    
    Steps:
    1. Try to consume 1 token from rate_limiter
    2. If successful: return success response
    3. If failed: raise HTTPException(status_code=429, detail="Rate limit exceeded")
    
    Bonus: Add headers showing rate limit info:
    - X-RateLimit-Limit: capacity
    - X-RateLimit-Remaining: current tokens
    """
    if not rate_limiter.consume(1):
        raise HTTPException(
            status_code=429,
            detail="Rate limit exceeded"
        )
    
    response = JSONResponse({"message": "Request successful"})
    response.headers["X-RateLimit-Limit"] = str(rate_limiter.capacity)
    response.headers["X-RateLimit-Remaining"] = str(rate_limiter.tokens)
    return response



@app.get("/status")
async def rate_limit_status():
    """
    TODO: Return rate limiter information
    
    Call rate_limiter.get_info() and return it
    """
    return rate_limiter.get_info()


@app.get("/unlimited")
async def unlimited_resource():
    """This endpoint has NO rate limiting - for comparison"""
    return {
        "message": "This endpoint is unprotected!",
        "advice": "In production, always protect your endpoints"
    }


# ============================================================================
# TESTING INSTRUCTIONS
# ============================================================================
#
# 1. Run: uvicorn exercises.ex3_ratelimit_starter:app --reload --port 8002
#
# 2. Test rate limit - make rapid requests (should hit limit):
#    Windows PowerShell:
#    for ($i=1; $i -le 15; $i++) { curl http://localhost:8002/api/resource; Start-Sleep -Milliseconds 100 }
#
#    Or use this Python script:
#    import requests
#    for i in range(15):
#        r = requests.get('http://localhost:8002/api/resource')
#        print(f"{i+1}. Status: {r.status_code}")
#
# 3. Check status between requests:
#    curl http://localhost:8002/status
#
# 4. Wait a few seconds and try again - tokens should refill!
#
# ============================================================================
# BONUS CHALLENGES
# ============================================================================
#
# 1. Implement per-user rate limiting (different limits for different users)
# 2. Add sliding window instead of token bucket
# 3. Store rate limits in Redis for multi-instance support
# 4. Add rate limit by IP address
# 5. Implement different tiers (free: 10/min, premium: 100/min)
#
# ============================================================================
