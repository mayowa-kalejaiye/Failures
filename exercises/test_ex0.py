"""Simple tests for Exercise 0 (API Basics).

Run these after starting the app:

```bash
uvicorn exercises.ex0_api_basics_starter:app --reload --port 8000
python exercises/test_ex0.py
```
"""
import requests


BASE = "http://127.0.0.1:8000"


def assert_eq(a, b):
    if a != b:
        raise SystemExit(f"Assertion failed: {a} != {b}")


def run():
    r = requests.get(f"{BASE}/health")
    assert_eq(r.status_code, 200)
    print("health OK ->", r.json())

    # reset store
    r = requests.get(f"{BASE}/debug/reset")
    assert_eq(r.status_code, 200)

    # create user
    r = requests.post(f"{BASE}/users", json={"email": "a@example.com", "name": "Alice"})
    assert_eq(r.status_code, 201)
    print("create OK ->", r.json())

    # duplicate should 409
    r = requests.post(f"{BASE}/users", json={"email": "a@example.com", "name": "Alice"})
    assert_eq(r.status_code, 409)
    print("duplicate check OK")

    # list users
    r = requests.get(f"{BASE}/users")
    assert_eq(r.status_code, 200)
    print("list OK ->", r.json())

    # get user
    r = requests.get(f"{BASE}/users/1")
    assert_eq(r.status_code, 200)
    print("get OK ->", r.json())


if __name__ == "__main__":
    run()
