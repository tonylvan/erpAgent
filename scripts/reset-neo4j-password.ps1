# Neo4j Password Reset Script
# This script resets the Neo4j password using neo4j-admin

param(
    [Parameter(Mandatory=$true)]
    [string]$NewPassword,
    
    [string]$Neo4jHome = "C:\Users\Administrator\AppData\Local\Neo4j\Relate\Data\dbmss"
)

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "  Neo4j Password Reset Tool" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# Find Neo4j installation
Write-Host "[1/5] Searching for Neo4j installation..." -ForegroundColor Yellow

$neo4jPaths = @()
if (Test-Path $Neo4jHome) {
    $neo4jPaths = Get-ChildItem -Path $Neo4jHome -Directory -Filter "dbms-*" | Select-Object -ExpandProperty FullName
}

if ($neo4jPaths.Count -eq 0) {
    # Try alternative paths
    $altPaths = @(
        "C:\Program Files\Neo4j",
        "C:\Program Files (x86)\Neo4j",
        "$env:USERPROFILE\Neo4j",
        "$env:LOCALAPPDATA\Neo4j"
    )
    
    foreach ($path in $altPaths) {
        if (Test-Path $path) {
            $found = Get-ChildItem -Path $path -Recurse -Filter "neo4j-admin.bat" -ErrorAction SilentlyContinue | Select-Object -First 1
            if ($found) {
                $neo4jPaths = @($found.Directory.Parent.FullName)
                break
            }
        }
    }
}

if ($neo4jPaths.Count -eq 0) {
    Write-Host "ERROR: Could not find Neo4j installation!" -ForegroundColor Red
    Write-Host "Please specify the correct path using -Neo4jHome parameter" -ForegroundColor Red
    exit 1
}

$selectedPath = $neo4jPaths[0]
Write-Host "Found Neo4j at: $selectedPath" -ForegroundColor Green
Write-Host ""

# Check if Neo4j is running
Write-Host "[2/5] Checking Neo4j service status..." -ForegroundColor Yellow
$neo4jProcess = Get-Process -Name "neo4j*" -ErrorAction SilentlyContinue

if ($neo4jProcess) {
    Write-Host "Neo4j is currently running. Stopping service..." -ForegroundColor Yellow
    
    $stopScript = Join-Path $selectedPath "bin\neo4j.bat"
    if (Test-Path $stopScript) {
        & $stopScript stop
        Start-Sleep -Seconds 3
    } else {
        # Try to stop via Windows service
        $service = Get-Service -Name "neo4j*" -ErrorAction SilentlyContinue
        if ($service) {
            Stop-Service -Name $service.Name -Force
            Start-Sleep -Seconds 3
        } else {
            # Kill process as last resort
            Stop-Process -Name "neo4j*" -Force -ErrorAction SilentlyContinue
            Start-Sleep -Seconds 2
        }
    }
    Write-Host "Neo4j stopped successfully" -ForegroundColor Green
} else {
    Write-Host "Neo4j is not running" -ForegroundColor Green
}
Write-Host ""

# Reset password using neo4j-admin
Write-Host "[3/5] Resetting password..." -ForegroundColor Yellow

$adminTool = Join-Path $selectedPath "bin\neo4j-admin.bat"
if (-not (Test-Path $adminTool)) {
    # Try alternative location
    $adminTool = Join-Path $selectedPath "bin\tools\neo4j-admin.bat"
}

if (-not (Test-Path $adminTool)) {
    Write-Host "ERROR: Could not find neo4j-admin.bat!" -ForegroundColor Red
    Write-Host "Searched at: $adminTool" -ForegroundColor Red
    exit 1
}

Write-Host "Using admin tool: $adminTool" -ForegroundColor Gray

# Execute password reset
try {
    $output = & $adminTool dbms set-initial-password $NewPassword 2>&1
    $exitCode = $LASTEXITCODE
    
    if ($exitCode -eq 0) {
        Write-Host "Password reset successfully!" -ForegroundColor Green
    } else {
        Write-Host "Warning: Command returned exit code $exitCode" -ForegroundColor Yellow
        Write-Host "Output: $output" -ForegroundColor Gray
    }
} catch {
    Write-Host "ERROR: Failed to reset password" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    exit 1
}
Write-Host ""

# Start Neo4j service
Write-Host "[4/5] Starting Neo4j service..." -ForegroundColor Yellow

$startScript = Join-Path $selectedPath "bin\neo4j.bat"
if (Test-Path $startScript) {
    & $startScript start
    Start-Sleep -Seconds 5
} else {
    # Try to start via Windows service
    $service = Get-Service -Name "neo4j*" -ErrorAction SilentlyContinue
    if ($service) {
        Start-Service -Name $service.Name
        Start-Sleep -Seconds 5
    }
}

# Verify Neo4j is running
$neo4jProcess = Get-Process -Name "neo4j*" -ErrorAction SilentlyContinue
if ($neo4jProcess) {
    Write-Host "Neo4j started successfully!" -ForegroundColor Green
} else {
    Write-Host "Warning: Could not verify Neo4j is running" -ForegroundColor Yellow
}
Write-Host ""

# Update .env file if exists
Write-Host "[5/5] Updating configuration files..." -ForegroundColor Yellow

$envFiles = @(
    "D:\erpAgent\backend\.env",
    "D:\erpAgent\.env",
    "$PSScriptRoot\..\.env"
)

foreach ($envFile in $envFiles) {
    if (Test-Path $envFile) {
        Write-Host "Found .env file: $envFile" -ForegroundColor Gray
        
        $content = Get-Content $envFile -Raw
        
        # Update Neo4j password
        if ($content -match "NEO4J_PASSWORD=.*") {
            $content = $content -replace "NEO4J_PASSWORD=.*", "NEO4J_PASSWORD=$NewPassword"
            Set-Content -Path $envFile -Value $content -NoNewline
            Write-Host "Updated NEO4J_PASSWORD in $envFile" -ForegroundColor Green
        }
        
        # Update Neo4j URI if needed
        if ($content -match "NEO4J_URI=.*") {
            Write-Host "Neo4j URI configuration found" -ForegroundColor Gray
        }
    }
}
Write-Host ""

# Summary
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "  Password Reset Complete!" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "New Credentials:" -ForegroundColor White
Write-Host "  Username: neo4j" -ForegroundColor Green
Write-Host "  Password: $NewPassword" -ForegroundColor Green
Write-Host ""
Write-Host "Connection Details:" -ForegroundColor White
Write-Host "  Bolt URI: bolt://localhost:7687" -ForegroundColor Gray
Write-Host "  HTTP URI: http://localhost:7474" -ForegroundColor Gray
Write-Host ""
Write-Host "Test Connection:" -ForegroundColor White
Write-Host "  Open Neo4j Browser at http://localhost:7474" -ForegroundColor Gray
Write-Host "  Login with the new credentials" -ForegroundColor Gray
Write-Host ""
