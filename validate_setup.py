#!/usr/bin/env python3
"""
Quick validation script to check if the environment is ready for running startup scripts.
Run this before using start_all scripts to catch common issues early.
"""

import sys
import os
from pathlib import Path

def print_header(text):
    print("\n" + "="*60)
    print(f"  {text}")
    print("="*60 + "\n")

def print_check(passed, message, details=""):
    status = "✓ PASS" if passed else "✗ FAIL"
    color_code = "\033[92m" if passed else "\033[91m"  # Green or Red
    reset = "\033[0m"
    
    print(f"{color_code}[{status}]{reset} {message}")
    if details and not passed:
        print(f"       → {details}")
    return passed

def main():
    print_header("B2B Contact Miner - Environment Validation")
    
    project_root = Path(__file__).parent
    all_passed = True
    
    # Check 1: Python version
    print("Checking Python installation...")
    python_version = sys.version_info
    passed = python_version.major >= 3 and python_version.minor >= 8
    all_passed &= print_check(
        passed,
        f"Python {python_version.major}.{python_version.minor}.{python_version.micro}",
        "Python 3.8+ is required"
    )
    
    # Check 2: .env file
    print("\nChecking configuration...")
    env_file = project_root / ".env"
    env_example = project_root / ".env.example"
    
    if env_file.exists():
        all_passed &= print_check(True, ".env file exists")
        
        # Check if it's just a copy of example
        with open(env_file, 'r') as f:
            content = f.read()
            if 'your_' in content.lower() or 'change_me' in content.lower():
                all_passed &= print_check(
                    False,
                    ".env file needs configuration",
                    "Update placeholder values with your actual credentials"
                )
            else:
                all_passed &= print_check(True, ".env file appears configured")
    else:
        all_passed &= print_check(
            False,
            ".env file missing",
            f"Run: copy .env.example .env (Windows) or cp .env.example .env (Linux/Mac)"
        )
    
    # Check 3: Required dependencies
    print("\nChecking dependencies...")
    required_packages = [
        ('flask', 'Flask web server'),
        ('fastapi', 'FastAPI monitoring'),
        ('uvicorn', 'ASGI server'),
        ('sqlalchemy', 'Database ORM'),
        ('redis', 'Redis client'),
        ('loguru', 'Logging'),
        ('schedule', 'Task scheduler'),
    ]
    
    for package, description in required_packages:
        try:
            __import__(package.replace('-', '_'))
            all_passed &= print_check(True, f"{description} ({package})")
        except ImportError:
            all_passed &= print_check(
                False,
                f"{description} ({package})",
                f"Run: pip install {package}"
            )
    
    # Check 4: Database connectivity
    print("\nChecking database...")
    try:
        from dotenv import load_dotenv
        load_dotenv(env_file if env_file.exists() else None)
        
        database_url = os.getenv('DATABASE_URL', '')
        if not database_url:
            all_passed &= print_check(
                False,
                "DATABASE_URL not set",
                "Add DATABASE_URL to your .env file"
            )
        else:
            # Try to import MySQL driver
            try:
                import pymysql
                all_passed &= print_check(True, "MySQL driver (pymysql) installed")
                
                # Test connection (optional, can be slow)
                from sqlalchemy import create_engine, text
                engine = create_engine(database_url)
                with engine.connect() as conn:
                    conn.execute(text("SELECT 1"))
                all_passed &= print_check(True, "Database connection successful")
            except Exception as e:
                all_passed &= print_check(
                    False,
                    "Database connection failed",
                    str(e)
                )
    except Exception as e:
        all_passed &= print_check(False, "Database check error", str(e))
    
    # Check 5: Redis (optional)
    print("\nChecking Redis (optional)...")
    try:
        import redis
        redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
        r = redis.from_url(redis_url, socket_timeout=2)
        r.ping()
        all_passed &= print_check(True, "Redis connection successful")
    except Exception as e:
        print_check(
            False,
            "Redis not available (optional)",
            "System will use in-memory deduplication instead"
        )
    
    # Check 6: Directory structure
    print("\nChecking directory structure...")
    required_dirs = ['logs', 'pids', 'templates', 'models', 'services']
    for dir_name in required_dirs:
        dir_path = project_root / dir_name
        all_passed &= print_check(
            dir_path.exists() and dir_path.is_dir(),
            f"Directory '{dir_name}' exists"
        )
    
    # Check 7: Required files
    print("\nChecking required files...")
    required_files = [
        'main.py',
        'web_server.py',
        'scheduler.py',
        'monitoring/healthcheck.py',
        'requirements.txt',
    ]
    
    for file_name in required_files:
        file_path = project_root / file_name
        all_passed &= print_check(
            file_path.exists(),
            f"File '{file_name}' exists"
        )
    
    # Check 8: Port availability
    print("\nChecking port availability...")
    import socket
    
    ports_to_check = [
        (5000, "Flask Web Server"),
        (8000, "FastAPI Monitoring"),
    ]
    
    for port, service in ports_to_check:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = sock.connect_ex(('localhost', port))
        sock.close()
        
        if result == 0:
            print_check(
                False,
                f"Port {port} ({service}) is in use",
                f"Stop existing service or change port in code"
            )
        else:
            all_passed &= print_check(True, f"Port {port} ({service}) is available")
    
    # Final summary
    print_header("Validation Summary")
    
    if all_passed:
        print("\033[92m✓ All checks passed! Your environment is ready.\033[0m")
        print("\nYou can now run:")
        if sys.platform == 'win32':
            print("  Windows:  start_all.bat start")
            print("  PowerShell: .\\start_all.ps1 start")
        else:
            print("  Linux/Mac: ./start_all.sh start")
        print("\nTo run the pipeline manually:")
        print("  python main.py")
        return 0
    else:
        print("\033[91m✗ Some checks failed. Please fix the issues above.\033[0m")
        print("\nCommon fixes:")
        print("  1. Copy .env.example to .env and configure it")
        print("  2. Install dependencies: pip install -r requirements.txt")
        print("  3. Start MySQL/MariaDB database server")
        print("  4. Create database: CREATE DATABASE contact_miner;")
        print("\nAfter fixing, run this validation again.")
        return 1

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\nValidation cancelled.")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nUnexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
