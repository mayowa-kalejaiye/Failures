"""
Network & Timeout Failure Simulations

Common network-related issues in distributed systems:
1. Slow downstream services
2. Request timeouts
3. Intermittent failures
4. Retry logic with exponential backoff
5. Cascading failures
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel
import asyncio
import random
import time
from datetime import datetime
from typing import Optional

app = FastAPI(title="Network Failure Simulator")


class RetryConfig(BaseModel):
    max_retries: int = 3
    base_delay: float = 1.0
    max_delay: float = 10.0


# Global stats
request_stats = {
    "total_requests": 0,
    "failed_requests": 0,
    "retried_requests": 0,
    "total_retries": 0
}


async def exponential_backoff(attempt: int, base_delay: float = 1.0, max_delay: float = 10.0):
    """Implement exponential backoff with jitter"""
    delay = min(base_delay * (2 ** attempt), max_delay)
    jitter = random.uniform(0, 0.1 * delay)  # Add jitter to prevent thundering herd
    await asyncio.sleep(delay + jitter)
    return delay + jitter


async def simulate_external_api_call(failure_rate: float = 0.3, slow_rate: float = 0.3):
    """Simulate calling an external API that might fail or be slow"""
    
    # Simulate network latency
    await asyncio.sleep(random.uniform(0.1, 0.5))
    
    # Random failures
    if random.random() < failure_rate:
        raise ConnectionError("Failed to connect to external service")
    
    # Random slow responses
    if random.random() < slow_rate:
        await asyncio.sleep(random.uniform(2, 5))
    
    return {"data": "success", "timestamp": datetime.now().isoformat()}


@app.get("/")
async def root():
    return {
        "message": "Network Failure Simulator",
        "endpoints": {
            "slow_endpoint": "/api/slow",
            "timeout": "/api/timeout",
            "intermittent": "/api/intermittent",
            "with_retry": "/api/retry",
            "cascading": "/api/cascade",
            "stats": "/stats"
        }
    }


@app.get("/api/slow")
async def slow_endpoint(delay: Optional[float] = None):
    """
    Simulates a slow endpoint
    Common causes: Slow database queries, external API calls, heavy processing
    """
    if delay is None:
        delay = random.uniform(3, 8)
    
    request_stats["total_requests"] += 1
    
    start = time.time()
    await asyncio.sleep(delay)
    duration = time.time() - start
    
    return {
        "status": "success",
        "message": "This endpoint is intentionally slow",
        "delay": f"{duration:.2f}s",
        "impact": "Users may experience timeouts or poor experience"
    }


@app.get("/api/timeout")
async def timeout_endpoint(timeout: float = 2.0):
    """
    Simulates a request that times out
    Set a low timeout to experience the failure
    """
    request_stats["total_requests"] += 1
    
    try:
        # Try to complete within timeout
        await asyncio.wait_for(
            asyncio.sleep(5),  # Task takes 5 seconds
            timeout=timeout    # But we only wait for timeout seconds
        )
        return {"status": "success"}
        
    except asyncio.TimeoutError:
        request_stats["failed_requests"] += 1
        raise HTTPException(
            status_code=504,
            detail={
                "error": "Gateway Timeout",
                "message": f"Request exceeded timeout of {timeout}s",
                "suggestion": "Consider increasing timeout or optimizing the operation"
            }
        )


@app.get("/api/intermittent")
async def intermittent_failure(failure_rate: float = 0.5):
    """
    Simulates intermittent failures
    These are particularly tricky because they work sometimes
    """
    request_stats["total_requests"] += 1
    
    if random.random() < failure_rate:
        request_stats["failed_requests"] += 1
        
        # Different types of intermittent failures
        error_type = random.choice([
            "connection_reset",
            "dns_failure", 
            "ssl_error",
            "service_unavailable"
        ])
        
        error_messages = {
            "connection_reset": "Connection reset by peer",
            "dns_failure": "Failed to resolve hostname",
            "ssl_error": "SSL handshake failed",
            "service_unavailable": "Service temporarily unavailable"
        }
        
        raise HTTPException(
            status_code=503,
            detail={
                "error": error_type,
                "message": error_messages[error_type],
                "suggestion": "Implement retry logic for intermittent failures"
            }
        )
    
    return {
        "status": "success",
        "message": "Request succeeded this time",
        "note": "But it might fail on the next request"
    }


@app.get("/api/retry")
async def with_retry_logic(max_retries: int = 3):
    """
    Demonstrates proper retry logic with exponential backoff
    This is how you should handle unreliable external services
    """
    request_stats["total_requests"] += 1
    request_stats["retried_requests"] += 1
    
    retry_count = 0
    retry_delays = []
    
    while retry_count <= max_retries:
        try:
            result = await simulate_external_api_call(failure_rate=0.5)
            
            return {
                "status": "success",
                "data": result,
                "retries": retry_count,
                "retry_delays": retry_delays,
                "message": "Request succeeded" + (f" after {retry_count} retries" if retry_count > 0 else " on first attempt")
            }
            
        except ConnectionError as e:
            retry_count += 1
            request_stats["total_retries"] += 1
            
            if retry_count > max_retries:
                request_stats["failed_requests"] += 1
                raise HTTPException(
                    status_code=503,
                    detail={
                        "error": "Max retries exceeded",
                        "message": str(e),
                        "retries": retry_count - 1,
                        "retry_delays": retry_delays
                    }
                )
            
            # Exponential backoff
            delay = await exponential_backoff(retry_count - 1)
            retry_delays.append(f"{delay:.2f}s")


@app.get("/api/cascade")
async def cascading_failure():
    """
    Simulates cascading failures
    When one service fails, it can cause failures in dependent services
    """
    request_stats["total_requests"] += 1
    
    services = ["auth", "database", "cache", "payment"]
    failed_services = []
    
    # Simulate checking multiple services
    for service in services:
        await asyncio.sleep(0.1)  # Small delay
        
        # If one service fails, increase failure rate for others (cascade effect)
        failure_rate = 0.2 + (len(failed_services) * 0.2)
        
        if random.random() < failure_rate:
            failed_services.append(service)
    
    if failed_services:
        request_stats["failed_requests"] += 1
        raise HTTPException(
            status_code=503,
            detail={
                "error": "Cascading failure detected",
                "failed_services": failed_services,
                "message": "Multiple service failures detected",
                "impact": "System is in degraded state",
                "prevention": "Use circuit breakers and bulkheads to prevent cascade"
            }
        )
    
    return {
        "status": "success",
        "services_checked": services,
        "all_healthy": True
    }


@app.get("/stats")
async def get_stats():
    """Get request statistics"""
    total = request_stats["total_requests"]
    failed = request_stats["failed_requests"]
    
    return {
        "requests": request_stats,
        "success_rate": f"{((total - failed) / total * 100) if total > 0 else 0:.2f}%",
        "failure_rate": f"{(failed / total * 100) if total > 0 else 0:.2f}%",
        "avg_retries_per_request": f"{request_stats['total_retries'] / max(request_stats['retried_requests'], 1):.2f}"
    }


@app.post("/reset")
async def reset_stats():
    """Reset statistics"""
    global request_stats
    request_stats = {
        "total_requests": 0,
        "failed_requests": 0,
        "retried_requests": 0,
        "total_retries": 0
    }
    return {"status": "reset"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
