# 🎓 START HERE - Your Learning Journey

## What Changed?

I transformed this from a "read the code" project into a **"build it yourself"** project! 

### Before ❌
- Complete working code examples
- You just read and run them
- No hands-on practice

### Now ✅  
- **Exercise templates with TODOs**
- **YOU write the implementation**
- **Reference solutions** available when stuck
- **Test scripts** to verify your work

## 🚀 Your First 30 Minutes

### Step 1: Read This (2 minutes)
You're doing it! ✅

### Step 2: Open Exercise 1 (1 minute)
```bash
code c:\Users\kalej\Documents\Failures\exercises\ex1_db_starter.py
```

### Step 3: Read ALL the TODOs (5 minutes)
Don't write code yet - just read and understand what you'll build.

### Step 4: Implement `__init__` (10 minutes)
Start with the simplest part:
```python
class ConnectionPool:
    def __init__(self, max_connections: int = 5):
        self.max_connections = max_connections
        self.available_connections = max_connections
```

### Step 5: Test It (2 minutes)
```bash
# At bottom of file, add temporarily:
if __name__ == "__main__":
    pool = ConnectionPool(5)
    print(f"Created pool with {pool.max_connections} connections")
    print(f"Available: {pool.available_connections}")

# Run it:
python exercises/ex1_db_starter.py
```

### Step 6: Keep Going! (10 minutes)
Implement the next method. Test it. Repeat!

## 📚 Key Documents

| Document | Purpose | When To Read |
|----------|---------|--------------|
| [LEARNING_GUIDE.md](LEARNING_GUIDE.md) | Philosophy & approach | Before starting |
| [STUDENT_GUIDE.md](STUDENT_GUIDE.md) | Quick reference | While coding |
| [exercises/SOLUTIONS.md](exercises/SOLUTIONS.md) | Hints & solutions | When stuck |
| [exercises/README.md](exercises/README.md) | Exercise overview | For navigation |

## 📝 The Three Exercises

### 🎯 Exercise 1: Database Connection Pools (START HERE!)
**File:** `exercises/ex1_db_starter.py`  
**Time:** 2-3 hours  
**Difficulty:** ⭐⭐☆☆☆

What you'll build:
- Connection pool with limited capacity
- Acquire/release connection methods
- Pool exhaustion simulation
- Health monitoring

**Start with:** The `__init__` method

---

### 🎯 Exercise 2: Network Failures & Retries
**File:** `exercises/ex2_network_starter.py`  
**Time:** 2-3 hours  
**Difficulty:** ⭐⭐⭐☆☆

What you'll build:
- Flaky external API simulator
- Retry logic with exponential backoff
- Timeout handling
- Cascading failure demonstration

**Start with:** The `call_external_api()` function

---

### 🎯 Exercise 3: Rate Limiting
**File:** `exercises/ex3_ratelimit_starter.py`  
**Time:** 2-3 hours  
**Difficulty:** ⭐⭐⭐⭐☆

What you'll build:
- Token bucket algorithm
- Token refill mechanism
- Protected API endpoint
- HTTP 429 responses

**Start with:** The `TokenBucket.__init__` method

## ✅ Checklist For Success

Before you start coding:
- [ ] Read [LEARNING_GUIDE.md](LEARNING_GUIDE.md)
- [ ] Have [STUDENT_GUIDE.md](STUDENT_GUIDE.md) open for reference
- [ ] Understand the goal of Exercise 1
- [ ] Know how to run the server
- [ ] Know how to test endpoints

While coding:
- [ ] Implement one method at a time
- [ ] Test after each method
- [ ] Use print statements to debug
- [ ] Don't copy-paste solutions
- [ ] Take breaks when frustrated

After completing each exercise:
- [ ] Run the test script
- [ ] All tests pass
- [ ] Understand WHY it works
- [ ] Can explain code to someone else

## 🎓 Learning Principles

### 1. Struggle = Learning
If it's easy, you're not learning. Embrace the challenge!

### 2. Small Steps
Don't try to write everything at once. One method at a time.

### 3. Test Frequently
Run your code every 5-10 minutes. Catch errors early.

### 4. Read Errors
Error messages tell you exactly what's wrong. Read them carefully!

### 5. Google Everything
Every backend engineer Googles things constantly. It's normal!

## 🆘 When You're Stuck

### After 10 minutes:
- [ ] Read the error message carefully
- [ ] Add print statements to see what's happening
- [ ] Check your logic step by step

### After 20 minutes:
- [ ] Google the specific problem
- [ ] Check the hints in the exercise file
- [ ] Review [STUDENT_GUIDE.md](STUDENT_GUIDE.md) for patterns

### After 30 minutes:
- [ ] Look at [exercises/SOLUTIONS.md](exercises/SOLUTIONS.md) for hints
- [ ] Look at JUST the method you're stuck on
- [ ] Understand it, then try again yourself

### Still stuck?
- [ ] Check the reference implementation in root folder
- [ ] Understand why it works
- [ ] Close the file and rewrite from memory

## 🎯 Your Goal

By the end of these exercises, you should be able to:

✅ Explain how connection pools work  
✅ Implement retry logic from scratch  
✅ Build a rate limiter  
✅ Handle errors gracefully  
✅ Test failure scenarios  
✅ Debug async Python code  

## 🚀 Ready To Start?

1. **Open** [exercises/ex1_db_starter.py](exercises/ex1_db_starter.py)
2. **Read** all the comments and TODOs
3. **Start** with the `ConnectionPool.__init__` method
4. **Code** one small piece at a time
5. **Test** frequently

Good luck! Remember: **You learn by doing, not by reading!** 💪

---

## 📞 Quick Reference Commands

```bash
# Start Exercise 1 server
uvicorn exercises.ex1_db_starter:app --reload --port 8000

# Test your endpoint
curl http://localhost:8000/slow-query

# Run automated tests (after implementing)
python exercises/test_ex1.py

# View in browser
# http://localhost:8000
```

---

**Let's build something! 🚀**
