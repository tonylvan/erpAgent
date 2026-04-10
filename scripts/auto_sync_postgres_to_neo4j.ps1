# PostgreSQL to Neo4j Auto Sync Script
# Run this script to sync data from PostgreSQL to Neo4j

$ErrorActionPreference = "Stop"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host " PostgreSQL to Neo4j Auto Sync" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$scriptPath = "D:\erpAgent\scripts\sync_postgres_to_neo4j.py"

if (-not (Test-Path $scriptPath)) {
    Write-Host "[ERROR] Sync script not found: $scriptPath" -ForegroundColor Red
    exit 1
}

Write-Host "Sync script: $scriptPath" -ForegroundColor Green
Write-Host ""

# Run sync
Write-Host "Starting sync..." -ForegroundColor Yellow
Write-Host ""

try {
    $startTime = Get-Date
    
    # Run Python sync script
    $output = python $scriptPath 2>&1
    
    $endTime = Get-Date
    $duration = ($endTime - $startTime).TotalSeconds
    
    Write-Host $output
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Green
    Write-Host " Sync completed in $([math]::Round($duration, 1)) seconds" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Green
    Write-Host ""
    
    # Log to file
    $logDir = "D:\erpAgent\logs"
    if (-not (Test-Path $logDir)) {
        New-Item -Path $logDir -ItemType Directory -Force | Out-Null
    }
    
    $logFile = Join-Path $logDir "sync_$(Get-Date -Format 'yyyyMMdd').log"
    $logEntry = "[$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')] Sync completed in $([math]::Round($duration, 1))s"
    Add-Content -Path $logFile -Value $logEntry
    
    Write-Host "Log: $logFile" -ForegroundColor Gray
    
} catch {
    Write-Host "[ERROR] Sync failed: $_" -ForegroundColor Red
    Write-Host $_.Exception.Message
    exit 1
}