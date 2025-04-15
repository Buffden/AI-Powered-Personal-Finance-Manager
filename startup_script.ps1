& .\venv\Scripts\Activate.ps1

pip install -r requirements.txt

$env:PYTHONPATH = (Get-Location).Path

$flaskProcess = Start-Process -FilePath "python" -ArgumentList "backend\flask_app.py" -PassThru

Start-Sleep -Seconds 5

try {
    Start-Process -FilePath "streamlit" -ArgumentList "run frontend\streamlit_app.py" -Wait
} finally {
    Stop-Process -Id $flaskProcess.Id -Force
}