@echo off
echo ========================================================
echo   SENTINELS // Self-Healing Netflix-Clone Ecosystem
echo ========================================================
echo.
echo Stopping any existing demo containers...
docker rm -f patient_app dashboard_app patient_netflix sentinel_dashboard sentinel_healer >nul 2>&1

echo.
echo Building and Orchestrating the Sentinels Microservices...
docker-compose up -d --build

echo.
echo ========================================================
echo.
echo [1] COMPONENT: Netflix Clone is running at:
echo     http://localhost:5000/
echo.
echo [2] COMPONENT: Cyberpunk Dashboard is running at:
echo     http://localhost:8080/
echo.
echo [3] COMPONENT: AI Healer Agent is actively monitoring.
echo.
echo You can view the Live Logs of the Healer by running:
echo     docker logs -f sentinel_healer
echo.
echo ========================================================
echo Hit ENTER to exit this setup script.
pause >nul
