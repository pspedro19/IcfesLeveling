@echo off
REM Build Android APK for Development
REM Usage: scripts\build_android_dev.bat

echo Building Android APK (Development)...
cd /d "%~dp0.."

flutter build apk --debug --dart-define=API_URL=http://10.0.2.2:4000/api/v1

echo.
echo APK generado en: build\app\outputs\flutter-apk\app-debug.apk
pause
