@echo off
echo Activating Kampala Pharmaceutical Industries virtual environment...
call pharma_env\Scripts\activate.bat
echo.
echo Virtual environment activated! You can now use:
echo   python manage.py runserver
echo   python manage.py migrate
echo   python manage.py createsuperuser
echo.
cmd /k
