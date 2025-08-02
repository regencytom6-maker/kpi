# Running the Kampala Pharmaceutical Industries Operations System

## Quick Start Guide

### Method 1: Using Virtual Environment (Recommended)

1. **Open Command Prompt or PowerShell**
2. **Navigate to project directory:**
   ```cmd
   cd "C:\Users\Ronald\Desktop\new system"
   ```

3. **Run the server using virtual environment:**
   ```cmd
   pharma_env\Scripts\python.exe manage.py runserver
   ```

4. **Access the system:**
   - Admin Panel: http://127.0.0.1:8000/admin/
   - BMR Creation: http://127.0.0.1:8000/bmr/create/

### Method 2: Using Batch File

1. **Double-click** `start_server.bat` in the project folder
2. **Wait** for the server to start
3. **Open browser** to http://127.0.0.1:8000/admin/

### Method 3: Using PowerShell Script

1. **Right-click** `start_server.ps1` → Run with PowerShell
2. **If execution policy error**, run this first:
   ```powershell
   Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
   ```

## Login Credentials

### Admin User
- **Username:** admin
- **Password:** admin123
- **Role:** System Administrator

### QA Officer
- **Username:** qa_officer
- **Password:** qa123
- **Role:** Quality Assurance

## System Features

### 1. Admin Dashboard
- **URL:** http://127.0.0.1:8000/admin/
- **Manage:** Users, Products, BMRs, Workflow phases
- **Access:** Full system administration

### 2. BMR Creation (QA)
- **URL:** http://127.0.0.1:8000/bmr/create/
- **Feature:** Manual batch number entry
- **Format:** XXXYYYY (e.g., 0012025)
- **Auto-populate:** Product details on selection

### 3. Sample Data Available
- **Products:** Paracetamol 500mg Tablets, Diclofenac Gel 1%
- **Users:** Admin, QA Officer
- **Workflow:** All production phases configured

## Troubleshooting

### Error: "No module named 'rest_framework'"
**Solution:** Always use virtual environment:
```cmd
pharma_env\Scripts\python.exe manage.py runserver
```

### Error: "Permission denied"
**Solution:** Run as administrator or change to project directory

### Error: "Port already in use"
**Solution:** Use different port:
```cmd
pharma_env\Scripts\python.exe manage.py runserver 8080
```

### Error: "ModuleNotFoundError"
**Solution:** Install missing packages:
```cmd
pharma_env\Scripts\python.exe -m pip install -r requirements.txt
```

## Development Notes

- **Database:** SQLite (db.sqlite3)
- **Static Files:** Served automatically in development
- **Debug Mode:** Enabled (DEBUG=True)
- **Time Zone:** Africa/Kampala

## Next Steps

1. **Login** as admin or QA officer
2. **Create products** if needed
3. **Create BMRs** with manual batch numbers
4. **Test workflow** phases
5. **Add more users** with different roles

## Support

For technical issues or questions about the pharmaceutical workflow system, refer to the README.md file or check the Django admin interface for detailed configuration options.

---
**Kampala Pharmaceutical Industries Operations Department**
