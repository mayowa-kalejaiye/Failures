"""
Rate Limiting Simulations

Common rate limiting strategies to protect your API:
1. Token Bucket - Allows bursts while limiting average rate
2. Fixed Window - Simple but can allow burst at window boundaries
3. Sliding Window - More accurate but more complex
4. IP-based rate limiting
"""

from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
import time
from datetime import datetime, timedelta
from collections import defaultdict
from typing import Dict, Optional

app = FastAPI(title="Rate Limiting Simulator")


class RateLimitConfig(BaseModel):
    requests_per_minute: int = 10
    burst_size: int = 5


# Rate limiting storage (in production, use Redis)
token_buckets: Dict[str, dict] = {}
fixed_windows: Dict[str, dict] = defaultdict(lambda: {"count": 0, "reset_time": time.time() + 60})
sliding_windows: Dict[str, list] = defaultdict(list)

# Stats
rate_limit_stats = {
    "total_requests": 0,
    "rate_limited": 0,
    "successful": 0
}


class TokenBucket:
    """
    Token Bucket Algorithm
    - Tokens added at fixed rate
    - Can accumulate up to bucket capacity (allows bursts)
    - Request consumes one token
    """
    def __init__(self, capacity: int, refill_rate: float):
        self.capacity = capacity  # Max tokens
        self.tokens = capacity    # Current tokens
        self.refill_rate = refill_rate  # Tokens per second
        self.last_refill = time.time()
    
    def consume(self, tokens: int = 1) -> bool:
        """Try to consume tokens, return True if successful"""
        self._refill()
        
        if self.tokens >= tokens:
            self.tokens -= tokens
            return True
        return False
    
    def _refill(self):
        """Refill tokens based on time elapsed"""
        now = time.time()
        elapsed = now - self.last_refill
        
        # Add tokens based on time elapsed
        new_tokens = elapsed * self.refill_rate
        self.tokens = min(self.capacity, self.tokens + new_tokens)
        self.last_refill = now
    
    def get_status(self):
        self._refill()
        return {
            "available_tokens": int(self.tokens),
            "capacity": self.capacity,
            "refill_rate": f"{self.refill_rate} tokens/sec"
        }


def get_client_id(request: Request) -> str:
    """Get client identifier (in production, could be API key, user ID, etc.)"""
    return request.client.host if request.client else "unknown"


@app.get("/")
async def root():
    return {
        "message": "Rate Limiting Simulator",
        "endpoints": {
            "token_bucket": "/api/token-bucket",
            "fixed_window": "/api/fixed-window",
            "sliding_window": "/api/sliding-window",
            "premium": "/api/premium",
            "status": "/rate-limit/status",
            "stats": "/stats"
        },
        "tip": "Hit the same endpoint multiple times quickly to trigger rate limiting"
    }


@app.get("/api/token-bucket")
async def token_bucket_endpoint(request: Request):
    """
    Token Bucket Rate Limiting
    - Allows 10 requests per minute (avg)
    - Allows bursts up to 5 tokens
    """
    client_id = get_client_id(request)
    rate_limit_stats["total_requests"] += 1
    
    # Initialize bucket for new clients
    if client_id not in token_buckets:
        # 10 requests per minute = 10/60 = 0.167 tokens per second
        token_buckets[client_id] = TokenBucket(capacity=5, refill_rate=10/60)
    
    bucket = token_buckets[client_id]
    
    if not bucket.consume():
        rate_limit_stats["rate_limited"] += 1
        raise HTTPException(
            status_code=429,
            detail={
                "error": "Rate limit exceeded",
                "message": "Too many requests",
                "limit": "10 requests per minute",
                "burst_allowed": "5 requests",
                "retry_after": "Wait for tokens to refill",
                "current_tokens": bucket.get_status()
            }
        )
    
    rate_limit_stats["successful"] += 1
    return {
        "status": "success",
        "message": "Request processed",
        "rate_limit": bucket.get_status(),
        "algorithm": "Token Bucket"
    }


@app.get("/api/fixed-window")
async def fixed_window_endpoint(request: Request):
    """
    Fixed Window Rate Limiting
    - Simple: 10 requests per 60-second window
    - Problem: Can get 20 requests in short time at window boundary
    """
    client_id = get_client_id(request)
    rate_limit_stats["total_requests"] += 1
    
    now = time.time()
    window = fixed_windows[client_id]
    
    # Reset window if expired
    if now >= window["reset_time"]:
        window["count"] = 0
        window["reset_time"] = now + 60
    
    # Check limit
    if window["count"] >= 10:
        rate_limit_stats["rate_limited"] += 1
        seconds_until_reset = int(window["reset_time"] - now)
        
        raise HTTPException(
            status_code=429,
            detail={
                "error": "Rate limit exceeded",
                "message": "Too many requests in this window",
                "limit": "10 requests per minute",
                "retry_after": f"{seconds_until_reset} seconds",
                "window_resets_at": datetime.fromtimestamp(window["reset_time"]).isoformat(),
                "problem": "Fixed window allows bursts at boundaries"
            }
        )
    
    window["count"] += 1
    rate_limit_stats["successful"] += 1
    
    return {
        "status": "success",
        "message": "Request processed",
        "rate_limit": {
            "used": window["count"],
            "limit": 10,
            "remaining": 10 - window["count"],
            "reset_in": f"{int(window['reset_time'] - now)}s"
        },
        "algorithm": "Fixed Window"
    }


