@echo off
echo ========================================
echo    Iniciando Backend ICFES Leveling
echo ========================================
echo.

REM Verificar si Python está instalado
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python no está instalado o no está en el PATH
    echo Por favor, instala Python desde https://python.org
    pause
    exit /b 1
)

REM Verificar si estamos en el directorio correcto
if not exist "app" (
    echo ERROR: No se encontró el directorio 'app'
    echo Asegúrate de ejecutar este script desde apps/backend/
    pause
    exit /b 1
)

REM Verificar si existe el entorno virtual
if not exist "venv" (
    echo Creando entorno virtual...
    python -m venv venv
    if errorlevel 1 (
        echo ERROR: No se pudo crear el entorno virtual
        pause
        exit /b 1
    )
)

REM Activar entorno virtual
echo Activando entorno virtual...
call venv\Scripts\activate.bat
if errorlevel 1 (
    echo ERROR: No se pudo activar el entorno virtual
    pause
    exit /b 1
)

REM Instalar dependencias si no están instaladas
echo Verificando dependencias...
pip show fastapi >nul 2>&1
if errorlevel 1 (
    echo Instalando dependencias...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo ERROR: No se pudieron instalar las dependencias
        pause
        exit /b 1
    )
)

echo.
echo ========================================
echo    Configuración del Servidor
echo ========================================
echo Host: 0.0.0.0
echo Puerto: 4000
echo URL: http://localhost:4000
echo.
echo Presiona Ctrl+C para detener el servidor
echo ========================================
echo.

REM Iniciar el servidor
python -m uvicorn app.main:app --host 0.0.0.0 --port 4000 --reload

echo.
echo Servidor detenido.
pause 