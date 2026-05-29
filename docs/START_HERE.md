# Start Here

If this project feels like too much at first, start here and take it one step at a time. The exercises are meant to help beginners and rusty developers rebuild confidence.

## Before you start (Foundations)

If you are new to APIs, HTTP, or running a local Python service, read the short primer in [FOUNDATIONS.md](FOUNDATIONS.md) first. It covers:

- what an API is
- basic HTTP methods
- JSON examples and `curl` commands
- how to run a FastAPI app locally with `uvicorn`

Completing Foundations will make the exercises and later system-building guides much easier to follow.

## What changed

This project used to be more of a read-and-run demo. It is now meant to be a learning path where you write the code yourself.

## Your first 30 minutes

1. Read this file.
2. Open [exercises/ex1_db_starter.py](exercises/ex1_db_starter.py).
3. Read every TODO before writing code.
4. Implement the `__init__` method.
5. Run the file and check the result.

Simple starting point:

```python
class ConnectionPool:
    def __init__(self, max_connections: int = 5):
        self.max_connections = max_connections
        self.available_connections = max_connections
```

## What to read next

- [LEARNING_GUIDE.md](LEARNING_GUIDE.md)
- [STUDENT_GUIDE.md](STUDENT_GUIDE.md)
- [exercises/README.md](exercises/README.md)

## The three exercises

1. Database connection pools
2. Network retries and timeouts
3. Rate limiting

Start with exercise 1. It is the simplest place to begin.

## How to work through each exercise

1. Read the file.
2. Implement one method.
3. Test that method before moving on.
4. If you get stuck, read the hint file and try again.

## Helpful habits

- Change one thing at a time.
- Read the error message.
- Keep notes about what you learned.
- Take breaks when you need them.

## Your goal

By the end of the exercises, you should understand:

- how connection pools work
- why retries need backoff
- how rate limiting protects a service
- how to read and fix common backend errors

## Useful commands

```bash
uvicorn exercises.ex1_db_starter:app --reload --port 8000
curl http://localhost:8000/slow-query
python exercises/test_ex1.py
```

## Final reminder

You do not need to know everything before starting. You only need to take the next small step.
