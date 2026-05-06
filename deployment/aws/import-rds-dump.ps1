param(
    [Parameter(Mandatory = $true)][string]$RdsHost,
    [int]$Port = 3306,
    [Parameter(Mandatory = $true)][string]$Database,
    [Parameter(Mandatory = $true)][string]$User,
    [Parameter(Mandatory = $true)][string]$Password,
    [Parameter(Mandatory = $true)][string]$DumpPath
)

$ErrorActionPreference = "Stop"

$mysql = (Get-Command mysql).Source
if (-not $mysql) {
    throw "mysql executable not found."
}

if (-not (Test-Path $DumpPath)) {
    throw "Dump file not found: $DumpPath"
}

$tempImportDir = Join-Path $env:TEMP "er_search_character_rds_import"
New-Item -ItemType Directory -Force -Path $tempImportDir | Out-Null
$tmpSqlPath = Join-Path $tempImportDir "import.sql"
if (Test-Path $tmpSqlPath) {
    Remove-Item $tmpSqlPath -Force
}

$extension = [System.IO.Path]::GetExtension($DumpPath).ToLowerInvariant()
if ($extension -eq ".zip") {
    Expand-Archive -Path $DumpPath -DestinationPath $tempImportDir -Force
    $expandedSql = Get-ChildItem $tempImportDir -Filter *.sql | Sort-Object LastWriteTime -Descending | Select-Object -First 1
    if (-not $expandedSql) {
        throw "No SQL file found after expanding archive."
    }
    Copy-Item $expandedSql.FullName $tmpSqlPath -Force
}
else {
    Copy-Item $DumpPath $tmpSqlPath -Force
}

Write-Host "Importing dump into RDS '$Database' at $RdsHost:$Port ..."
$normalizedSqlPath = $tmpSqlPath -replace "\\", "/"
& $mysql "--host=$RdsHost" "--port=$Port" "--user=$User" "--password=$Password" "--default-character-set=utf8mb4" $Database "--execute=SOURCE $normalizedSqlPath"

Write-Host "Import completed."
