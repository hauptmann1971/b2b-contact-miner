# =============================================================================
# B2B Contact Miner - Full Application Startup Script (PowerShell)
# =============================================================================
# This script starts all necessary components:
# 1. Redis (if using Docker)
# 2. MySQL (if using Docker)
# 3. FastAPI Monitoring Server (port 8000)
# 4. Flask Web Server (port 5000)
# 5. Task Scheduler (daily pipeline runs)
# =============================================================================

$ErrorActionPreference = "Stop"

# Configuration
$ProjectDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$LogDir = Join-Path $ProjectDir "logs"
$PidDir = Join-Path $ProjectDir "pids"

# Create necessary directories
if (-not (Test-Path $LogDir)) { New-Item -ItemType Directory -Path $LogDir | Out-Null }
if (-not (Test-Path $PidDir)) { New-Item -ItemType Directory -Path $PidDir | Out-Null }

Write-Host "========================================" -ForegroundColor Blue
Write-Host "  B2B Contact Miner - Starting All Services" -ForegroundColor Blue
Write-Host "========================================" -ForegroundColor Blue
Write-Host ""

# Function to check if a process is running
function Test-ProcessRunning {
    param($PidFile)
    
    if (Test-Path $PidFile) {
        $processId = Get-Content $PidFile
        try {
            $process = Get-Process -Id $processId -ErrorAction SilentlyContinue
            return ($null -ne $process)
        } catch {
            return $false
        }
    }
    return $false
}

# Function to stop a service
function Stop-Service {
    param($ServiceName)
    
    $pidFile = Join-Path $PidDir "$ServiceName.pid"
    
    if (Test-ProcessRunning $pidFile) {
        $processId = Get-Content $pidFile
        Write-Host "Stopping $ServiceName (PID: $processId)..." -ForegroundColor Yellow
        
        try {
            Stop-Process -Id $processId -Force -ErrorAction SilentlyContinue
            Start-Sleep -Seconds 2
            
            # Force kill if still running
            if (Test-ProcessRunning $pidFile) {
                Write-Host "Force killing $ServiceName..." -ForegroundColor Red
                Stop-Process -Id $processId -Force -ErrorAction SilentlyContinue
            }
            
            Remove-Item $pidFile -ErrorAction SilentlyContinue
            Write-Host "$ServiceName stopped" -ForegroundColor Green
        } catch {
            Write-Host "Error stopping $ServiceName : $_" -ForegroundColor Red
        }
    } else {
        Write-Host "$ServiceName is not running" -ForegroundColor Yellow
    }
}

# Function to start a service
function Start-ServiceCustom {
    param($ServiceName, $Command)
    
    $logFile = Join-Path $LogDir "$ServiceName.log"
    $pidFile = Join-Path $PidDir "$ServiceName.pid"
    
    if (Test-ProcessRunning $pidFile) {
        Write-Host "$ServiceName is already running" -ForegroundColor Yellow
        return
    }
    
    Write-Host "Starting $ServiceName ..." -ForegroundColor Blue
    
    # Start process using Start-Process with proper arguments
    $process = Start-Process -FilePath "py" `
        -ArgumentList $Command.Split(' ') `
        -WorkingDirectory $ProjectDir `
        -PassThru `
        -NoNewWindow `
        -RedirectStandardOutput "$logFile.out" `
        -RedirectStandardError "$logFile.err"
    
    # Combine outputs into single log file after a delay
    Start-Job -ScriptBlock {
        param($logFile, $outFile, $errFile)
        Start-Sleep -Seconds 1
        if (Test-Path $outFile) { Get-Content $outFile | Out-File $logFile }
        if (Test-Path $errFile) { Get-Content $errFile | Out-File $logFile -Append }
    } -ArgumentList $logFile, "$logFile.out", "$logFile.err" | Out-Null
    
    $process.Id | Out-File -FilePath $pidFile -Encoding utf8
    
    Start-Sleep -Seconds 2
    Write-Host "$ServiceName started (PID: $($process.Id), Log: $logFile)" -ForegroundColor Green
}

