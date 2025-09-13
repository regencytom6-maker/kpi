# Tablet QC Rollback Fix and Git Workflow

This document outlines the permanent fix for the tablet QC rollback issue and the correct Git workflow to deploy it to your server.

## Step 1: Fix the Code Locally

Let's make sure your local code has the correct tablet QC rollback functionality. Our analysis shows that the code in your repository should be working correctly, but the server might be running an older version.

The key files involved are:
- `workflow/services.py` - Contains the `handle_qc_failure_rollback` method
- `bmr/views.py` - Contains the QC failure handling that calls the rollback

## Step 2: Commit and Push Changes

Once you've verified the code is correct locally, push it to your repository:

```bash
# Navigate to your project directory
cd C:\Users\KPI-DvOps\Desktop\New folder\new system

# Add all changes
git add .

# Commit with a descriptive message
git commit -m "Fix tablet QC rollback functionality"

# Push to the repository
git push origin master
```

## Step 3: Pull Changes on the Server

Now on your server, pull the latest changes:

```bash
# Navigate to your project directory on the server
cd C:\Users\Administrator\kpi

# Pull the latest changes
git pull origin master
```

## Step 4: Restart Your Application

After pulling the changes, restart your Django application:

```bash
# If using waitress
python run_server.py
```

## Why This Approach is Better

1. **Proper Development Workflow**: This follows the standard git-based development workflow
2. **Version Control**: All changes are tracked in git
3. **Consistency**: Ensures all environments use the same code
4. **Rollback Capability**: If something goes wrong, you can easily roll back to a previous version

## Creating a Simple Update Script for the Server

You can create a simple batch file on your server to make updates easier:

```batch
@echo off
echo ========== KPI Server Update Script ==========
cd C:\Users\Administrator\kpi
echo Pulling latest changes from git...
git pull origin master
echo.
echo Update complete. Restarting application...
python run_server.py
```

Save this as `update_kpi.bat` on your server and run it whenever you push changes to the repository.