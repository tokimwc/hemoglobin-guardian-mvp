@echo off
chcp 65001 > nul
setlocal EnableDelayedExpansion

echo [INFO] Checking environment variables...

REM Required environment variables
set "REQUIRED_VARS=GOOGLE_CLOUD_PROJECT GOOGLE_CLOUD_LOCATION VISION_AI_LOCATION VERTEX_AI_LOCATION GEMINI_MODEL_ID SERVICE_NAME ARTIFACT_REGISTRY_LOCATION ARTIFACT_REGISTRY_REPOSITORY"

REM Check if .env file exists
if not exist ".env" (
    echo [ERROR] .env file not found in the current directory
    exit /b 1
)

REM Load environment variables from .env
for /f "usebackq tokens=1,* delims==" %%a in (".env") do (
    set "%%a=%%b"
)

REM Initialize variables
set "MISSING_VARS="
set "ERROR=0"

REM Check environment variables
for %%v in (%REQUIRED_VARS%) do (
    if not defined %%v (
        set "MISSING_VARS=!MISSING_VARS! %%v"
        set "ERROR=1"
    )
)

REM Check credential files
if not exist "%GOOGLE_APPLICATION_CREDENTIALS%" (
    echo [ERROR] Google Cloud credentials file not found at %GOOGLE_APPLICATION_CREDENTIALS%
    set "ERROR=1"
)

if not exist "%FIREBASE_CREDENTIALS_PATH%" (
    echo [ERROR] Firebase credentials file not found at %FIREBASE_CREDENTIALS_PATH%
    set "ERROR=1"
)

REM Report errors or success
if %ERROR%==1 (
    echo.
    if defined MISSING_VARS echo [ERROR] Missing required environment variables:%MISSING_VARS%
    echo [ERROR] Please check your .env file and ensure all required variables are set.
    exit /b 1
) else (
    echo [SUCCESS] All environment variables are properly set.
    echo.
    echo Current configuration:
    echo ---------------------
    echo Project ID: %GOOGLE_CLOUD_PROJECT%
    echo Region: %GOOGLE_CLOUD_LOCATION%
    echo Service Name: %SERVICE_NAME%
    echo Vision AI Location: %VISION_AI_LOCATION%
    echo Vertex AI Location: %VERTEX_AI_LOCATION%
    echo.
    echo [SUCCESS] Environment check completed successfully.
    exit /b 0
) 