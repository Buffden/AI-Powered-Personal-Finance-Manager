:: filepath: c:\Users\might\OneDrive\Desktop\School\AI-Powered-Personal-Finance-Manager\startup_script.bat
@echo off

:: Exit immediately if a command fails
setlocal enabledelayedexpansion

:: Activate virtual environment
echo Starting virtual environment...
call venv\Scripts\activate

:: Install requirements
echo Installing requirements...
pip install -r requirements.txt

:: Set PYTHONPATH to the project root
echo Setting PYTHONPATH...
set PYTHONPATH=%cd%

:: Start Flask backend in the background
echo Starting Flask backend...
start /B python -m backend.flask_app
set FLASK_PID=%!

:: Wait for Flask to start
echo Waiting for Flask backend to initialize...
timeout /t 5 >nul

:: Start Streamlit frontend
echo Starting Streamlit frontend...
streamlit run frontend/streamlit_app.py

:: Cleanup: Kill Flask process when Streamlit exits
echo Shutting down Flask backend...
taskkill /PID %FLASK_PID% /F