param(
    [Parameter(Mandatory = $true)][string]$RdsHost,
    [int]$Port = 3306,
    [Parameter(Mandatory = $true)][string]$Database,
    [Parameter(Mandatory = $true)][string]$User,
    [Parameter(Mandatory = $true)][string]$Password
)

$ErrorActionPreference = "Stop"

$mysql = (Get-Command mysql).Source
if (-not $mysql) {
    throw "mysql executable not found."
}

$query = @"
SELECT 'rankdb_v2' AS table_name, COUNT(*) AS row_count FROM rankdb_v2
UNION ALL
SELECT 'rankdb_train_base' AS table_name, COUNT(*) AS row_count FROM rankdb_train_base
UNION ALL
SELECT 'daily_position_synergy_cache' AS table_name, COUNT(*) AS row_count FROM daily_position_synergy_cache
UNION ALL
SELECT 'daily_score_metric_cache' AS table_name, COUNT(*) AS row_count FROM daily_score_metric_cache;
"@

Write-Host "Testing RDS connectivity to $RdsHost:$Port ..."
& $mysql "--host=$RdsHost" "--port=$Port" "--user=$User" "--password=$Password" "--default-character-set=utf8mb4" "--database=$Database" "-e" "SELECT NOW() AS current_time, DATABASE() AS current_database;"

Write-Host ""
Write-Host "Checking key table counts ..."
& $mysql "--host=$RdsHost" "--port=$Port" "--user=$User" "--password=$Password" "--default-character-set=utf8mb4" "--database=$Database" "-e" $query
