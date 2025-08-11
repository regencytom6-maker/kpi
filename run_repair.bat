@echo off
echo Running coating workflow repair script...
pharma_env\Scripts\python.exe manage.py shell < repair_coating_workflow.py
echo Done
pause
