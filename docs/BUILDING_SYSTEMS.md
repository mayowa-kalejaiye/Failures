# Building Systems Guide

This is the second stage of the project.

The exercises teach the basics. This guide helps you take those basics and use them in a small real system.

## The goal of this stage

Do not try to build everything at once. Start with one component, make it understandable, and keep the code small enough to read.

## What to build first

Start with the authentication system.

It is a good first component because it uses the same ideas as the exercises:

- connection pooling
- retries
- timeouts
- rate limiting
- careful error handling

## How the component should feel

Each component should be:

- simple to understand
- easy to run locally
- small enough to test
- written in steps
- documented for a beginner

## Common structure

```text
component_name/
README.md
config.py
api.py
core.py
tests/
```

## Beginner-friendly build plan

### Step 1: Read the purpose

Write down what the component is for in one or two sentences.

### Step 2: Build the happy path

Make the simplest version work first.

### Step 3: Add one safety feature

Add one thing that protects the system when something goes wrong.

### Step 4: Test the failure

Make sure the safety feature really works.

### Step 5: Add the next piece

Repeat with the next feature.

## Suggested component order

1. Authentication system
2. Payment processing
3. File upload service
4. Notification system
5. API gateway

You do not need to finish all of them. One well-built component is enough to learn a lot.

## What to focus on

When building a component, ask these questions:

1. What is the smallest useful version of this feature?
2. What can fail first?
3. What should happen if it fails?
4. How can I test that behavior?

## What not to do

- Do not start with advanced architecture.
- Do not add many features before one works.
- Do not hide the code behind too many layers.
- Do not copy patterns that you do not yet understand.

## A good learning rhythm

1. Read a small part.
2. Write a small part.
3. Run it.
4. Fix it.
5. Move on.

## Next step

Open [components/auth_system/README.md](../components/auth_system/README.md) and start with the first small feature there.

### Phase 3: Failure Handling (2-3 hours)

1. **Add connection pools** - For DB access
2. **Add rate limiting** - Protect endpoints
3. **Add circuit breakers** - For external services
4. **Add retry logic** - For transient failures
5. **Add timeouts** - Prevent hanging requests

### Phase 4: Testing Failures (1-2 hours)

1. **Write failure tests** - Simulate each failure mode
2. **Verify recovery** - System returns to normal
3. **Load testing** - Behavior under load
4. **Chaos testing** - Random failures

### Phase 5: Production Readiness (1-2 hours)

1. **Add monitoring** - Metrics and logging
2. **Add health checks** - /health endpoint
3. **Document** - API docs, runbooks
4. **Deploy** - Docker, config, secrets

---

## Component Template

Use this template to start each new component:

