@echo off
echo ==========================================
echo  Iniciando Private Document RAG API
echo ==========================================
echo.

REM Verificar se Ollama está rodando
curl -s http://localhost:11434/api/tags >nul 2>&1
if errorlevel 1 (
    echo [AVISO] Ollama nao esta rodando!
    echo [AVISO] Instale o Ollama em: https://ollama.com
    echo [AVISO] E execute: ollama run llama3.1
    echo.
    pause
    exit /b 1
)

echo [1/2] Iniciando Backend...
cd /d c:\Users\afvs1\askQuestionsAboutThisPDF\backend
start "Backend" cmd /k "venv\Scripts\python -m uvicorn app.main:app --reload --port 8000"

echo [2/2] Iniciando Frontend...
cd /d c:\Users\afvs1\askQuestionsAboutThisPDF\frontend
set PATH=c:\Users\afvs1\askQuestionsAboutThisPDF\nodejs;%%PATH%%
start "Frontend" cmd /k "npm run dev"

echo.
echo ==========================================
echo  Aplicacao iniciada!
echo ==========================================
echo  Backend:  http://localhost:8000
echo  Frontend: http://localhost:5173
echo ==========================================
pause

