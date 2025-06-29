#!/usr/bin/env python3
"""
Development scripts for TLDW Discord bot.
"""
import subprocess
import sys
import os

def run_tests():
    """Run tests with unittest."""
    return subprocess.run([sys.executable, "-m", "unittest", "tests.py", "-v"])

def run_pytest():
    """Run tests with pytest."""
    return subprocess.run([sys.executable, "-m", "pytest", "-v"])

def run_tests_with_coverage():
    """Run tests with pytest and coverage."""
    return subprocess.run([sys.executable, "-m", "pytest", "--cov=tldw", "tests.py"])

def start_bot():
    """Start the Discord bot."""
    return subprocess.run([sys.executable, "main.py"])

def main():
    """Main entry point for scripts."""
    if len(sys.argv) < 2:
        print("Usage: python scripts.py <command>")
        print("Commands:")
        print("  test       - Run tests with unittest")
        print("  pytest     - Run tests with pytest")  
        print("  test-cov   - Run tests with coverage")
        print("  start      - Start the Discord bot")
        return 1
    
    command = sys.argv[1]
    
    if command == "test":
        return run_tests().returncode
    elif command == "pytest":
        return run_pytest().returncode
    elif command == "test-cov":
        return run_tests_with_coverage().returncode
    elif command == "start":
        return start_bot().returncode
    else:
        print(f"Unknown command: {command}")
        return 1

if __name__ == "__main__":
    sys.exit(main())