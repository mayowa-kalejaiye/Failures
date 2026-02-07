"""
Circuit Breaker Pattern

Prevents cascading failures by stopping requests to failing services:
- Closed: Normal operation, requests pass through
- Open: Service is failing, reject requests immediately
- Half-Open: Test if service recovered

This is crucial for maintaining system stability when dependencies fail.
"""

from fastapi import FastAPI, HTTPException, Request
from enum import Enum
import asyncio
import random
import time
from datetime import datetime, timedelta
from typing import Dict, Optional

app = FastAPI(title="Circuit Breaker Pattern Simulator")


class CircuitState(Enum):
    CLOSED = "closed"      # Working normally
    OPEN = "open"          # Failing, reject requests
    HALF_OPEN = "half_open"  # Testing recovery


class CircuitBreaker:
    """
    Circuit Breaker Implementation
    
    Closed -> Open: After failure_threshold failures
    Open -> Half-Open: After timeout_duration
    Half-Open -> Closed: After success_threshold successes
    Half-Open -> Open: On any failure
    """
    
    def __init__(
        self,
        failure_threshold: int = 5,
        timeout_duration: float = 30.0,
        success_threshold: int = 2
    ):
        self.failure_threshold = failure_threshold
        self.timeout_duration = timeout_duration  # seconds
        self.success_threshold = success_threshold
        
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time: Optional[float] = None
        
        # Statistics
        self.total_calls = 0
        self.successful_calls = 0
        self.failed_calls = 0
        self.rejected_calls = 0
    
    async def call(self, func, *args, **kwargs):
        """Execute function with circuit breaker protection"""
        self.total_calls += 1
        
        # Check if we should attempt the call
        if not self._can_attempt():
            self.rejected_calls += 1
            raise HTTPException(
                status_code=503,
                detail={
                    "error": "Circuit breaker is OPEN",
                    "message": "Service is temporarily unavailable",
                    "state": self.state.value,
                    "retry_after": self._get_retry_after(),
                    "explanation": "Too many failures detected. Circuit breaker prevents further damage."
                }
            )
        
        try:
            # Attempt the call
            result = await func(*args, **kwargs)
            self._on_success()
            return result
            
        except Exception as e:
            self._on_failure()
            raise
    
    def _can_attempt(self) -> bool:
        """Check if we should attempt the call"""
        if self.state == CircuitState.CLOSED:
            return True
        
        if self.state == CircuitState.OPEN:
            # Check if timeout has elapsed
            if self.last_failure_time and \
               time.time() - self.last_failure_time >= self.timeout_duration:
                self.state = CircuitState.HALF_OPEN
                self.success_count = 0
                return True
            return False
        
        if self.state == CircuitState.HALF_OPEN:
            return True
        
        return False
    
    def _on_success(self):
        """Handle successful call"""
        self.successful_calls += 1
        
        if self.state == CircuitState.HALF_OPEN:
            self.success_count += 1
            
            # Enough successes to close circuit
            if self.success_count >= self.success_threshold:
                self.state = CircuitState.CLOSED
                self.failure_count = 0
                self.success_count = 0
        
        # In closed state, reset failure count on success
        if self.state == CircuitState.CLOSED:
            self.failure_count = 0
    
    def _on_failure(self):
        """Handle failed call"""
        self.failed_calls += 1
        self.last_failure_time = time.time()
        
        if self.state == CircuitState.HALF_OPEN:
            # Any failure in half-open -> back to open
            self.state = CircuitState.OPEN
            self.failure_count = 0
            return
        
        if self.state == CircuitState.CLOSED:
            self.failure_count += 1
            
            # Too many failures -> open circuit
            if self.failure_count >= self.failure_threshold:
                self.state = CircuitState.OPEN
    
    def _get_retry_after(self) -> str:
        """Get time until circuit might close"""
        if self.state != CircuitState.OPEN or not self.last_failure_time:
            return "unknown"
        
        elapsed = time.time() - self.last_failure_time
        remaining = max(0, self.timeout_duration - elapsed)
        return f"{int(remaining)} seconds"
    
    def get_status(self) -> dict:
        """Get current circuit breaker status"""
        return {
            "state": self.state.value,
            "failure_count": self.failure_count,
            "success_count": self.success_count,
            "configuration": {
                "failure_threshold": self.failure_threshold,
                "timeout_duration": f"{self.timeout_duration}s",
                "success_threshold": self.success_threshold
            },
            "statistics": {
                "total_calls": self.total_calls,
                "successful": self.successful_calls,
                "failed": self.failed_calls,
                "rejected": self.rejected_calls
            },
            "retry_after": self._get_retry_after() if self.state == CircuitState.OPEN else None
        }


# Simulate different services with different reliability
services = {
    "reliable": CircuitBreaker(failure_threshold=5, timeout_duration=10),
    "unreliable": CircuitBreaker(failure_threshold=3, timeout_duration=20),
    "flaky": CircuitBreaker(failure_threshold=5, timeout_duration=15)
}


