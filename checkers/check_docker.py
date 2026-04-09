"""
Check if Docker is installed and running
If not, provide installation instructions
"""
import subprocess
import sys
from loguru import logger


def check_docker():
    """Check if Docker is installed and running"""
    try:
        result = subprocess.run(
            ["docker", "--version"],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if result.returncode == 0:
            logger.info(f"✅ Docker installed: {result.stdout.strip()}")
            return True
        else:
            logger.warning("❌ Docker not found")
            return False
            
    except FileNotFoundError:
        logger.warning("❌ Docker not installed")
        return False
    except Exception as e:
        logger.error(f"Error checking Docker: {e}")
        return False


def check_docker_running():
    """Check if Docker daemon is running"""
    try:
        result = subprocess.run(
            ["docker", "info"],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if result.returncode == 0:
            logger.info("✅ Docker daemon is running")
            return True
        else:
            logger.warning("❌ Docker daemon is not running")
            return False
            
    except Exception as e:
        logger.error(f"Error checking Docker daemon: {e}")
        return False


def check_docker_compose():
    """Check if docker-compose is available"""
    try:
        result = subprocess.run(
            ["docker-compose", "--version"],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if result.returncode == 0:
            logger.info(f"✅ docker-compose installed: {result.stdout.strip()}")
            return True
        else:
            logger.warning("❌ docker-compose not found")
            return False
            
    except FileNotFoundError:
        logger.warning("❌ docker-compose not installed")
        return False
    except Exception as e:
        logger.error(f"Error checking docker-compose: {e}")
        return False


def print_installation_guide():
    """Print installation instructions"""
    print("\n" + "="*80)
    print("DOCKER INSTALLATION GUIDE")
    print("="*80)
    print("\n📥 Step 1: Download Docker Desktop")
    print("   https://www.docker.com/products/docker-desktop/")
    print("\n🔧 Step 2: Install Docker Desktop")
    print("   - Run installer (requires Administrator rights)")
    print("   - Follow installation wizard")
    print("   - Restart your computer")
    print("\n▶️  Step 3: Start Docker Desktop")
    print("   - Launch Docker Desktop application")
    print("   - Wait for it to start (whale icon in tray)")
    print("\n✅ Step 4: Verify installation")
    print("   docker --version")
    print("   docker-compose --version")
    print("\n🚀 Step 5: Start Redis and MySQL")
    print("   docker-compose up -d")
    print("\n" + "="*80)


def main():
    """Main check function"""
    logger.info("Checking Docker setup...")
    print()
    
    docker_installed = check_docker()
    docker_running = check_docker_running() if docker_installed else False
    compose_installed = check_docker_compose()
    
    print()
    
    if docker_installed and docker_running and compose_installed:
        logger.success("✅ All Docker components are ready!")
        logger.info("You can now run: docker-compose up -d")
        return True
    else:
        logger.warning("⚠️  Docker is not fully set up")
        print_installation_guide()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
