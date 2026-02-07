# 🛠️ Tools & Utilities

Helper scripts for testing and running the project.

## Files

### [launcher.py](launcher.py)
Interactive launcher for running different failure scenarios.

**Usage:**
```bash
python tools/launcher.py
```

**Features:**
- Menu-driven interface
- Launch any reference scenario
- Automatic port management
- Easy testing of failures

**Example:**
```
=================================
Backend Failure Scenarios Launcher
=================================

Select a scenario to launch:
1. Database Failures (Port 8000)
2. Network Failures (Port 8001)
3. Rate Limiting (Port 8002)
4. Circuit Breaker (Port 8003)
5. Resource Failures (Port 8004)
6. Exit

Enter choice (1-6): _
```

### [test_scenarios.py](test_scenarios.py)
Automated tests for all failure scenarios.

**Usage:**
```bash
python tools/test_scenarios.py
```

**Features:**
- Automated testing of all reference implementations
- Validates failure behavior
- Checks recovery mechanisms
- Generates test report

**What it tests:**
- ✅ Database connection pool exhaustion
- ✅ Network retry logic
- ✅ Rate limiting enforcement
- ✅ Circuit breaker state transitions
- ✅ Resource limit handling

**Example Output:**
```
Running Automated Tests...
==========================

Testing Database Failures...
  ✓ Slow query works
  ✓ Pool exhaustion returns 503
  ✓ Pool recovers correctly

Testing Network Failures...
  ✓ Retry logic succeeds eventually
  ✓ Timeout prevents hanging
  
...

Results: 15/15 tests passed
```

## Adding Your Own Tools

As you build more components, add utility scripts here:

```bash
# Example: Health check script
tools/
├── launcher.py
├── test_scenarios.py
├── health_check.py          # Check all services
├── load_test.py             # Load testing
└── chaos_test.py            # Chaos engineering
```

## Tips

### Quick Start All Services
```bash
# Run the launcher and pick a scenario
python tools/launcher.py
```

### Run All Tests
```bash
# Validate everything works
python tools/test_scenarios.py
```

### Custom Scripts
Create your own utilities:
```python
# tools/my_tool.py
import sys
sys.path.append('..')

from reference.circuit_breaker import CircuitBreaker
# Your custom tool code...
```

---

💡 **Pro Tip:** Use these tools to quickly validate your implementations work correctly!
