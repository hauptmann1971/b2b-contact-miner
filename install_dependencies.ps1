# Установка всех необходимых зависимостей для B2B Contact Miner

Write-Host "Installing all required dependencies..." -ForegroundColor Green
Write-Host ""

$packages = @(
    "redis",
    "loguru",
    "fastapi",
    "uvicorn",
    "schedule",
    "flask",
    "sqlalchemy",
    "pymysql",
    "cryptography",
    "pydantic-settings"
)

foreach ($package in $packages) {
    Write-Host "Installing $package..." -ForegroundColor Yellow
    py -m pip install $package --quiet
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  ✓ $package installed" -ForegroundColor Green
    } else {
        Write-Host "  ✗ Failed to install $package" -ForegroundColor Red
    }
}

Write-Host ""
Write-Host "All dependencies installed!" -ForegroundColor Green
Write-Host ""
Write-Host "Now you can run: .\start_all.ps1 start" -ForegroundColor Cyan