async def call_reliable_service():
    """Simulates a mostly reliable external service"""
    await asyncio.sleep(0.1)
    if random.random() < 0.1:  # 10% failure rate
        raise ConnectionError("Service temporarily unavailable")
    return {"service": "reliable", "data": "success"}


async def call_unreliable_service():
    """Simulates an unreliable external service"""
    await asyncio.sleep(0.2)
    if random.random() < 0.6:  # 60% failure rate
        raise ConnectionError("Service is having issues")
    return {"service": "unreliable", "data": "success"}


async def call_flaky_service():
    """Simulates a flaky service that alternates between working and failing"""
    await asyncio.sleep(0.15)
    
    # Fail in batches to trigger circuit breaker
    second = int(time.time()) % 60
    if second % 20 < 10:  # Fail for 10 seconds every 20 seconds
        raise ConnectionError("Service is in failure mode")
    return {"service": "flaky", "data": "success"}


@app.get("/")
async def root():
    return {
        "message": "Circuit Breaker Pattern Simulator",
        "endpoints": {
            "reliable_service": "/api/reliable",
            "unreliable_service": "/api/unreliable",
            "flaky_service": "/api/flaky",
            "status": "/circuit-breaker/status",
            "reset": "/reset (POST)"
        },
        "tip": "Call unreliable or flaky services repeatedly to see circuit breaker in action",
        "states": {
            "CLOSED": "Normal operation",
            "OPEN": "Service failing, requests rejected",
            "HALF_OPEN": "Testing if service recovered"
        }
    }


@app.get("/api/reliable")
async def reliable_endpoint():
    """
    Call a mostly reliable service through circuit breaker
    This should rarely trip the circuit breaker
    """
    try:
        result = await services["reliable"].call(call_reliable_service)
        return {
            "status": "success",
            "result": result,
            "circuit_breaker": services["reliable"].get_status()
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Service call failed",
                "message": str(e),
                "circuit_breaker": services["reliable"].get_status()
            }
        )


@app.get("/api/unreliable")
async def unreliable_endpoint():
    """
    Call an unreliable service through circuit breaker
    This will trip the circuit breaker quickly due to high failure rate
    """
    try:
        result = await services["unreliable"].call(call_unreliable_service)
        return {
            "status": "success",
            "result": result,
            "circuit_breaker": services["unreliable"].get_status()
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail={
                "error": "Service call failed",
                "message": str(e),
                "circuit_breaker": services["unreliable"].get_status()
            }
        )


@app.get("/api/flaky")
async def flaky_endpoint():
    """
    Call a flaky service through circuit breaker
    Demonstrates circuit breaker opening and closing over time
    """
    try:
        result = await services["flaky"].call(call_flaky_service)
        return {
            "status": "success",
            "result": result,
            "circuit_breaker": services["flaky"].get_status()
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail={
                "error": "Service call failed",
                "message": str(e),
                "circuit_breaker": services["flaky"].get_status()
            }
        )


@app.get("/circuit-breaker/status")
async def get_all_status():
    """Get status of all circuit breakers"""
    return {
        service_name: breaker.get_status()
        for service_name, breaker in services.items()
    }


@app.get("/circuit-breaker/{service_name}")
async def get_service_status(service_name: str):
    """Get status of a specific circuit breaker"""
    if service_name not in services:
        raise HTTPException(status_code=404, detail="Service not found")
    
    return services[service_name].get_status()


@app.post("/reset")
async def reset():
    """Reset all circuit breakers"""
    global services
    
    services = {
        "reliable": CircuitBreaker(failure_threshold=5, timeout_duration=10),
        "unreliable": CircuitBreaker(failure_threshold=3, timeout_duration=20),
        "flaky": CircuitBreaker(failure_threshold=5, timeout_duration=15)
    }
    
    return {
        "status": "reset",
        "message": "All circuit breakers reset",
        "services": list(services.keys())
    }


@app.get("/demo/scenario")
async def demo_scenario():
    """
    Demonstrates a complete circuit breaker scenario
    Shows transition through all states
    """
    scenario = {
        "explanation": "Circuit Breaker State Transitions",
        "states": {
            "CLOSED": {
                "description": "Normal operation",
                "behavior": "All requests pass through",
                "transition": f"Opens after {services['reliable'].failure_threshold} consecutive failures"
            },
            "OPEN": {
                "description": "Service is failing",
                "behavior": "All requests rejected immediately (fail-fast)",
                "benefit": "Prevents cascading failures and gives service time to recover",
                "transition": f"Transitions to HALF_OPEN after {services['reliable'].timeout_duration}s"
            },
            "HALF_OPEN": {
                "description": "Testing recovery",
                "behavior": "Limited requests allowed to test service health",
                "transition": f"Closes after {services['reliable'].success_threshold} successes, Opens on any failure"
            }
        },
        "current_status": {
            service_name: breaker.get_status()
            for service_name, breaker in services.items()
        },
        "try_this": [
            "1. Call /api/unreliable repeatedly (5+ times)",
            "2. Watch circuit breaker OPEN after failures",
            "3. Wait for timeout period",
            "4. See it transition to HALF_OPEN",
            "5. Successful calls will CLOSE it again"
        ]
    }
    
    return scenario


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003)
