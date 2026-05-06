param(
    [Parameter(Mandatory = $true)][string]$PemPath,
    [Parameter(Mandatory = $true)][string]$Ec2Host,
    [string]$Ec2User = "ubuntu",
    [string]$RemoteDir = "~/er_migration",
    [Parameter(Mandatory = $true)][string]$LocalDumpPath
)

$ErrorActionPreference = "Stop"

if (-not (Test-Path $PemPath)) {
    throw "PEM file not found: $PemPath"
}

if (-not (Test-Path $LocalDumpPath)) {
    throw "Dump file not found: $LocalDumpPath"
}

$scp = (Get-Command scp).Source
$ssh = (Get-Command ssh).Source

if (-not $scp) {
    throw "scp executable not found."
}
if (-not $ssh) {
    throw "ssh executable not found."
}

Write-Host "Creating remote directory on EC2 ..."
& $ssh -i $PemPath "${Ec2User}@${Ec2Host}" "mkdir -p $RemoteDir"

Write-Host "Uploading dump to EC2 ..."
& $scp -i $PemPath $LocalDumpPath "${Ec2User}@${Ec2Host}:$RemoteDir/"

Write-Host "Upload completed."