```python
"""
Component: [NAME]
Purpose: [WHAT IT DOES]
Failure Patterns: [LIST PATTERNS USED]
"""

import asyncio
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Dict, Any
import logging

# Import your failure handling modules
from circuit_breaker import CircuitBreaker
from rate_limiting import TokenBucket

logger = logging.getLogger(__name__)

# ============================================
# Configuration
# ============================================

@dataclass
class ComponentConfig:
    """Configuration for this component"""
    db_pool_size: int = 10
    rate_limit_requests: int = 100
    rate_limit_window: int = 60
    circuit_breaker_threshold: int = 5
    circuit_breaker_timeout: int = 30
    request_timeout: int = 30

# ============================================
# Core Business Logic
# ============================================

class YourComponent:
    """
    Main component class
    
    Handles:
    - [Feature 1]
    - [Feature 2]
    - [Feature 3]
    """
    
    def __init__(self, config: ComponentConfig):
        self.config = config
        
        # Set up failure handling
        self.circuit_breaker = CircuitBreaker(
            failure_threshold=config.circuit_breaker_threshold,
            timeout_duration=config.circuit_breaker_timeout
        )
        
        self.rate_limiter = TokenBucket(
            capacity=config.rate_limit_requests,
            refill_rate=config.rate_limit_requests / config.rate_limit_window
        )
        
        logger.info(f"Initialized {self.__class__.__name__}")
    
    async def do_something(self, param: str) -> Dict[str, Any]:
        """
        Core functionality
        
        Failures handled:
        - Rate limiting
        - Circuit breaker
        - Timeouts
        """
        
        # Check rate limit
        if not self.rate_limiter.consume(1):
            raise RateLimitExceeded("Too many requests")
        
        # Use circuit breaker for external calls
        try:
            result = await self.circuit_breaker.call(
                self._external_call,
                param
            )
            return result
        except Exception as e:
            logger.error(f"Operation failed: {e}")
            raise
    
    async def _external_call(self, param: str) -> Dict[str, Any]:
        """
        Internal method that might fail
        """
        # Implementation here
        pass

# ============================================
# Custom Exceptions
# ============================================

class RateLimitExceeded(Exception):
    pass

class ServiceUnavailable(Exception):
    pass

# ============================================
# FastAPI Endpoints
# ============================================

from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel

app = FastAPI(title="Your Component API")

# Initialize component
config = ComponentConfig()
component = YourComponent(config)

class YourRequest(BaseModel):
    param: str

@app.post("/api/action")
async def perform_action(request: YourRequest):
    """
    Perform an action
    
    Failures:
    - 429: Rate limit exceeded
    - 503: Service unavailable (circuit breaker open)
    - 504: Timeout
    """
    try:
        result = await component.do_something(request.param)
        return {"success": True, "data": result}
    
    except RateLimitExceeded:
        raise HTTPException(status_code=429, detail="Rate limit exceeded")
    
    except ServiceUnavailable:
        raise HTTPException(status_code=503, detail="Service temporarily unavailable")
    
    except asyncio.TimeoutError:
        raise HTTPException(status_code=504, detail="Request timeout")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "circuit_breaker": component.circuit_breaker.state,
        "timestamp": datetime.utcnow().isoformat()
    }

# ============================================
# Entry Point
# ============================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

---

## Learning Path

### Week 1: Authentication System

- Understand user flows
- Design DB schema
- Implement with failure handling
- Test and deploy

### Week 2: Payment Processing

- Learn payment concepts
- Implement idempotency
- Test edge cases
- Add audit logging

### Week 3: File Upload Service

- Understand streaming
- Implement chunked uploads
- Add virus scanning
- Test with large files

### Week 4: Notification System

- Design queue architecture
- Implement multi-provider
- Add retry logic
- Test delivery tracking

### Week 5: API Gateway

- Learn routing patterns
- Implement load balancing
- Add circuit breakers
- Test failover

---

## Success Metrics

For each component you build, measure:

### Functionality

- All happy path features work
- All endpoints return correct responses
- Data is persisted correctly

### Resilience

- Gracefully handles DB failures
- Recovers from external service outages
- Prevents resource exhaustion
- Rate limiting works correctly

### Production Readiness

- Has comprehensive tests
- Has monitoring and logging
- Has health check endpoint
- Has documentation

---

## Getting Started

1. **Choose a component** - Start with Authentication (it's the simplest)
2. **Create the folder structure**
3. **Copy the template** - Customize for your component
4. **Implement step by step** - Follow the 5 phases
5. **Test thoroughly** - Happy path AND failure modes
6. **Document** - Write a README for the component

---

## Pro Tips

### Start Simple

Don't build everything at once. Start with:

1. One endpoint
2. One failure pattern
3. One test

Then iterate.

### Think Production

Ask yourself:

- What happens if the DB is down?
- What if this endpoint gets 1000 requests/second?
- How do I debug this in production?
- What metrics do I need?

### Reuse Your Code

Build a `common/` folder with:

- Connection pool implementations
- Rate limiter implementations
- Circuit breaker implementations
- Monitoring utilities

Then import them in each component.

---

## Next Steps

1. Read through this entire guide
2. Look at the component templates in `/components/` folder
3. Pick your first component to build
4. Follow the 5-phase implementation process
5. Share your completed component!

---

**Remember**: You're not just learning to code. You're learning to build systems that DON'T break in production!
