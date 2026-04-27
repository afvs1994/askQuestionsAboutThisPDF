@echo off
chcp 65001 >nul 2>&1
echo ==========================================
echo  Iniciando Private Document RAG API
echo ==========================================
echo.

REM Detecta o diretorio onde este script esta localizado
set "SCRIPT_DIR=%~dp0"
set "SCRIPT_DIR=%SCRIPT_DIR:~0,-1%"

REM --- Verificar / Iniciar Ollama ---
echo [0/3] Verificando Ollama...
curl -s http://localhost:11434/api/tags >nul 2>&1
if errorlevel 1 (
    echo [INFO] Ollama nao esta rodando. Tentando iniciar...
    
    REM Tenta iniciar pelo caminho conhecido no computador do usuario
    if exist "C:\Users\afvs1\AppData\Local\Programs\Ollama\ollama.exe" (
        start "Ollama Server" /min cmd /c "C:\Users\afvs1\AppData\Local\Programs\Ollama\ollama.exe serve"
        echo [INFO] Ollama iniciado (C:\Users\afvs1\AppData\Local\Programs\Ollama\ollama.exe)
    ) else (
        REM Tenta iniciar pelo PATH (funciona em qualquer computador)
        where ollama >nul 2>&1
        if errorlevel 1 (
            echo [ERRO] Ollama nao encontrado!
            echo [ERRO] Instale o Ollama em: https://ollama.com
            echo [ERRO] Ou adicione o diretorio do Ollama ao PATH do sistema.
            pause
            exit /b 1
        ) else (
            start "Ollama Server" /min cmd /c "ollama serve"
            echo [INFO] Ollama iniciado (via PATH)
        )
    )
    
    echo [INFO] Aguardando Ollama iniciar (5 segundos)...
    timeout /t 5 /nobreak >nul
    
    REM Verifica novamente
    curl -s http://localhost:11434/api/tags >nul 2>&1
    if errorlevel 1 (
        echo [AVISO] Ollama pode nao estar pronto ainda. Continuando mesmo assim...
    ) else (
        echo [OK] Ollama esta respondendo.
    )
) else (
    echo [OK] Ollama ja esta rodando.
)
echo.

REM --- Iniciar Backend ---
echo [1/3] Iniciando Backend...
cd /d "%SCRIPT_DIR%\backend"

REM Verifica se existe venv, senao tenta python direto
if exist "venv\Scripts\python.exe" (
    set "PYTHON_CMD=venv\Scripts\python"
    echo [INFO] Usando Python do venv
) else (
    set "PYTHON_CMD=python"
    echo [INFO] Usando Python do sistema
)

start "Backend" cmd /k "%PYTHON_CMD% -m uvicorn app.main:app --reload --port 8000"
echo [OK] Backend iniciado em http://localhost:8000
echo.

REM --- Iniciar Frontend ---
echo [2/3] Iniciando Frontend...
cd /d "%SCRIPT_DIR%\frontend"

REM Adiciona Node.js local ao PATH (funciona neste projeto)
set "PATH=%SCRIPT_DIR%\nodejs;%PATH%"

REM Verifica se npm esta disponivel
REM npm --version >nul 2>&1
REM if errorlevel 1 (
REM    echo [ERRO] npm nao encontrado!
REM    echo [ERRO] Verifique se o Node.js esta em: %SCRIPT_DIR%\nodejs
REM    pause
REM    exit /b 1
REM )

start "Frontend" cmd /k "npm run dev"
echo [OK] Frontend iniciado em http://localhost:5173
echo.

echo ==========================================
echo  Aplicacao iniciada!
echo ==========================================
echo  Backend:  http://localhost:8000
echo  Frontend: http://localhost:5173
echo ==========================================
echo.
echo [DICA] Para parar, feche as janelas do Backend e Frontend.
pause
