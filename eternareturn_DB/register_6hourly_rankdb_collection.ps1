$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$registerScript = Join-Path $scriptDir "register_hourly_rankdb_collection.ps1"

if (-not (Test-Path $registerScript)) {
    throw "Register script not found: $registerScript"
}

& $registerScript
