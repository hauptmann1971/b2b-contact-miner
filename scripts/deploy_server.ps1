param(
    [Parameter(Mandatory = $true)]
    [string]$Host,

    [string]$User = "root",
    [string]$AppDir = "/opt/b2b-contact-miner",
    [string]$Branch = "main",
    [switch]$CopyEnv = $true,
    [switch]$InstallDeps = $true,
    [string]$ServiceToRestart = "b2b-web"
)

$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $PSScriptRoot
$envPath = Join-Path $projectRoot ".env"
$remote = "$User@$Host"

if ($CopyEnv -and -not (Test-Path -LiteralPath $envPath)) {
    throw ".env not found in project root: $envPath"
}

Write-Host "Deploy target: $remote"
Write-Host "AppDir: $AppDir | Branch: $Branch"
Write-Host "Copy .env: $CopyEnv | Install deps: $InstallDeps"

$installDepsFlag = if ($InstallDeps) { "1" } else { "0" }

$remoteScript = @"
set -e
mkdir -p "$AppDir"
cd "$AppDir"

if [ ! -d .git ]; then
  echo "ERROR: $AppDir is not a git repository. Clone it first."
  exit 1
fi

git fetch --all --prune
git checkout "$Branch"
git pull --ff-only origin "$Branch"

if [ ! -d venv ]; then
  python3 -m venv venv
fi

if [ "$installDepsFlag" = "1" ]; then
  ./venv/bin/pip install --upgrade pip
  ./venv/bin/pip install -r requirements.txt
fi

if [ -f ./migrations/apply_llm_tracking_migration.py ]; then
  ./venv/bin/python ./migrations/apply_llm_tracking_migration.py || true
fi
if [ -f ./migrations/apply_contacts_json_migration.py ]; then
  ./venv/bin/python ./migrations/apply_contacts_json_migration.py || true
fi
if [ -f ./migrations/apply_raw_search_response_migration.py ]; then
  ./venv/bin/python ./migrations/apply_raw_search_response_migration.py || true
fi

supervisorctl reread || true
supervisorctl update || true
supervisorctl restart "$ServiceToRestart" || supervisorctl restart all
"@

Write-Host "Running remote deploy commands..."
ssh -o StrictHostKeyChecking=accept-new $remote $remoteScript

if ($CopyEnv) {
    Write-Host "Uploading .env..."
    scp -o StrictHostKeyChecking=accept-new $envPath "${remote}:${AppDir}/.env"

    Write-Host "Running token and health checks..."
    $verifyScript = @"
set -e
cd "$AppDir"
./venv/bin/python -m scripts.test_yandex_token || true
supervisorctl restart "$ServiceToRestart" || supervisorctl restart all
"@
    ssh -o StrictHostKeyChecking=accept-new $remote $verifyScript
}

Write-Host ""
Write-Host "Deployment completed."
Write-Host "Server: $remote"
Write-Host "Health: http://$Host/health-check"
