"""
EXERCISE 1: Database Connection Pool
====================================

YOUR MISSION: Build a connection pool simulator and see it break!

CONCEPTS TO LEARN:
- Connection pools (limited resources)
- Pool exhaustion (what happens when they're all used)
- Slow queries (queries that take forever)
- Resource management

RUN: uvicorn exercises.ex1_db_starter:app --reload --port 8000
"""

from fastapi import FastAPI, HTTPException
import asyncio
from datetime import datetime

app = FastAPI(title="DB Exercise")

# STEP 1: Build a ConnectionPool class
# ====================================
class ConnectionPool:
    """Simulates a database connection pool"""
    
    def __init__(self, max_connections: int = 5):
        # TODO: Store max_connections
        # TODO: Track available_connections (starts at max)
        # TODO: Maybe track active queries?
        pass
    
    async def acquire_connection(self):
        """
        TODO: Try to get a connection
        - If available_connections > 0, decrease it and return True
        - If none available, return False
        """
        pass
    
    def release_connection(self):
        """
        TODO: Give back a connection
        - Increase available_connections (but don't go over max!)
        """
        pass
    
    def get_stats(self):
        """
        TODO: Return a dictionary with pool info:
        - total_connections
        - available_connections  
        - in_use (calculated)
        """
        pass


# STEP 2: Create your pool
# ========================
# TODO: Create a global ConnectionPool with 5 max connections
# db_pool = ConnectionPool(max_connections=5)


# STEP 3: Build the endpoints
# ===========================

@app.get("/")
async def home():
    return {
        "message": "Database Failure Simulator",
        "endpoints": {
            "/slow-query": "Simulate a slow database query",
            "/health": "Check connection pool status",
            "/exhaust-pool": "Take all connections at once!"
        }
    }


@app.get("/slow-query")
async def slow_query():
    """
    TODO: Simulate a slow database query
    
    Steps:
    1. Try to acquire a connection from db_pool
    2. If you can't get one, raise HTTPException(status_code=503, detail="No connections available")
    3. If you got one, sleep for 5 seconds using: await asyncio.sleep(5)
    4. Release the connection
    5. Return success message
    """
    return {"status": "TODO: Implement me!"}


@app.get("/health")
async def health():
    """
    TODO: Return the pool statistics
    
    Call db_pool.get_stats() and return it
    """
    return {"status": "TODO: Implement me!"}


@app.get("/exhaust-pool")
async def exhaust_pool():
    """
    CHALLENGE: Take ALL connections and hold them
    
    TODO:
    1. Try to acquire ALL connections in a loop
    2. Sleep for 10 seconds
    3. Release them all
    4. Return how many you grabbed
    
    HINT: You might need a list to track which connections you got
    """
    return {"status": "TODO: Implement me!"}


# ============================================================================
# TESTING INSTRUCTIONS
# ============================================================================
# 
# 1. Run the server:
#    uvicorn exercises.ex1_db_starter:app --reload --port 8000
#
# 2. Test slow query:
#    curl http://localhost:8000/slow-query
#
# 3. Test pool exhaustion - run these in 6 different terminals at same time:
#    curl http://localhost:8000/slow-query
#    curl http://localhost:8000/slow-query  
#    curl http://localhost:8000/slow-query
#    curl http://localhost:8000/slow-query
#    curl http://localhost:8000/slow-query
#    curl http://localhost:8000/slow-query  # <-- This should fail!
#
# 4. While slow queries running, check health:
#    curl http://localhost:8000/health
#
# ============================================================================
# BONUS CHALLENGES
# ============================================================================
#
# 1. Add a timeout - if can't get connection in 2 seconds, fail
# 2. Add query logging - track which queries are running
# 3. Add auto-recovery - detect hung queries and kill them
# 4. Add metrics - track average wait time for connections
#
# ============================================================================
