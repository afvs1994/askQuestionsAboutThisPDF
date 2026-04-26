@echo off
chcp 65001 >nul 2>&1
echo ==========================================
echo  Iniciando Frontend
echo ==========================================
echo.

REM Detecta o diretório onde este script está localizado
set "SCRIPT_DIR=%~dp0"
set "SCRIPT_DIR=%SCRIPT_DIR:~0,-1%"

REM Adiciona Node.js local ao PATH
set "PATH=%SCRIPT_DIR%\nodejs;%PATH%"

cd /d "%SCRIPT_DIR%\frontend"

REM Verifica se npm está disponível
npm --version >nul 2>&1
if errorlevel 1 (
    echo [ERRO] npm não encontrado!
    echo [ERRO] Verifique se o Node.js está em: %SCRIPT_DIR%\nodejs
    pause
    exit /b 1
)

echo [INFO] Iniciando servidor de desenvolvimento...
npm run dev

pause

