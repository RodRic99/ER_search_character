param(
    [string]$DbHost = "127.0.0.1",
    [int]$Port = 3306,
    [Parameter(Mandatory = $true)][string]$Database,
    [Parameter(Mandatory = $true)][string]$User,
    [Parameter(Mandatory = $true)][string]$Password,
    [string[]]$Tables = @(),
    [string]$OutputPath = ""
)

$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$tmpDir = Join-Path $scriptDir "tmp"
New-Item -ItemType Directory -Force -Path $tmpDir | Out-Null

if ([string]::IsNullOrWhiteSpace($OutputPath)) {
    $dumpName = if ($Tables.Count -gt 0) {
        "local-$($Tables -join '_')-export.sql.zip"
    }
    else {
        "local-db-export.sql.zip"
    }
    $OutputPath = Join-Path $tmpDir $dumpName
}

$mysqldump = (Get-Command mysqldump).Source
if (-not $mysqldump) {
    throw "mysqldump executable not found."
}

$plainSqlPath = [System.IO.Path]::ChangeExtension($OutputPath, ".sql")
if (Test-Path $plainSqlPath) {
    Remove-Item $plainSqlPath -Force
}
if (Test-Path $OutputPath) {
    Remove-Item $OutputPath -Force
}

$args = @(
    "--host=$DbHost"
    "--port=$Port"
    "--user=$User"
    "--password=$Password"
    "--default-character-set=utf8mb4"
    "--single-transaction"
    "--routines"
    "--triggers"
    "--hex-blob"
)

if ($Tables.Count -gt 0) {
    $args += $Database
    $args += $Tables
}
else {
    $args += "--databases"
    $args += $Database
}

if ($Tables.Count -gt 0) {
    Write-Host "Exporting table(s) '$($Tables -join ", ")' from database '$Database' at ${DbHost}:$Port ..."
}
else {
    Write-Host "Exporting local database '$Database' from ${DbHost}:$Port ..."
}
& $mysqldump @args | Out-File -FilePath $plainSqlPath -Encoding utf8

if (-not (Test-Path $plainSqlPath)) {
    throw "SQL dump was not created."
}

Write-Host "Compressing dump ..."
Compress-Archive -Path $plainSqlPath -DestinationPath $OutputPath -Force
Remove-Item $plainSqlPath -Force

Write-Host "Done: $OutputPath"
