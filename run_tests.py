# Run Tests Script
# Usage: python run_tests.py

import subprocess
import sys

def run_tests():
    """Run all tests with pytest"""
    print("="*60)
    print("Running B2B Contact Miner Tests")
    print("="*60)
    
    # Run pytest with verbose output and coverage
    cmd = [
        sys.executable, "-m", "pytest",
        "tests/",
        "-v",
        "--tb=short",
        "--cov=services",
        "--cov=utils",
        "--cov-report=term-missing"
    ]
    
    try:
        result = subprocess.run(cmd, check=True)
        print("\n✅ All tests passed!")
        return 0
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Tests failed with exit code {e.returncode}")
        return e.returncode
    except FileNotFoundError:
        print("\n❌ pytest not found. Install with: pip install pytest pytest-cov")
        return 1


if __name__ == "__main__":
    exit(run_tests())
