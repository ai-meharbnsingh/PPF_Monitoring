@echo off
REM ============================================================
REM PPF Workshop Monitoring — PostgreSQL Setup Script
REM Run this once to create the ppf_user and ppf_monitoring DB
REM ============================================================

SET PGBIN=C:\Program Files\PostgreSQL\18\bin
SET PGHOST=localhost
SET PGPORT=5432

echo.
echo ==========================================
echo  PPF Workshop — PostgreSQL Setup
echo ==========================================
echo.
echo This will create:
echo   User:     ppf_user (password: ppf_dev_password_2026)
echo   Database: ppf_monitoring
echo.
set /p PGPASSWORD=Enter your postgres superuser password:

SET PGPASSWORD=%PGPASSWORD%

echo.
echo [1/3] Creating ppf_user...
"%PGBIN%\psql.exe" -U postgres -h 127.0.0.1 -p %PGPORT% -c "DO $$ BEGIN IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'ppf_user') THEN CREATE USER ppf_user WITH PASSWORD 'ppf_dev_password_2026'; END IF; END $$;"

echo.
echo [2/3] Creating ppf_monitoring database...
"%PGBIN%\psql.exe" -U postgres -h 127.0.0.1 -p %PGPORT% -c "SELECT 1 FROM pg_database WHERE datname='ppf_monitoring'" | findstr /C:"1 row" >nul
if errorlevel 1 (
    "%PGBIN%\psql.exe" -U postgres -h 127.0.0.1 -p %PGPORT% -c "CREATE DATABASE ppf_monitoring OWNER ppf_user ENCODING 'UTF8';"
) else (
    echo   ppf_monitoring already exists — skipping.
)

echo.
echo [3/3] Granting privileges...
"%PGBIN%\psql.exe" -U postgres -h 127.0.0.1 -p %PGPORT% -c "GRANT ALL PRIVILEGES ON DATABASE ppf_monitoring TO ppf_user;"
"%PGBIN%\psql.exe" -U postgres -h 127.0.0.1 -p %PGPORT% -d ppf_monitoring -c "GRANT ALL ON SCHEMA public TO ppf_user;"
"%PGBIN%\psql.exe" -U postgres -h 127.0.0.1 -p %PGPORT% -d ppf_monitoring -c "ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO ppf_user; ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO ppf_user;"

echo.
echo ==========================================
echo  Done! Test connection with:
echo  psql -U ppf_user -h 127.0.0.1 -d ppf_monitoring
echo ==========================================
echo.
SET PGPASSWORD=
pause
