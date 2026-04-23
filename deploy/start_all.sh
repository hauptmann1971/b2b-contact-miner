#!/bin/bash

# =============================================================================
# B2B Contact Miner - Full Application Startup Script
# =============================================================================
# This script starts all necessary components:
# 1. Redis (if using Docker)
# 2. MySQL (if using Docker)
# 3. FastAPI Monitoring Server (port 8000)
# 4. Flask Web Server (port 5000)
# 5. Task Scheduler (daily pipeline runs)
# 6. Background Workers (async task processing)
# =============================================================================

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_DIR="$PROJECT_DIR/logs"
PID_DIR="$PROJECT_DIR/pids"

# Create necessary directories
mkdir -p "$LOG_DIR"
mkdir -p "$PID_DIR"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  B2B Contact Miner - Starting All Services${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Function to check if a process is running
is_running() {
    local pid_file=$1
    if [ -f "$pid_file" ]; then
        local pid=$(cat "$pid_file")
        if ps -p $pid > /dev/null 2>&1; then
            return 0
        fi
    fi
    return 1
}

# Function to stop a service
stop_service() {
    local service_name=$1
    local pid_file="$PID_DIR/${service_name}.pid"
    
    if is_running "$pid_file"; then
        local pid=$(cat "$pid_file")
        echo -e "${YELLOW}Stopping $service_name (PID: $pid)...${NC}"
        kill $pid 2>/dev/null || true
        sleep 2
        
        # Force kill if still running
        if is_running "$pid_file"; then
            echo -e "${RED}Force killing $service_name...${NC}"
            kill -9 $pid 2>/dev/null || true
        fi
        
        rm -f "$pid_file"
        echo -e "${GREEN}$service_name stopped${NC}"
    else
        echo -e "${YELLOW}$service_name is not running${NC}"
    fi
}

# Function to start a service in background
start_service() {
    local service_name=$1
    local command=$2
    local log_file="$LOG_DIR/${service_name}.log"
    local pid_file="$PID_DIR/${service_name}.pid"
    
    if is_running "$pid_file"; then
        echo -e "${YELLOW}$service_name is already running${NC}"
        return
    fi
    
    echo -e "${BLUE}Starting $service_name...${NC}"
    nohup $command > "$log_file" 2>&1 &
    local pid=$!
    echo $pid > "$pid_file"
    echo -e "${GREEN}$service_name started (PID: $pid, Log: $log_file)${NC}"
}

# Parse command line arguments
ACTION=${1:-"start"}

case $ACTION in
    start)
        echo -e "${GREEN}Starting all services...${NC}"
        echo ""
        
        # Step 1: Start Docker services (optional)
        echo -e "${BLUE}[1/6] Checking Docker services...${NC}"
        if command -v docker-compose &> /dev/null; then
            if [ -f "$PROJECT_DIR/doc/docker-compose.yml" ]; then
                echo "Starting Redis and MySQL with Docker..."
                cd "$PROJECT_DIR/doc"
                docker-compose up -d 2>/dev/null || echo -e "${YELLOW}Docker services might already be running${NC}"
                cd "$PROJECT_DIR"
                sleep 3
            fi
        else
            echo -e "${YELLOW}Docker Compose not found, skipping Docker services${NC}"
        fi
        echo ""
        
        # Step 2: Start FastAPI Monitoring Server
        echo -e "${BLUE}[2/6] Starting FastAPI Monitoring Server (port 8000)...${NC}"
        start_service "monitoring" "python monitoring/healthcheck.py"
        sleep 2
        echo ""
        
        # Step 3: Start Flask Web Server
        echo -e "${BLUE}[3/6] Starting Flask Web Server (port 5000)...${NC}"
        start_service "web_server" "python web_server.py"
        sleep 2
        echo ""
        
        # Step 4: Start Task Scheduler
        echo -e "${BLUE}[4/6] Starting Task Scheduler...${NC}"
        start_service "scheduler" "python scheduler.py"
        sleep 1
        echo ""
        
        # Step 5: Start Main Pipeline (if needed)
        echo -e "${BLUE}[5/6] Main Pipeline ready (run 'python main.py' manually or wait for scheduler)${NC}"
        echo ""
        
        # Step 6: Status check
        echo -e "${BLUE}[6/6] Checking service status...${NC}"
        echo ""
        
        # Check each service
        services=("monitoring:8000" "web_server:5000" "scheduler:N/A")
        for service_info in "${services[@]}"; do
            IFS=':' read -r service port <<< "$service_info"
            pid_file="$PID_DIR/${service}.pid"
            
            if is_running "$pid_file"; then
                pid=$(cat "$pid_file")
                if [ "$port" != "N/A" ]; then
                    echo -e "  ${GREEN}✓${NC} $service (PID: $pid, Port: $port)"
                else
                    echo -e "  ${GREEN}✓${NC} $service (PID: $pid)"
                fi
            else
                echo -e "  ${RED}✗${NC} $service - NOT RUNNING"
            fi
        done
        
        echo ""
        echo -e "${GREEN}========================================${NC}"
        echo -e "${GREEN}  All services started successfully!${NC}"
        echo -e "${GREEN}========================================${NC}"
        echo ""
        echo -e "${BLUE}Access points:${NC}"
        echo -e "  • Flask Web UI:      http://localhost:5000"
        echo -e "  • FastAPI Health:    http://localhost:8000/health"
        echo -e "  • FastAPI Docs:      http://localhost:8000/docs"
        echo ""
        echo -e "${BLUE}Logs directory: $LOG_DIR${NC}"
        echo -e "${BLUE}PIDs directory: $PID_DIR${NC}"
        echo ""
        echo -e "${YELLOW}To stop all services, run: ./start_all.sh stop${NC}"
        ;;
        
    stop)
        echo -e "${YELLOW}Stopping all services...${NC}"
        echo ""
        
        stop_service "scheduler"
        stop_service "web_server"
        stop_service "monitoring"
        
        echo ""
        echo -e "${YELLOW}Optional: Stop Docker services?${NC}"
        read -p "Stop Docker containers (y/n)? " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            if [ -f "$PROJECT_DIR/doc/docker-compose.yml" ]; then
                cd "$PROJECT_DIR/doc"
                docker-compose down 2>/dev/null || true
                cd "$PROJECT_DIR"
                echo -e "${GREEN}Docker services stopped${NC}"
            fi
        fi
        
        echo ""
        echo -e "${GREEN}All services stopped${NC}"
        ;;
        
    restart)
        echo -e "${YELLOW}Restarting all services...${NC}"
        echo ""
        $0 stop
        sleep 2
        echo ""
        $0 start
        ;;
        
    status)
        echo -e "${BLUE}Service Status:${NC}"
        echo ""
        
        services=("monitoring:8000" "web_server:5000" "scheduler:N/A")
        for service_info in "${services[@]}"; do
            IFS=':' read -r service port <<< "$service_info"
            pid_file="$PID_DIR/${service}.pid"
            
            if is_running "$pid_file"; then
                pid=$(cat "$pid_file")
                if [ "$port" != "N/A" ]; then
                    echo -e "  ${GREEN}✓${NC} $service (PID: $pid, Port: $port)"
                else
                    echo -e "  ${GREEN}✓${NC} $service (PID: $pid)"
                fi
            else
                echo -e "  ${RED}✗${NC} $service - NOT RUNNING"
            fi
        done
        
        echo ""
        
        # Check Docker
        if command -v docker-compose &> /dev/null; then
            echo -e "${BLUE}Docker Services:${NC}"
            cd "$PROJECT_DIR/doc"
            docker-compose ps 2>/dev/null || echo -e "  ${YELLOW}Docker services not running${NC}"
            cd "$PROJECT_DIR"
        fi
        
        echo ""
        echo -e "${BLUE}Recent Logs:${NC}"
        echo ""
        for log_file in "$LOG_DIR"/*.log; do
            if [ -f "$log_file" ]; then
                service_name=$(basename "$log_file" .log)
                echo -e "${BLUE}$service_name:${NC}"
                tail -n 3 "$log_file" 2>/dev/null | sed 's/^/  /'
                echo ""
            fi
        done
        ;;
        
    logs)
        SERVICE=${2:-"all"}
        
        if [ "$SERVICE" = "all" ]; then
            echo -e "${BLUE}Tailing all logs (Ctrl+C to exit)...${NC}"
            echo ""
            tail -f "$LOG_DIR"/*.log
        else
            log_file="$LOG_DIR/${SERVICE}.log"
            if [ -f "$log_file" ]; then
                echo -e "${BLUE}Tailing $SERVICE logs (Ctrl+C to exit)...${NC}"
                echo ""
                tail -f "$log_file"
            else
                echo -e "${RED}Log file not found: $log_file${NC}"
                exit 1
            fi
        fi
        ;;
        
    clean)
        echo -e "${YELLOW}Cleaning up PID files and old logs...${NC}"
        rm -f "$PID_DIR"/*.pid
        find "$LOG_DIR" -name "*.log" -mtime +7 -delete 2>/dev/null || true
        echo -e "${GREEN}Cleanup complete${NC}"
        ;;
        
    *)
        echo -e "${RED}Usage: $0 {start|stop|restart|status|logs [service]|clean}${NC}"
        echo ""
        echo "Commands:"
        echo "  start   - Start all services"
        echo "  stop    - Stop all services"
        echo "  restart - Restart all services"
        echo "  status  - Show service status"
        echo "  logs    - Tail all logs (or specify service name)"
        echo "  clean   - Remove PID files and old logs"
        exit 1
        ;;
esac

exit 0
