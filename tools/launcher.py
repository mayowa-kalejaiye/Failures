"""
Simple Launcher for Backend Failure Simulators

Run this script to easily launch any scenario
"""

import sys
import subprocess


SCENARIOS = {
    "1": {
        "name": "Database Failures",
        "file": "db_failures",
        "port": 8000,
        "description": "Connection pools, slow queries, deadlocks"
    },
    "2": {
        "name": "Network Failures",
        "file": "network_failures",
        "port": 8001,
        "description": "Timeouts, retries, cascading failures"
    },
    "3": {
        "name": "Rate Limiting",
        "file": "rate_limiting",
        "port": 8002,
        "description": "Token bucket, fixed window, sliding window"
    },
    "4": {
        "name": "Circuit Breaker",
        "file": "circuit_breaker",
        "port": 8003,
        "description": "Prevent cascading failures, automatic recovery"
    },
    "5": {
        "name": "Resource Failures",
        "file": "resource_failures",
        "port": 8004,
        "description": "Memory leaks, CPU intensive tasks"
    }
}


def show_menu():
    print("\n" + "="*60)
    print("Backend Failure Simulator Launcher".center(60))
    print("="*60)
    print("\nSelect a scenario to run:\n")
    
    for key, scenario in SCENARIOS.items():
        print(f"{key}. {scenario['name']}")
        print(f"   Port {scenario['port']}: {scenario['description']}")
        print()
    
    print("0. Exit")
    print("\n" + "="*60)


def launch_scenario(scenario_key):
    if scenario_key not in SCENARIOS:
        print("Invalid selection!")
        return
    
    scenario = SCENARIOS[scenario_key]
    
    print(f"\nLaunching {scenario['name']}...")
    print(f"URL: http://localhost:{scenario['port']}")
    print(f"Description: {scenario['description']}")
    print("\nPress Ctrl+C to stop the server\n")
    print("="*60 + "\n")
    
    try:
        # Launch uvicorn using python -m to ensure it uses the venv
        subprocess.run([
            sys.executable,
            "-m",
            "uvicorn",
            f"{scenario['file']}:app",
            "--reload",
            "--port", str(scenario['port'])
        ])
    except KeyboardInterrupt:
        print("\n\nServer stopped by user")
    except FileNotFoundError:
        print("\nError: uvicorn not found. Please run: pip install -r requirements.txt")
    except Exception as e:
        print(f"\nError: {str(e)}")


def main():
    while True:
        show_menu()
        
        try:
            choice = input("Enter your choice (0-5): ").strip()
            
            if choice == "0":
                print("\nGoodbye! Happy learning!")
                sys.exit(0)
            
            if choice in SCENARIOS:
                launch_scenario(choice)
            else:
                print("\nInvalid choice. Please select 0-5")
                input("\nPress Enter to continue...")
        
        except KeyboardInterrupt:
            print("\n\nGoodbye!")
            sys.exit(0)
        except Exception as e:
            print(f"\nError: {str(e)}")
            input("\nPress Enter to continue...")


if __name__ == "__main__":
    print("""
    ╔══════════════════════════════════════════════════════════╗
    ║                                                          ║
    ║     Backend Failure Simulation Learning Platform         ║
    ║                                                          ║
    ║  Learn how real-world backend systems fail and how to    ║
    ║  handle failures gracefully in production.               ║
    ║                                                          ║
    ╚══════════════════════════════════════════════════════════╝
    """)
    
    main()
