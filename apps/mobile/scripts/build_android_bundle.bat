@echo off
REM Build Android App Bundle for Play Store
REM Usage: scripts\build_android_bundle.bat [API_URL]
REM Example: scripts\build_android_bundle.bat https://api.icfesleveling.com/api/v1

set API_URL=%1
if "%API_URL%"=="" (
    echo ERROR: Debes proporcionar la URL de la API
    echo Uso: scripts\build_android_bundle.bat https://tu-api.com/api/v1
    exit /b 1
)

echo Building Android App Bundle (Play Store)...
echo API URL: %API_URL%
cd /d "%~dp0.."

flutter build appbundle --release --dart-define=API_URL=%API_URL%

echo.
echo AAB generado en: build\app\outputs\bundle\release\app-release.aab
pause
