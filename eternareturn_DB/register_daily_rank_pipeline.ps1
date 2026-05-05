$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$runnerScript = Join-Path $scriptDir "run_daily_rank_pipeline.ps1"
$taskName = "ER_Daily_Rank_Pipeline"

if (-not (Test-Path $runnerScript)) {
    throw "Runner script not found: $runnerScript"
}

$action = New-ScheduledTaskAction `
    -Execute "powershell.exe" `
    -Argument "-NoProfile -ExecutionPolicy Bypass -File `"$runnerScript`""

$trigger = New-ScheduledTaskTrigger -Daily -At 00:05

$settings = New-ScheduledTaskSettingsSet `
    -StartWhenAvailable `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -MultipleInstances IgnoreNew

Register-ScheduledTask `
    -TaskName $taskName `
    -Action $action `
    -Trigger $trigger `
    -Settings $settings `
    -Description "Collect rank matches until daily 00:00 cutoff, retrain the model, and refresh all-predict outputs."

Write-Host "Registered scheduled task: $taskName"