@app.get("/api/sliding-window")
async def sliding_window_endpoint(request: Request):
    """
    Sliding Window Rate Limiting
    - More accurate than fixed window
    - Tracks individual request timestamps
    - Limit: 10 requests per 60 seconds
    """
    client_id = get_client_id(request)
    rate_limit_stats["total_requests"] += 1
    
    now = time.time()
    window_size = 60  # seconds
    limit = 10
    
    # Get request history
    requests = sliding_windows[client_id]
    
    # Remove old requests outside the window
    requests[:] = [req_time for req_time in requests if now - req_time < window_size]
    
    # Check limit
    if len(requests) >= limit:
        rate_limit_stats["rate_limited"] += 1
        oldest_request = min(requests)
        retry_after = int((oldest_request + window_size) - now)
        
        raise HTTPException(
            status_code=429,
            detail={
                "error": "Rate limit exceeded",
                "message": "Too many requests in sliding window",
                "limit": f"{limit} requests per {window_size} seconds",
                "retry_after": f"{retry_after} seconds",
                "current_count": len(requests),
                "advantage": "More accurate than fixed window - prevents boundary bursts"
            }
        )
    
    # Add current request
    requests.append(now)
    rate_limit_stats["successful"] += 1
    
    return {
        "status": "success",
        "message": "Request processed",
        "rate_limit": {
            "used": len(requests),
            "limit": limit,
            "remaining": limit - len(requests),
            "window": f"{window_size}s sliding"
        },
        "algorithm": "Sliding Window"
    }


@app.get("/api/premium")
async def premium_endpoint(request: Request, tier: str = "free"):
    """
    Demonstrates tiered rate limiting
    Different limits for different user tiers
    """
    client_id = f"{get_client_id(request)}:{tier}"
    rate_limit_stats["total_requests"] += 1
    
    # Different limits per tier
    limits = {
        "free": {"capacity": 3, "rate": 5/60},      # 5 per minute, burst of 3
        "basic": {"capacity": 10, "rate": 20/60},   # 20 per minute, burst of 10
        "premium": {"capacity": 50, "rate": 100/60} # 100 per minute, burst of 50
    }
    
    if tier not in limits:
        raise HTTPException(status_code=400, detail="Invalid tier")
    
    config = limits[tier]
    
    # Initialize bucket
    if client_id not in token_buckets:
        token_buckets[client_id] = TokenBucket(
            capacity=config["capacity"],
            refill_rate=config["rate"]
        )
    
    bucket = token_buckets[client_id]
    
    if not bucket.consume():
        rate_limit_stats["rate_limited"] += 1
        raise HTTPException(
            status_code=429,
            detail={
                "error": "Rate limit exceeded",
                "tier": tier,
                "limits": {
                    "free": "5 req/min",
                    "basic": "20 req/min",
                    "premium": "100 req/min"
                },
                "current_tier_limit": f"{int(config['rate'] * 60)} req/min",
                "suggestion": "Upgrade tier for higher limits"
            }
        )
    
    rate_limit_stats["successful"] += 1
    return {
        "status": "success",
        "tier": tier,
        "rate_limit": bucket.get_status(),
        "message": "Different tiers get different rate limits"
    }


@app.get("/rate-limit/status")
async def rate_limit_status(request: Request):
    """Check current rate limit status"""
    client_id = get_client_id(request)
    
    status = {}
    
    if client_id in token_buckets:
        status["token_bucket"] = token_buckets[client_id].get_status()
    
    if client_id in fixed_windows:
        window = fixed_windows[client_id]
        now = time.time()
        status["fixed_window"] = {
            "used": window["count"],
            "limit": 10,
            "remaining": 10 - window["count"],
            "reset_in": f"{int(window['reset_time'] - now)}s"
        }
    
    if client_id in sliding_windows:
        now = time.time()
        requests = [r for r in sliding_windows[client_id] if now - r < 60]
        status["sliding_window"] = {
            "used": len(requests),
            "limit": 10,
            "remaining": 10 - len(requests)
        }
    
    return {
        "client_id": client_id,
        "rate_limits": status if status else "No rate limit data yet"
    }


@app.get("/stats")
async def get_stats():
    """Get rate limiting statistics"""
    total = rate_limit_stats["total_requests"]
    limited = rate_limit_stats["rate_limited"]
    
    return {
        "stats": rate_limit_stats,
        "rate_limit_percentage": f"{(limited / total * 100) if total > 0 else 0:.2f}%",
        "success_percentage": f"{(rate_limit_stats['successful'] / total * 100) if total > 0 else 0:.2f}%"
    }


@app.post("/reset")
async def reset():
    """Reset all rate limits and stats"""
    global token_buckets, fixed_windows, sliding_windows, rate_limit_stats
    
    token_buckets = {}
    fixed_windows = defaultdict(lambda: {"count": 0, "reset_time": time.time() + 60})
    sliding_windows = defaultdict(list)
    rate_limit_stats = {
        "total_requests": 0,
        "rate_limited": 0,
        "successful": 0
    }
    
    return {"status": "reset"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)
