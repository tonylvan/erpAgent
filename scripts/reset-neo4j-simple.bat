@echo off
chcp 65001 >nul
echo ==========================================
echo   Neo4j Password Reset Tool
echo ==========================================
echo.

set "NEO4J_PASSWORD=Tony1985"
set "NEO4J_HOME=C:\Users\Administrator\AppData\Local\Neo4j\Relate\Data\dbmss"

echo [1/4] Searching for Neo4j installation...
if exist "%NEO4J_HOME%" (
    echo Found Neo4j home: %NEO4J_HOME%
    for /d %%D in ("%NEO4J_HOME%\dbms-*") do (
        set "DBMS_PATH=%%D"
        echo Found database: %%D
        goto :found
    )
) else (
    echo Neo4j home not found at default location
    echo Please manually specify the path
    exit /b 1
)

:found
echo.
echo [2/4] Stopping Neo4j service...
if exist "%DBMS_PATH%\bin\neo4j.bat" (
    call "%DBMS_PATH%\bin\neo4j.bat" stop
    timeout /t 3 /nobreak >nul
)

echo.
echo [3/4] Resetting password...
if exist "%DBMS_PATH%\bin\neo4j-admin.bat" (
    call "%DBMS_PATH%\bin\neo4j-admin.bat" dbms set-initial-password %NEO4J_PASSWORD%
    if %errorlevel% neq 0 (
        echo Warning: Password reset command returned error %errorlevel%
    ) else (
        echo Password reset successfully!
    )
) else (
    echo ERROR: neo4j-admin.bat not found!
    echo Looked in: %DBMS_PATH%\bin\
    exit /b 1
)

echo.
echo [4/4] Starting Neo4j service...
if exist "%DBMS_PATH%\bin\neo4j.bat" (
    call "%DBMS_PATH%\bin\neo4j.bat" start
    timeout /t 5 /nobreak >nul
)

echo.
echo ==========================================
echo   Password Reset Complete!
echo ==========================================
echo.
echo New Credentials:
echo   Username: neo4j
echo   Password: %NEO4J_PASSWORD%
echo.
echo Connection Details:
echo   Bolt URI: bolt://localhost:7687
echo   HTTP URI: http://localhost:7474
echo.
pause
