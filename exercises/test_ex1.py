"""
Test Script for Exercise 1: Database Connection Pool

Run this to verify your implementation works correctly!

Usage:
    python exercises/test_ex1.py

Make sure your server is running first:
    uvicorn exercises.ex1_db_starter:app --reload --port 8000
"""

import requests
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

BASE_URL = "http://localhost:8000"

def test_health():
    """Test 1: Health endpoint should return pool stats"""
    print("\nTest 1: Health Check")
    try:
        r = requests.get(f"{BASE_URL}/health")
        if r.status_code == 200:
            data = r.json()
            print(f"   Health endpoint works!")
            print(f"   Pool stats: {data}")
            return True
        else:
            print(f"   Health endpoint returned {r.status_code}")
            return False
    except Exception as e:
        print(f"   Error: {e}")
        print(f"   Is your server running? Check implementation of /health")
        return False


def test_slow_query():
    """Test 2: Slow query should work"""
    print("\nTest 2: Single Slow Query")
    try:
        start = time.time()
        r = requests.get(f"{BASE_URL}/slow-query")
        elapsed = time.time() - start
        
        if r.status_code == 200:
            print(f"   Slow query completed in {elapsed:.2f}s")
            return True
        else:
            print(f"   Query failed with status {r.status_code}")
            return False
    except Exception as e:
        print(f"   Error: {e}")
        return False


def test_concurrent_queries(num_queries=6):
    """Test 3: Pool exhaustion with concurrent queries"""
    print(f"\nTest 3: {num_queries} Concurrent Queries (Pool Size: 5)")
    print("   Expected: 5 should succeed, 1 should fail with 503")
    
    def make_request(i):
        try:
            r = requests.get(f"{BASE_URL}/slow-query", timeout=10)
            return (i, r.status_code, "success")
        except Exception as e:
            return (i, None, str(e))
    
    with ThreadPoolExecutor(max_workers=num_queries) as executor:
        futures = [executor.submit(make_request, i) for i in range(1, num_queries + 1)]
        
        successes = 0
        failures = 0
        
        for future in as_completed(futures):
            i, status, result = future.result()
            if status == 200:
                print(f"   Request {i}: Success")
                successes += 1
            elif status == 503:
                print(f"   Request {i}: Pool exhausted (expected!)")
                failures += 1
            else:
                print(f"   Request {i}: Unexpected - {status} {result}")
        
        print(f"\n   Results: {successes} succeeded, {failures} failed")
        
        if successes == 5 and failures == 1:
            print("   Perfect! Your pool is working correctly!")
            return True
        elif successes > 0:
            print("   Partial success - check your acquire/release logic")
            return False
        else:
            print("   No requests succeeded - check your implementation")
            return False


def test_pool_recovery():
    """Test 4: Pool should recover after queries complete"""
    print("\nTest 4: Pool Recovery")
    print("   Waiting for pool to recover...")
    time.sleep(6)  # Wait for slow queries to complete
    
    try:
        r = requests.get(f"{BASE_URL}/health")
        data = r.json()
        
        # Check if we have full capacity again
        if "available_connections" in data:
            if data["available_connections"] == data.get("total_connections", 5):
                print(f"   Pool recovered! {data['available_connections']}/{data['total_connections']} available")
                return True
            else:
                print(f"   Pool not fully recovered: {data}")
                print("   Check if you're releasing connections properly")
                return False
        else:
            print(f"   Health endpoint doesn't return connection info")
            return False
    except Exception as e:
        print(f"   Error: {e}")
        return False


def main():
    print("="*60)
    print("  Database Connection Pool - Exercise 1 Tests")
    print("="*60)
    
    # Check if server is running
    try:
        requests.get(BASE_URL, timeout=2)
    except:
        print("\nServer not responding!")
        print("\nStart your server first:")
        print("   uvicorn exercises.ex1_db_starter:app --reload --port 8000")
        return
    
    results = []
    
    # Run all tests
    results.append(("Health Check", test_health()))
    results.append(("Slow Query", test_slow_query()))
    results.append(("Pool Exhaustion", test_concurrent_queries()))
    results.append(("Pool Recovery", test_pool_recovery()))
    
    # Summary
    print("\n" + "="*60)
    print("  Test Summary")
    print("="*60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "PASS" if result else "FAIL"
        print(f"  {status}: {test_name}")
    
    print(f"\n  Score: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n  Excellent! All tests passed!")
        print("  Ready to move to Exercise 2!")
    elif passed >= total * 0.5:
        print("\n  Good progress! Fix remaining issues.")
        print("  Check SOLUTIONS.md if you're stuck")
    else:
        print("\n  Keep working! You're learning!")
        print("  Review the exercise file and try again")
    
    print("="*60)


if __name__ == "__main__":
    main()
