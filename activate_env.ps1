# Kampala Pharmaceutical Industries - Environment Activation
Write-Host "Activating virtual environment..." -ForegroundColor Green

# Set execution policy if needed
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser -Force

# Activate virtual environment
& "pharma_env\Scripts\Activate.ps1"

Write-Host ""
Write-Host "Virtual environment activated!" -ForegroundColor Green
Write-Host "You can now use:" -ForegroundColor Yellow
Write-Host "  python manage.py runserver" -ForegroundColor Cyan
Write-Host "  python manage.py migrate" -ForegroundColor Cyan
Write-Host "  python manage.py createsuperuser" -ForegroundColor Cyan
Write-Host ""
