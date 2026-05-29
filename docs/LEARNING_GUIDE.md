# Learning Guide

This project is meant to help you learn by building small things first. It is fine to be a beginner or to feel rusty. You do not need to know everything before you start.

## How to use the project

Work through the material in this order:

1. Read [START_HERE.md](START_HERE.md).
2. Open the first exercise file.
3. Read the TODO comments.
4. Implement one small method.
5. Test that method before moving on.

## Learning path

### Exercise 1: Database connection pools

File: `exercises/ex1_db_starter.py`

What you will build:

- a simple connection pool class
- acquire and release methods
- a way to see when the pool is full
- a health check endpoint

What you will learn:

- why databases have limits
- what pool exhaustion looks like
- how to think about resource cleanup

### Exercise 2: Network retries and timeouts

File: `exercises/ex2_network_starter.py`

What you will build:

- a flaky API simulator
- retry logic with backoff
- timeout handling
- a small example of cascading failure

What you will learn:

- why retries are useful
- when not to retry
- how timeouts protect a service

### Exercise 3: Rate limiting

File: `exercises/ex3_ratelimit_starter.py`

What you will build:

- a token bucket limiter
- token refill logic
- a protected endpoint
- a response for too many requests

What you will learn:

- how rate limits protect services
- how to think about bursts of traffic
- why HTTP 429 matters

## How to work

Keep the process small and calm.

1. Change one method at a time.
2. Run the code often.
3. Read error messages carefully.
4. Keep notes about what you tried.
5. Use the solution files only when you need a hint.

## Good habits

- Start with the simplest method.
- Test the happy path first.
- Add failure cases after the basics work.
- Take breaks when you feel stuck.

## What success looks like

You are making progress when you can:

- explain what the code is doing
- predict what might fail
- fix a bug without guessing blindly
- finish a small exercise on your own

## When you get stuck

Use this order:

1. Read the error message.
2. Check the TODOs again.
3. Compare with the hints in the exercise.
4. Try a smaller change.
5. Ask for help if you still need it.

## First session example

Start with the connection pool constructor:

```python
class ConnectionPool:
    def __init__(self, max_connections: int = 5):
        self.max_connections = max_connections
        self.available_connections = max_connections
```

Test it with a short script:

```python
pool = ConnectionPool(3)
print(pool.available_connections)
```

That's it! Small steps. Build up.

## Ready?

Open [exercises/ex1_db_starter.py](exercises/ex1_db_starter.py) and start coding!

Remember: **Struggle = Learning**. Embrace it!
