@echo off
REM =====================================================
REM SCRIPT DE INICIO LOCAL - ICFES LEVELING
REM =====================================================
REM Este script inicia todos los servicios localmente
REM sin Docker para desarrollo rápido
REM =====================================================

echo =====================================================
echo    INICIANDO ICFES LEVELING - MODO LOCAL
echo =====================================================
echo.

REM Colores para output (Windows no soporta colores nativamente en batch)
REM pero podemos usar echo para mensajes claros

REM Verificar Python
echo [1/7] Verificando Python...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python no está instalado
    echo Instala Python 3.11+ desde https://www.python.org
    pause
    exit /b 1
)
echo OK - Python encontrado

REM Verificar Node.js
echo [2/7] Verificando Node.js...
node --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Node.js no está instalado
    echo Instala Node.js 18+ desde https://nodejs.org
    pause
    exit /b 1
)
echo OK - Node.js encontrado

REM Instalar dependencias del backend si no existen
echo [3/7] Verificando dependencias del backend...
cd apps\backend
if not exist "venv" (
    echo Creando entorno virtual...
    python -m venv venv
    call venv\Scripts\activate
    pip install -r requirements.txt
) else (
    call venv\Scripts\activate
)
echo OK - Dependencias del backend listas

REM Instalar dependencias del frontend si no existen
echo [4/7] Verificando dependencias del frontend...
cd ..\frontend
if not exist "node_modules" (
    echo Instalando dependencias del frontend...
    npm install
)
echo OK - Dependencias del frontend listas

REM Crear archivo .env si no existe
cd ..\..
if not exist ".env" (
    echo [5/7] Creando archivo .env...
    (
        echo # Environment Configuration
        echo ENVIRONMENT=development
        echo DEBUG=true
        echo.
        echo # Database - Usando SQLite para desarrollo local
        echo DATABASE_URL=sqlite:///./icfes_local.db
        echo.
        echo # JWT
        echo JWT_SECRET=dev-secret-key-change-in-production
        echo ALGORITHM=HS256
        echo ACCESS_TOKEN_EXPIRE_MINUTES=30
        echo.
        echo # API URLs
        echo NEXT_PUBLIC_API_URL=http://localhost:4000
        echo NEXT_PUBLIC_WS_URL=ws://localhost:4002
        echo.
        echo # Frontend
        echo NEXT_PUBLIC_APP_URL=http://localhost:4001
    ) > .env
    echo OK - Archivo .env creado
) else (
    echo [5/7] Archivo .env ya existe
)

echo.
echo [6/7] Iniciando servicios...
echo.

REM Iniciar backend en una nueva ventana
echo Iniciando Backend (FastAPI) en puerto 4000...
start "ICFES Backend" cmd /k "cd apps\backend && venv\Scripts\activate && python -m uvicorn app.main:app --host 0.0.0.0 --port 4000 --reload"

REM Esperar 3 segundos para que el backend inicie
timeout /t 3 /nobreak >nul

REM Iniciar frontend en una nueva ventana
echo Iniciando Frontend (Next.js) en puerto 4001...
start "ICFES Frontend" cmd /k "cd apps\frontend && npm run dev"

REM Iniciar WebSocket server (opcional)
echo Iniciando WebSocket Server en puerto 4002...
start "ICFES WebSocket" cmd /k "cd apps\websocket && python main.py"

echo.
echo [7/7] Esperando que los servicios inicien...
timeout /t 5 /nobreak >nul

echo.
echo =====================================================
echo    ICFES LEVELING INICIADO EXITOSAMENTE
echo =====================================================
echo.
echo Servicios disponibles:
echo   - Frontend:  http://localhost:4001
echo   - Backend:   http://localhost:4000
echo   - API Docs:  http://localhost:4000/docs
echo   - WebSocket: ws://localhost:4002
echo.
echo Para detener los servicios, cierra las ventanas de comando
echo.
echo Presiona cualquier tecla para abrir el navegador...
pause >nul

REM Abrir el navegador
start http://localhost:4001

echo.
echo Sistema iniciado. Esta ventana se puede cerrar.
pause