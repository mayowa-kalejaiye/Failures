"""
Resource & Memory Failure Simulations

Common resource-related issues:
1. Memory leaks
2. Resource exhaustion
3. Thread pool saturation
4. Disk space issues
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
import asyncio
import random
import psutil
import os
from datetime import datetime
from typing import List

app = FastAPI(title="Resource Failure Simulator")

# Simulate memory leak
memory_leak_storage: List[bytes] = []

# Track background tasks
background_tasks_running = 0
MAX_BACKGROUND_TASKS = 10


@app.get("/")
async def root():
    return {
        "message": "Resource Failure Simulator",
        "endpoints": {
            "memory_leak": "/resource/memory-leak",
            "memory_status": "/resource/memory-status",
            "cpu_intensive": "/resource/cpu-intensive",
            "background_task": "/resource/background-task",
            "task_status": "/resource/task-status",
            "system_status": "/resource/system",
            "cleanup": "/resource/cleanup (POST)"
        },
        "warning": "These endpoints can affect system performance"
    }


@app.get("/resource/memory-leak")
async def simulate_memory_leak(size_mb: int = 10):
    """
    Simulates a memory leak
    Each call allocates memory that isn't released
    """
    if size_mb > 100:
        raise HTTPException(
            status_code=400,
            detail="Size limited to 100MB per request for safety"
        )
    
    # Allocate memory that won't be garbage collected
    data = b"x" * (size_mb * 1024 * 1024)
    memory_leak_storage.append(data)
    
    # Get current process memory
    process = psutil.Process(os.getpid())
    memory_info = process.memory_info()
    
    return {
        "status": "memory allocated",
        "allocated_mb": size_mb,
        "total_leaked_mb": len(memory_leak_storage) * size_mb,
        "process_memory": {
            "rss_mb": memory_info.rss / 1024 / 1024,  # Resident Set Size
            "vms_mb": memory_info.vms / 1024 / 1024,  # Virtual Memory Size
        },
        "warning": "Memory not released - will cause issues over time",
        "impact": "In production, this leads to OOM (Out of Memory) errors"
    }


@app.get("/resource/memory-status")
async def memory_status():
    """Check current memory usage"""
    process = psutil.Process(os.getpid())
    memory_info = process.memory_info()
    
    system_memory = psutil.virtual_memory()
    
    return {
        "process": {
            "rss_mb": round(memory_info.rss / 1024 / 1024, 2),
            "vms_mb": round(memory_info.vms / 1024 / 1024, 2),
            "percent": round(process.memory_percent(), 2)
        },
        "system": {
            "total_mb": round(system_memory.total / 1024 / 1024, 2),
            "available_mb": round(system_memory.available / 1024 / 1024, 2),
            "used_percent": system_memory.percent
        },
        "leak_storage": {
            "items": len(memory_leak_storage),
            "estimated_mb": len(memory_leak_storage) * 10
        }
    }


@app.get("/resource/cpu-intensive")
async def cpu_intensive_task(duration: int = 5):
    """
    Simulates CPU-intensive operation
    Blocks the event loop (bad practice!)
    """
    if duration > 10:
        raise HTTPException(
            status_code=400,
            detail="Duration limited to 10 seconds for safety"
        )
    
    start = datetime.now()
    
    # CPU-intensive calculation (blocking!)
    result = 0
    iterations = duration * 100_000_000
    
    for i in range(iterations):
        result += i * i
    
    elapsed = (datetime.now() - start).total_seconds()
    
    return {
        "status": "completed",
        "duration": f"{elapsed:.2f}s",
        "result": result % 1000000,  # Just a sample
        "warning": "This blocks the event loop!",
        "impact": "All other requests are blocked during this time",
        "solution": "Use background tasks or separate worker processes"
    }


async def long_running_background_task(task_id: int, duration: int):
    """Simulate a long-running background task"""
    global background_tasks_running
    
    try:
        await asyncio.sleep(duration)
    finally:
        background_tasks_running -= 1


@app.get("/resource/background-task")
async def create_background_task(
    duration: int = 30,
    background_tasks: BackgroundTasks = None
):
    """
    Creates background tasks
    Too many can exhaust resources
    """
    global background_tasks_running
    
    if background_tasks_running >= MAX_BACKGROUND_TASKS:
        raise HTTPException(
            status_code=503,
            detail={
                "error": "Too many background tasks",
                "current": background_tasks_running,
                "max": MAX_BACKGROUND_TASKS,
                "message": "System is overloaded with background tasks",
                "impact": "Can lead to resource exhaustion"
            }
        )
    
    task_id = background_tasks_running + 1
    background_tasks_running += 1
    
    # Create background task
    asyncio.create_task(long_running_background_task(task_id, duration))
    
    return {
        "status": "background task created",
        "task_id": task_id,
        "duration": f"{duration}s",
        "active_tasks": background_tasks_running,
        "max_tasks": MAX_BACKGROUND_TASKS,
        "remaining_slots": MAX_BACKGROUND_TASKS - background_tasks_running
    }


@app.get("/resource/task-status")
async def task_status():
    """Get background task status"""
    return {
        "active_tasks": background_tasks_running,
        "max_tasks": MAX_BACKGROUND_TASKS,
        "available_slots": MAX_BACKGROUND_TASKS - background_tasks_running,
        "utilization": f"{(background_tasks_running / MAX_BACKGROUND_TASKS * 100):.1f}%"
    }


@app.get("/resource/system")
async def system_status():
    """Get overall system resource status"""
    cpu_percent = psutil.cpu_percent(interval=0.1)
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    
    process = psutil.Process(os.getpid())
    
    return {
        "cpu": {
            "percent": cpu_percent,
            "count": psutil.cpu_count(),
            "per_cpu": psutil.cpu_percent(interval=0.1, percpu=True)
        },
        "memory": {
            "total_gb": round(memory.total / 1024 / 1024 / 1024, 2),
            "available_gb": round(memory.available / 1024 / 1024 / 1024, 2),
            "used_percent": memory.percent
        },
        "disk": {
            "total_gb": round(disk.total / 1024 / 1024 / 1024, 2),
            "used_gb": round(disk.used / 1024 / 1024 / 1024, 2),
            "free_gb": round(disk.free / 1024 / 1024 / 1024, 2),
            "used_percent": disk.percent
        },
        "process": {
            "cpu_percent": process.cpu_percent(),
            "memory_mb": round(process.memory_info().rss / 1024 / 1024, 2),
            "threads": process.num_threads()
        }
    }


@app.post("/resource/cleanup")
async def cleanup():
    """Clean up leaked resources"""
    global memory_leak_storage, background_tasks_running
    
    leaked_mb = len(memory_leak_storage) * 10
    memory_leak_storage.clear()
    
    return {
        "status": "cleanup completed",
        "memory_freed_mb": leaked_mb,
        "active_tasks": background_tasks_running,
        "message": "Memory leak storage cleared"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8004)
