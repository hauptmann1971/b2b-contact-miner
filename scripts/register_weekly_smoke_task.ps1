param(
    [string]$ProjectRoot = "C:\Users\romanov\PycharmProjects\b2b-contact-miner",
    [string]$TaskName = "B2BContactMinerWeeklySmoke",
    [string]$PythonExe = "py",
    [int]$Limit = 15,
    [double]$MinWithContactsRate = 20.0,
    [double]$MaxZeroPageRate = 60.0,
    [int]$MaxFailures = 0,
    [string]$Day = "SUN",
    [string]$Time = "03:00"
)

$ErrorActionPreference = "Stop"

if (-not (Test-Path -LiteralPath $ProjectRoot)) {
    throw "Project root not found: $ProjectRoot"
}

$runnerPath = Join-Path $ProjectRoot "checkers\run_weekly_smoke.py"
if (-not (Test-Path -LiteralPath $runnerPath)) {
    throw "Weekly smoke runner not found: $runnerPath"
}

$command = "$PythonExe checkers/run_weekly_smoke.py --limit $Limit --min-with-contacts-rate $MinWithContactsRate --max-zero-page-rate $MaxZeroPageRate --max-failures $MaxFailures"
$taskRun = "powershell.exe -NoProfile -ExecutionPolicy Bypass -Command `"Set-Location -LiteralPath '$ProjectRoot'; $command`""

Write-Host "Registering task '$TaskName'..."
Write-Host "Schedule: weekly $Day at $Time"
Write-Host "Command: $command"

schtasks /Create /TN $TaskName /TR $taskRun /SC WEEKLY /D $Day /ST $Time /F | Out-Host

Write-Host "Done."
Write-Host "Check task: schtasks /Query /TN $TaskName /V /FO LIST"
Write-Host "Run now:    schtasks /Run /TN $TaskName"
