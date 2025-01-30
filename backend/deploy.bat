@echo off
chcp 65001 > nul

setlocal EnableDelayedExpansion

REM Suppress batch termination prompt
set "PROMPT=$G"

echo [DEBUG] Script started
echo [DEBUG] Current directory: %CD%

REM Error handling settings
set "ERRORLEVEL=0"
set "ERROR_COUNT=0"
set "MAX_RETRIES=3"
set "RETRY_DELAY=30"

REM Docker settings
set "DOCKER_MEMORY=4g"
set "DOCKER_MEMORY_SWAP=4g"
set "DOCKER_BUILDKIT=1"
set "DOCKER_DEFAULT_PLATFORM=linux/amd64"
set "DOCKER_SCAN_SUGGEST=false"
set "BUILDKIT_STEP_LOG_MAX_SIZE=10485760"
set "BUILDKIT_STEP_LOG_MAX_SPEED=10485760"

REM Log settings
set "LOG_FILE=%~dp0build_error.log"
if exist "%LOG_FILE%" del /f /q "%LOG_FILE%"

echo [DEBUG] Cleaning up Docker system...
docker system prune -f --volumes >nul 2>&1
docker builder prune -f >nul 2>&1

echo [DEBUG] Checking prerequisites...
where docker >nul 2>&1 || (
    echo [ERROR] Docker is not installed or not in PATH
    exit /b 1
)

if not exist "Dockerfile" (
    echo [ERROR] Dockerfile not found in %CD%
    exit /b 1
)

if not exist ".env" (
    echo [ERROR] .env file not found in %CD%
    exit /b 1
)

:build_retry
set /a ERROR_COUNT+=1
echo [INFO] Build attempt %ERROR_COUNT% of %MAX_RETRIES%

echo [DEBUG] Starting Docker build with optimized settings...
docker build --no-cache --progress=plain ^
    --memory=%DOCKER_MEMORY% ^
    --memory-swap=%DOCKER_MEMORY_SWAP% ^
    --network=host ^
    --build-arg BUILDKIT_INLINE_CACHE=1 ^
    --build-arg DOCKER_BUILDKIT=1 ^
    --add-host=host.docker.internal:host-gateway ^
    --ulimit nofile=65536:65536 ^
    -t hemoglobin-backend . 2>"%LOG_FILE%"

if !ERRORLEVEL! neq 0 (
    echo [ERROR] Build failed with code !ERRORLEVEL!
    type "%LOG_FILE%"
    
    if !ERROR_COUNT! lss !MAX_RETRIES! (
        echo [DEBUG] Cleaning up and retrying in !RETRY_DELAY! seconds...
        docker system prune -f --volumes >nul 2>&1
        docker builder prune -f >nul 2>&1
        timeout /t !RETRY_DELAY! /nobreak >nul
        
        REM Adjust memory limits for next retry
        set /a RETRY_DELAY*=2
        if !ERROR_COUNT! equ 2 (
            set "DOCKER_MEMORY=3g"
            set "DOCKER_MEMORY_SWAP=3g"
        )
        goto :build_retry
    ) else (
        echo [FATAL] Build failed after !MAX_RETRIES! attempts
        echo [DEBUG] Full build logs saved to %LOG_FILE%
        exit /b 1
    )
)

echo [SUCCESS] Build completed successfully
exit /b 0 