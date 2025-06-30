#!/usr/bin/env python3
"""
Test runner script for Task Management API
"""

import subprocess
import sys
import os


def run_tests():
    """Run all tests with coverage"""
    print("🧪 Running Task Management API Test Suite")
    print("=" * 50)
    
    # Check if pytest is installed
    try:
        import pytest
    except ImportError:
        print("❌ pytest not found. Installing...")
        subprocess.run([sys.executable, "-m", "pip", "install", "pytest", "pytest-asyncio"])
    
    # Set environment variables for testing
    os.environ["DATABASE_URL"] = "sqlite:///:memory:"
    os.environ["DEBUG"] = "true"
    
    # Run tests
    test_commands = [
        ["python", "-m", "pytest", "tests/", "-v", "--tb=short"],
        ["python", "-m", "pytest", "tests/test_models.py", "-v"],
        ["python", "-m", "pytest", "tests/test_services.py", "-v"],
        ["python", "-m", "pytest", "tests/test_api.py", "-v"]
    ]
    
    for cmd in test_commands:
        print(f"\n🔄 Running: {' '.join(cmd)}")
        result = subprocess.run(cmd)
        if result.returncode != 0:
            print(f"❌ Test failed with return code {result.returncode}")
            return False
    
    print("\n✅ All tests passed!")
    return True


def run_api_tests():
    """Run API integration tests"""
    print("\n🚀 Running API Integration Tests")
    print("-" * 30)
    
    # Run API tests using pytest
    test_commands = [
        ["python", "-m", "pytest", "tests/test_api.py", "-v", "--tb=short"]
    ]
    
    for cmd in test_commands:
        print(f"\n🔄 Running: {' '.join(cmd)}")
        result = subprocess.run(cmd)
        if result.returncode != 0:
            print(f"❌ API test failed with return code {result.returncode}")
            return False
    
    print("\n✅ API integration tests passed!")
    return True


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Run tests for Task Management API")
    parser.add_argument("--api", action="store_true", help="Run API integration tests only")
    parser.add_argument("--unit", action="store_true", help="Run unit tests only")
    
    args = parser.parse_args()
    
    if args.api:
        success = run_api_tests()
    elif args.unit:
        success = run_tests()
    else:
        # Run both unit and API tests
        unit_success = run_tests()
        if unit_success:
            print("\n" + "=" * 50)
            api_success = run_api_tests()
            success = unit_success and api_success
        else:
            success = False
    
    if success:
        print("\n🎉 All tests completed successfully!")
        sys.exit(0)
    else:
        print("\n💥 Some tests failed!")
        sys.exit(1) 