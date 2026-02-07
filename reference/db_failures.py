"""
Database Failure Simulations

Common database-related failures you'll encounter in production:
1. Connection timeouts
2. Connection pool exhaustion
3. Query timeouts
4. Deadlocks
5. Connection drops
"""

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
import asyncio
import random
import time
from datetime import datetime
from typing import Dict, List

app = FastAPI(title="Database Failure Simulator")

# Simulate a connection pool with limited connections
class ConnectionPool:
    def __init__(self, max_connections: int = 5):
        self.max_connections = max_connections
        self.active_connections = 0
        self.total_requests = 0
        self.failed_requests = 0
    
    async def acquire(self, timeout: float = 5.0):
        """Simulate acquiring a database connection"""
        self.total_requests += 1
        start_time = time.time()
        
        while self.active_connections >= self.max_connections:
            if time.time() - start_time > timeout:
                self.failed_requests += 1
                raise TimeoutError("Connection pool exhausted - timeout waiting for connection")
            await asyncio.sleep(0.1)
        
        self.active_connections += 1
        return f"connection_{self.active_connections}"
    
    def release(self):
        """Release a connection back to the pool"""
        if self.active_connections > 0:
            self.active_connections -= 1

pool = ConnectionPool(max_connections=3)


@app.get("/")
async def root():
    return {
        "message": "Database Failure Simulator",
        "endpoints": {
            "health": "/health",
            "slow_query": "/query/slow",
            "timeout": "/query/timeout",
            "pool_exhaustion": "/query/pool-test",
            "deadlock": "/query/deadlock",
            "connection_drop": "/query/drop",
            "stats": "/stats"
        }
    }


@app.get("/health")
async def health():
    """Simple health check"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}


@app.get("/query/slow")
async def slow_query():
    """
    Simulates a slow database query
    Common causes: Missing indexes, full table scans, complex joins
    """
    query_time = random.uniform(2, 5)  # 2-5 seconds
    
    try:
        conn = await pool.acquire(timeout=10)
        await asyncio.sleep(query_time)  # Simulate slow query
        pool.release()
        
        return {
            "status": "success",
            "message": "Query completed (slowly)",
            "execution_time": f"{query_time:.2f}s",
            "warning": "This query would benefit from indexing!"
        }
    except TimeoutError as e:
        raise HTTPException(status_code=504, detail=str(e))


@app.get("/query/timeout")
async def query_timeout():
    """
    Simulates a query timeout
    Common in production when queries take too long
    """
    try:
        conn = await pool.acquire(timeout=2)  # Short timeout
        
        # Simulate a very long-running query
        await asyncio.sleep(10)
        pool.release()
        
        return {"status": "success"}
    except TimeoutError:
        raise HTTPException(
            status_code=504,
            detail="Query timeout: Database query exceeded maximum execution time"
        )
    except Exception as e:
        pool.release()
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/query/pool-test")
async def pool_exhaustion_test():
    """
    Test connection pool exhaustion
    Hit this endpoint multiple times simultaneously to exhaust the pool
    """
    try:
        conn = await pool.acquire(timeout=3)
        
        # Hold the connection for a while
        await asyncio.sleep(2)
        pool.release()
        
        return {
            "status": "success",
            "connection": conn,
            "pool_stats": {
                "active": pool.active_connections,
                "max": pool.max_connections,
                "available": pool.max_connections - pool.active_connections
            }
        }
    except TimeoutError as e:
        raise HTTPException(
            status_code=503,
            detail=f"Service unavailable: {str(e)}"
        )


@app.get("/query/deadlock")
async def simulate_deadlock():
    """
    Simulates a database deadlock scenario
    Deadlocks occur when two transactions wait for each other
    """
    # Randomly fail to simulate deadlock detection
    if random.random() < 0.3:  # 30% chance of deadlock
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Deadlock detected",
                "message": "Transaction was deadlocked and has been chosen as the victim",
                "retry": "Please retry the operation",
                "prevention": "Consider using optimistic locking or reducing transaction scope"
            }
        )
    
    return {
        "status": "success",
        "message": "Transaction completed successfully"
    }


@app.get("/query/drop")
async def connection_drop():
    """
    Simulates sudden connection drop
    Common causes: Network issues, database restarts, firewall timeouts
    """
    try:
        conn = await pool.acquire()
        
        # Randomly simulate connection drop
        if random.random() < 0.4:  # 40% chance
            pool.release()
            raise HTTPException(
                status_code=500,
                detail={
                    "error": "Connection lost",
                    "message": "Lost connection to database during query execution",
                    "type": "Connection Error",
                    "suggestion": "Implement retry logic with exponential backoff"
                }
            )
        
        await asyncio.sleep(1)
        pool.release()
        return {"status": "success", "data": "Query completed"}
        
    except HTTPException:
        raise
    except Exception as e:
        pool.release()
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/stats")
async def get_stats():
    """Get connection pool statistics"""
    return {
        "pool": {
            "max_connections": pool.max_connections,
            "active_connections": pool.active_connections,
            "available_connections": pool.max_connections - pool.active_connections
        },
        "requests": {
            "total": pool.total_requests,
            "failed": pool.failed_requests,
            "success_rate": f"{((pool.total_requests - pool.failed_requests) / pool.total_requests * 100) if pool.total_requests > 0 else 0:.2f}%"
        }
    }


@app.post("/reset")
async def reset_stats():
    """Reset statistics"""
    global pool
    pool = ConnectionPool(max_connections=3)
    return {"status": "reset", "message": "Statistics reset"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
