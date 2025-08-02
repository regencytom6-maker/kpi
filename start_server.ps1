# Kampala Pharmaceutical Industries - Server Startup Script
Write-Host "Starting Kampala Pharmaceutical Industries Operations System..." -ForegroundColor Green
Write-Host "Using virtual environment..." -ForegroundColor Yellow

# Run the Django server
& "pharma_env\Scripts\python.exe" manage.py runserver 8000

Write-Host "Server stopped." -ForegroundColor Red
Read-Host "Press Enter to exit"
