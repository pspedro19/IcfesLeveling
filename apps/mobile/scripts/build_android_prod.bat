@echo off
REM Build Android APK for Production
REM Usage: scripts\build_android_prod.bat [API_URL]
REM Example: scripts\build_android_prod.bat https://api.icfesleveling.com/api/v1

set API_URL=%1
if "%API_URL%"=="" (
    echo ERROR: Debes proporcionar la URL de la API
    echo Uso: scripts\build_android_prod.bat https://tu-api.com/api/v1
    exit /b 1
)

echo Building Android APK (Production)...
echo API URL: %API_URL%
cd /d "%~dp0.."

flutter build apk --release --dart-define=API_URL=%API_URL%

echo.
echo APK generado en: build\app\outputs\flutter-apk\app-release.apk
pause
