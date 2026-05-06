$ErrorActionPreference = "Stop"

$taskName = "ER_6Hourly_Rankdb_Collection"
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$runnerScript = Join-Path $scriptDir "run_hourly_rankdb_collection.cmd"

if (-not (Test-Path $runnerScript)) {
    throw "Runner script not found: $runnerScript"
}

$taskCommand = "`"$runnerScript`""
$startTime = (Get-Date).AddMinutes(1).ToString("HH:mm")

$arguments = @(
    "/Create",
    "/TN", $taskName,
    "/TR", $taskCommand,
    "/SC", "HOURLY",
    "/MO", "6",
    "/ST", $startTime,
    "/F"
)

$process = Start-Process -FilePath "schtasks.exe" -ArgumentList $arguments -NoNewWindow -Wait -PassThru

if ($process.ExitCode -ne 0) {
    throw "schtasks.exe failed with exit code $($process.ExitCode)"
}

Write-Host "Registered scheduled task: $taskName"
Write-Host "Runner script: $runnerScript"
Write-Host "First run starts at: $startTime"
Write-Host "Repeat interval: every 6 hours"
