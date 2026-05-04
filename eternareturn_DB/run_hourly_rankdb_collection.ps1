$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$pythonExe = "C:\Users\wnsgu\Anaconda3\python.exe"
$collectorScript = Join-Path $scriptDir "collect_recent_rankdb.py"
$logDir = Join-Path $scriptDir "logs"

if (-not (Test-Path $pythonExe)) {
    throw "Python executable not found: $pythonExe"
}

if (-not (Test-Path $collectorScript)) {
    throw "Collector script not found: $collectorScript"
}

New-Item -ItemType Directory -Force -Path $logDir | Out-Null

$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$logPath = Join-Path $logDir "rankdb_collect_$timestamp.log"

Push-Location $scriptDir
try {
    & $pythonExe $collectorScript *>&1 | Tee-Object -FilePath $logPath
    if ($LASTEXITCODE -ne 0) {
        throw "Collector exited with code $LASTEXITCODE"
    }
}
finally {
    Pop-Location
}
