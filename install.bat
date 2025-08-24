@echo off
setlocal enabledelayedexpansion

echo 🚀 Kompan Installation Script for Windows
echo ==========================================

:: Check if Docker is installed
docker --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Docker is not installed. Please install Docker Desktop first.
    echo Visit: https://docs.docker.com/desktop/windows/
    pause
    exit /b 1
)

:: Check if Docker daemon is running
docker info >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Docker daemon is not running. Please start Docker Desktop.
    pause
    exit /b 1
)

echo ✅ System requirements met

:: Setup directories
echo 📁 Setting up directories...
set INSTALL_DIR=%USERPROFILE%\kompan
if not exist "%INSTALL_DIR%" mkdir "%INSTALL_DIR%"
if not exist "%INSTALL_DIR%\data" mkdir "%INSTALL_DIR%\data"
if not exist "%INSTALL_DIR%\config" mkdir "%INSTALL_DIR%\config"

:: Create config if it doesn't exist
if not exist "%INSTALL_DIR%\config\settings.json" (
    echo ⚙️  Creating default configuration...
    (
        echo {
        echo   "scanning_interval": 2.0,
        echo   "tts_engine": "auto",
        echo   "language": "pl",
        echo   "api_timeout": 10,
        echo   "conversation_history_days": 30,
        echo   "claude_api_key": "",
        echo   "gui_port": 8080,
        echo   "api_port": 8081,
        echo   "audio_device": "default"
        echo }
    ) > "%INSTALL_DIR%\config\settings.json"
)

:: Build Docker image
echo 🔨 Building Docker image...
docker build -t kompan:latest .
if %errorlevel% neq 0 (
    echo ❌ Failed to build Docker image
    pause
    exit /b 1
)

echo ✅ Docker image built successfully

:: Create startup script
echo 📝 Creating startup script...
(
    echo @echo off
    echo.
    echo :: Stop existing container if running
    echo docker stop kompan 2^>nul
    echo docker rm kompan 2^>nul
    echo.
    echo :: Start new container
    echo docker run -d ^^^
    echo   --name kompan ^^^
    echo   -p 8080:8080 ^^^
    echo   -p 8081:8081 ^^^
    echo   -v "%USERPROFILE%\kompan\data:/app/data" ^^^
    echo   -v "%USERPROFILE%\kompan\config:/app/config" ^^^
    echo   --restart unless-stopped ^^^
    echo   kompan:latest
    echo.
    echo echo 🚀 Kompan started successfully!
    echo echo 📱 Open http://localhost:8080 in your browser
    echo echo 🔧 API available at http://localhost:8081
    echo.
    echo :: Try to open browser automatically
    echo timeout /t 3 /nobreak ^>nul
    echo start http://localhost:8080
) > "%INSTALL_DIR%\start-kompan.bat"

:: Create stop script
(
    echo @echo off
    echo echo 🛑 Stopping Kompan...
    echo docker stop kompan 2^>nul ^|^| echo Kompan was not running
    echo docker rm kompan 2^>nul
    echo echo ✅ Kompan stopped
    echo pause
) > "%INSTALL_DIR%\stop-kompan.bat"

:: Create logs script
(
    echo @echo off
    echo echo 📋 Kompan logs ^(press Ctrl+C to exit^):
    echo docker logs -f kompan
) > "%INSTALL_DIR%\logs-kompan.bat"

echo.
echo 🎉 Kompan installation completed successfully!
echo.
echo 📍 Installation directory: %INSTALL_DIR%
echo 🚀 To start: %INSTALL_DIR%\start-kompan.bat
echo 🛑 To stop:  %INSTALL_DIR%\stop-kompan.bat
echo 📋 To view logs: %INSTALL_DIR%\logs-kompan.bat
echo.
echo ⚙️  Configuration file: %INSTALL_DIR%\config\settings.json
echo 📁 Conversation data: %INSTALL_DIR%\data\
echo.
echo 🔑 To use Claude AI features:
echo    1. Get an API key from https://console.anthropic.com/
echo    2. Edit %INSTALL_DIR%\config\settings.json
echo    3. Set 'claude_api_key' to your API key
echo    4. Restart using stop and start scripts
echo.
echo 🌐 Ready to start? Run: %INSTALL_DIR%\start-kompan.bat
pause