# Function to check service status
function Test-ServiceStatus {
    param($ServiceName, $Port)
    
    $pidFile = Join-Path $PidDir "$ServiceName.pid"
    
    if (Test-ProcessRunning $pidFile) {
        $processId = Get-Content $pidFile
        if ($Port -ne "N/A") {
            Write-Host "  [OK] $ServiceName (PID: $processId, Port: $Port)" -ForegroundColor Green
        } else {
            Write-Host "  [OK] $ServiceName (PID: $processId)" -ForegroundColor Green
        }
        return $true
    } else {
        Write-Host "  [FAIL] $ServiceName - NOT RUNNING" -ForegroundColor Red
        if (Test-Path $pidFile) { Remove-Item $pidFile -ErrorAction SilentlyContinue }
        return $false
    }
}

# Parse command line arguments
$action = if ($args.Count -gt 0) { $args[0] } else { "start" }

switch ($action.ToLower()) {
    "start" {
        Write-Host "Starting all services..." -ForegroundColor Green
        Write-Host ""
        
        # Step 1: Check Docker services
        Write-Host "[1/6] Checking Docker services..." -ForegroundColor Blue
        if (Get-Command docker-compose -ErrorAction SilentlyContinue) {
            $dockerComposeFile = Join-Path $ProjectDir "doc\docker-compose.yml"
            if (Test-Path $dockerComposeFile) {
                Write-Host "Starting Redis and MySQL with Docker..."
                Push-Location (Join-Path $ProjectDir "doc")
                docker-compose up -d 2>$null
                if ($LASTEXITCODE -ne 0) {
                    Write-Host "Docker services might already be running" -ForegroundColor Yellow
                }
                Pop-Location
                Start-Sleep -Seconds 3
            }
        } else {
            Write-Host "Docker Compose not found, skipping Docker services" -ForegroundColor Yellow
        }
        Write-Host ""
        
        # Step 2: Start FastAPI Monitoring Server
        Write-Host "[2/6] Starting FastAPI Monitoring Server (port 8000)..." -ForegroundColor Blue
        Start-ServiceCustom "monitoring" "monitoring/healthcheck.py"
        Start-Sleep -Seconds 2
        Write-Host ""
        
        # Step 3: Start Flask Web Server
        Write-Host "[3/6] Starting Flask Web Server (port 5000)..." -ForegroundColor Blue
        Start-ServiceCustom "web_server" "web_server.py"
        Start-Sleep -Seconds 2
        Write-Host ""
        
        # Step 4: Start Task Scheduler
        Write-Host "[4/6] Starting Task Scheduler..." -ForegroundColor Blue
        Start-ServiceCustom "scheduler" "scheduler.py"
        Start-Sleep -Seconds 1
        Write-Host ""
        
        # Step 5: Main Pipeline info
        Write-Host "[5/6] Main Pipeline ready (run 'py main.py' manually or wait for scheduler)" -ForegroundColor Blue
        Write-Host ""
        
        # Step 6: Status check
        Write-Host "[6/6] Checking service status..." -ForegroundColor Blue
        Write-Host ""
        
        Test-ServiceStatus "monitoring" "8000"
        Test-ServiceStatus "web_server" "5000"
        Test-ServiceStatus "scheduler" "N/A"
        
        Write-Host ""
        Write-Host "========================================" -ForegroundColor Green
        Write-Host "  All services started successfully!" -ForegroundColor Green
        Write-Host "========================================" -ForegroundColor Green
        Write-Host ""
        Write-Host "Access points:" -ForegroundColor Blue
        Write-Host "  • Flask Web UI:      http://localhost:5000"
        Write-Host "  • FastAPI Health:    http://localhost:8000/health"
        Write-Host "  • FastAPI Docs:      http://localhost:8000/docs"
        Write-Host ""
        Write-Host "Logs directory: $LogDir" -ForegroundColor Blue
        Write-Host "PIDs directory: $PidDir" -ForegroundColor Blue
        Write-Host ""
        Write-Host "To stop all services, run: .\start_all.ps1 stop" -ForegroundColor Yellow
    }
    
    "stop" {
        Write-Host "Stopping all services..." -ForegroundColor Yellow
        Write-Host ""
        
        Stop-Service "scheduler"
        Stop-Service "web_server"
        Stop-Service "monitoring"
        
        Write-Host ""
        $stopDocker = Read-Host "Stop Docker containers (y/n)?"
        if ($stopDocker -eq "y" -or $stopDocker -eq "Y") {
            $dockerComposeFile = Join-Path $ProjectDir "doc\docker-compose.yml"
            if (Test-Path $dockerComposeFile) {
                Push-Location (Join-Path $ProjectDir "doc")
                docker-compose down 2>$null
                Pop-Location
                Write-Host "Docker services stopped" -ForegroundColor Green
            }
        }
        
        Write-Host ""
        Write-Host "All services stopped" -ForegroundColor Green
    }
    
    "restart" {
        Write-Host "Restarting all services..." -ForegroundColor Yellow
        Write-Host ""
        & $MyInvocation.MyCommand.Path stop
        Start-Sleep -Seconds 2
        Write-Host ""
        & $MyInvocation.MyCommand.Path start
    }
    
    "status" {
        Write-Host "Service Status:" -ForegroundColor Blue
        Write-Host ""
        
        Test-ServiceStatus "monitoring" "8000"
        Test-ServiceStatus "web_server" "5000"
        Test-ServiceStatus "scheduler" "N/A"
        
        Write-Host ""
        
        # Check Docker
        if (Get-Command docker-compose -ErrorAction SilentlyContinue) {
            Write-Host "Docker Services:" -ForegroundColor Blue
            Push-Location (Join-Path $ProjectDir "doc")
            docker-compose ps 2>$null
            if ($LASTEXITCODE -ne 0) {
                Write-Host "  Docker services not running" -ForegroundColor Yellow
            }
            Pop-Location
        }
        
        Write-Host ""
        Write-Host "Recent Logs:" -ForegroundColor Blue
        Write-Host ""
        
        Get-ChildItem (Join-Path $LogDir "*.log") -ErrorAction SilentlyContinue | ForEach-Object {
            $serviceName = $_.BaseName
            Write-Host "$serviceName :" -ForegroundColor Blue
            Get-Content $_.FullName -Tail 3 | ForEach-Object { Write-Host "  $_" }
            Write-Host ""
        }
    }
    
    "logs" {
        $service = if ($args.Count -gt 1) { $args[1] } else { "all" }
        
        if ($service -eq "all") {
            Write-Host "Tailing all logs (Ctrl+C to exit)..." -ForegroundColor Blue
            Write-Host ""
            Get-ChildItem (Join-Path $LogDir "*.log") | ForEach-Object {
                Write-Host "=== $($_.Name) ===" -ForegroundColor Cyan
            }
            Get-Content (Join-Path $LogDir "*.log") -Wait -Tail 10
        } else {
            $logFile = Join-Path $LogDir "$service.log"
            if (Test-Path $logFile) {
                Write-Host "Tailing $service logs (Ctrl+C to exit)..." -ForegroundColor Blue
                Write-Host ""
                Get-Content $logFile -Wait -Tail 10
            } else {
                Write-Host "Log file not found: $logFile" -ForegroundColor Red
                exit 1
            }
        }
    }
    
    "clean" {
        Write-Host "Cleaning up PID files and old logs..." -ForegroundColor Yellow
        Remove-Item (Join-Path $PidDir "*.pid") -ErrorAction SilentlyContinue
        Get-ChildItem (Join-Path $LogDir "*.log") | Where-Object { 
            $_.LastWriteTime -lt (Get-Date).AddDays(-7) 
        } | Remove-Item -Force -ErrorAction SilentlyContinue
        Write-Host "Cleanup complete" -ForegroundColor Green
    }
    
    default {
        Write-Host "Usage: .\start_all.ps1 {start|stop|restart|status|logs [service]|clean}" -ForegroundColor Red
        Write-Host ""
        Write-Host "Commands:"
        Write-Host "  start   - Start all services"
        Write-Host "  stop    - Stop all services"
        Write-Host "  restart - Restart all services"
        Write-Host "  status  - Show service status"
        Write-Host "  logs    - Tail all logs (or specify service name)"
        Write-Host "  clean   - Remove PID files and old logs"
        exit 1
    }
}

exit 0
