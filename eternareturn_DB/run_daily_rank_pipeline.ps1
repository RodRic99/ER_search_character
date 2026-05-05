$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$pythonExe = "C:\Users\wnsgu\Anaconda3\python.exe"
$pipelineScript = Join-Path $scriptDir "daily_rank_pipeline.py"
$logDir = Join-Path $scriptDir "logs"

if (-not (Test-Path $pythonExe)) {
    throw "Python executable not found: $pythonExe"
}

if (-not (Test-Path $pipelineScript)) {
    throw "Pipeline script not found: $pipelineScript"
}

New-Item -ItemType Directory -Force -Path $logDir | Out-Null

$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$logPath = Join-Path $logDir "daily_rank_pipeline_$timestamp.log"

Push-Location $scriptDir
try {
    & $pythonExe $pipelineScript *>&1 | Tee-Object -FilePath $logPath
    if ($LASTEXITCODE -ne 0) {
        throw "Daily pipeline exited with code $LASTEXITCODE"
    }
}
finally {
    Pop-Location
}
