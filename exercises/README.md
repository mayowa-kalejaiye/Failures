# Hands-On Exercises

This is where **YOU** write the code!

## Available Exercises

### Exercise 0: API Basics (new)

**File:** [ex0_api_basics_starter.py](ex0_api_basics_starter.py)  
**Port:** 8000  
**Time:** 30-90 minutes

Learn how to design and run a small API: endpoints, request/response models, validation, and basic error handling. Start here if you are new to APIs.

```bash
uvicorn exercises.ex0_api_basics_starter:app --reload --port 8000
```

Complete the TODOs in `ex0_api_basics_starter.py` and run `exercises/test_ex0.py` to check your work.

### Exercise 1: Database Connection Pools

**File:** [ex1_db_starter.py](ex1_db_starter.py)  
**Port:** 8000  
**Time:** 2-3 hours

Build a connection pool from scratch and watch it break under load.

```bash
uvicorn exercises.ex1_db_starter:app --reload --port 8000
```

---

### Exercise 2: Network Failures & Retries

**File:** [ex2_network_starter.py](ex2_network_starter.py)  
**Port:** 8001  
**Time:** 2-3 hours

Implement retry logic with exponential backoff and see cascading failures.

```bash
uvicorn exercises.ex2_network_starter:app --reload --port 8001
```

---

### Exercise 3: Rate Limiting

**File:** [ex3_ratelimit_starter.py](ex3_ratelimit_starter.py)  
**Port:** 8002  
**Time:** 2-3 hours

Build a token bucket algorithm to protect your API.

```bash
uvicorn exercises.ex3_ratelimit_starter:app --reload --port 8002
```

---

## How To Start

1. **Pick Exercise 1** - Always start with database patterns
2. If you are new to APIs, start with **Exercise 0** and follow `docs/FOUNDATIONS.md` first.
3. **Open the file** - Read all the TODOs
4. **Start coding** - Implement one method at a time
5. **Test frequently** - Run the server after each change
6. **Debug actively** - Print statements are your friend

## Resources

- [LEARNING_GUIDE.md](../docs/LEARNING_GUIDE.md) - Full learning philosophy
- [STUDENT_GUIDE.md](../docs/STUDENT_GUIDE.md) - Quick reference & patterns
- [SOLUTIONS.md](SOLUTIONS.md) - Hints and where to find solutions

## Remember

**You learn by DOING, not by reading!**

Good luck!
