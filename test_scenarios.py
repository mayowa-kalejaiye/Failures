"""
Testing Script - Run different failure scenarios

This script helps you test various endpoints and see failure scenarios in action.
"""

import requests
import time
from typing import Dict, Any


class FailureSimulatorTester:
    """Helper class to test failure scenarios"""
    
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.session = requests.Session()
    
    def test_endpoint(self, endpoint: str, description: str):
        """Test a single endpoint"""
        print(f"\n{'='*60}")
        print(f"Testing: {description}")
        print(f"Endpoint: {endpoint}")
        print(f"{'='*60}")
        
        try:
            response = self.session.get(f"{self.base_url}{endpoint}")
            print(f"Status: {response.status_code}")
            print(f"Response: {response.json()}")
            return response
        except Exception as e:
            print(f"Error: {str(e)}")
            return None
    
    def rapid_fire(self, endpoint: str, count: int, description: str):
        """Make multiple rapid requests to trigger rate limiting or pool exhaustion"""
        print(f"\n{'='*60}")
        print(f"Rapid Fire Test: {description}")
        print(f"Making {count} rapid requests to {endpoint}")
        print(f"{'='*60}")
        
        success = 0
        failed = 0
        rate_limited = 0
        
        for i in range(count):
            try:
                response = self.session.get(f"{self.base_url}{endpoint}")
                if response.status_code == 200:
                    success += 1
                    print(f"Request {i+1}: ✓ Success")
                elif response.status_code == 429:
                    rate_limited += 1
                    print(f"Request {i+1}: ⚠ Rate Limited")
                else:
                    failed += 1
                    print(f"Request {i+1}: ✗ Failed ({response.status_code})")
            except Exception as e:
                failed += 1
                print(f"Request {i+1}: ✗ Error - {str(e)}")
            
            time.sleep(0.1)  # Small delay between requests
        
        print(f"\nResults: {success} success, {failed} failed, {rate_limited} rate limited")


def test_database_failures():
    """Test database failure scenarios"""
    tester = FailureSimulatorTester("http://localhost:8000")
    
    print("\n" + "="*60)
    print("DATABASE FAILURE SCENARIOS")
    print("="*60)
    
    # Test slow query
    tester.test_endpoint("/query/slow", "Slow Query")
    
    # Test connection pool exhaustion
    print("\n\nTesting Connection Pool Exhaustion...")
    print("(Making 5 simultaneous requests to exhaust pool)")
    tester.rapid_fire("/query/pool-test", 5, "Pool Exhaustion")
    
    # Check stats
    time.sleep(3)
    tester.test_endpoint("/stats", "Connection Pool Stats")


def test_network_failures():
    """Test network failure scenarios"""
    tester = FailureSimulatorTester("http://localhost:8001")
    
    print("\n" + "="*60)
    print("NETWORK FAILURE SCENARIOS")
    print("="*60)
    
    # Test slow endpoint
    tester.test_endpoint("/api/slow?delay=2", "Slow Endpoint (2s)")
    
    # Test timeout
    tester.test_endpoint("/api/timeout?timeout=1", "Timeout (1s limit)")
    
    # Test intermittent failures
    print("\n\nTesting Intermittent Failures (multiple attempts)...")
    for i in range(5):
        tester.test_endpoint("/api/intermittent", f"Intermittent Attempt {i+1}")
        time.sleep(0.5)
    
    # Test retry logic
    tester.test_endpoint("/api/retry", "With Retry Logic")


def test_rate_limiting():
    """Test rate limiting scenarios"""
    tester = FailureSimulatorTester("http://localhost:8002")
    
    print("\n" + "="*60)
    print("RATE LIMITING SCENARIOS")
    print("="*60)
    
    # Test token bucket
    tester.rapid_fire("/api/token-bucket", 15, "Token Bucket (limit: 10/min)")
    
    time.sleep(2)
    
    # Test fixed window
    tester.rapid_fire("/api/fixed-window", 15, "Fixed Window (limit: 10/min)")
    
    # Check status
    time.sleep(1)
    tester.test_endpoint("/rate-limit/status", "Rate Limit Status")


def test_circuit_breaker():
    """Test circuit breaker pattern"""
    tester = FailureSimulatorTester("http://localhost:8003")
    
    print("\n" + "="*60)
    print("CIRCUIT BREAKER SCENARIOS")
    print("="*60)
    
    # Test unreliable service repeatedly
    print("\n\nTriggering Circuit Breaker (unreliable service)...")
    for i in range(10):
        response = tester.test_endpoint("/api/unreliable", f"Attempt {i+1}")
        time.sleep(0.5)
    
    # Check status
    tester.test_endpoint("/circuit-breaker/status", "All Circuit Breaker Status")


def main():
    """Main test runner"""
    print("""
    ╔══════════════════════════════════════════════════════════╗
    ║     Backend Failure Simulation Test Suite              ║
    ╚══════════════════════════════════════════════════════════╝
    
    This will test various failure scenarios.
    Make sure the following services are running:
    
    - Database Failures: http://localhost:8000
    - Network Failures: http://localhost:8001
    - Rate Limiting: http://localhost:8002
    - Circuit Breaker: http://localhost:8003
    
    Press Ctrl+C to stop at any time.
    """)
    
    input("Press Enter to start tests...")
    
    try:
        # Choose which tests to run
        print("\nSelect test to run:")
        print("1. Database Failures")
        print("2. Network Failures")
        print("3. Rate Limiting")
        print("4. Circuit Breaker")
        print("5. All Tests")
        
        choice = input("\nEnter choice (1-5): ").strip()
        
        if choice == "1":
            test_database_failures()
        elif choice == "2":
            test_network_failures()
        elif choice == "3":
            test_rate_limiting()
        elif choice == "4":
            test_circuit_breaker()
        elif choice == "5":
            test_database_failures()
            test_network_failures()
            test_rate_limiting()
            test_circuit_breaker()
        else:
            print("Invalid choice")
    
    except KeyboardInterrupt:
        print("\n\nTests interrupted by user")
    except Exception as e:
        print(f"\n\nError during testing: {str(e)}")


if __name__ == "__main__":
    main()
