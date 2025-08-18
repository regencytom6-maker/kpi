# Deployment Guide for KPI System on PythonAnywhere

This guide will walk you through deploying the Kampala Pharmaceutical Industries Operations System on PythonAnywhere's free tier for testing.

## Prerequisites

- A PythonAnywhere account (free tier is sufficient for testing)
- Your code pushed to a GitHub repository (which you've already done with kiizajudith/kpi)

## Step 1: Create a PythonAnywhere Account

1. Go to https://www.pythonanywhere.com/ and sign up for a free account
2. Verify your email and log in

## Step 2: Set Up a Web App

1. In your PythonAnywhere dashboard, click on the "Web" tab
2. Click on "Add a new web app"
3. Choose the "Manual configuration" option (not the Django option)
4. Select Python 3.10 (or the closest version to your local environment)
5. Click through to create the app

## Step 3: Clone Your Repository

1. Click on the "Consoles" tab
2. Start a new Bash console
3. Clone your repository with:
   ```bash
   git clone https://github.com/kiizajudith/kpi.git
   ```
4. Navigate to your project:
   ```bash
   cd kpi
   ```

## Step 4: Set Up a Virtual Environment

1. Create a virtual environment:
   ```bash
   python -m venv venv
   ```
2. Activate it:
   ```bash
   source venv/bin/activate
   ```
3. Install your requirements:
   ```bash
   pip install -r requirements.txt
   ```
4. Additionally, install:
   ```bash
   pip install mysqlclient
   ```

## Step 5: Configure Your Django Settings

Create a production settings file or update your existing one with:

1. Set `DEBUG = False`
2. Update `ALLOWED_HOSTS` to include your PythonAnywhere domain: 
   ```python
   ALLOWED_HOSTS = ['yourusername.pythonanywhere.com']
   ```
3. Configure database (PythonAnywhere provides MySQL):
   ```python
   DATABASES = {
       'default': {
           'ENGINE': 'django.db.backends.mysql',
           'NAME': 'yourusername$kpi',
           'USER': 'yourusername',
           'PASSWORD': 'your-database-password',
           'HOST': 'yourusername.mysql.pythonanywhere-services.com',
           'PORT': '3306',
       }
   }
   ```

## Step 6: Configure WSGI File

1. Go to the "Web" tab
2. Click on the WSGI configuration file link (e.g., `/var/www/yourusername_pythonanywhere_com_wsgi.py`)
3. Replace the content with:

```python
import os
import sys

# Add your project directory to the sys.path
path = '/home/yourusername/kpi'
if path not in sys.path:
    sys.path.insert(0, path)

# Set environment variable for Django settings module
os.environ['DJANGO_SETTINGS_MODULE'] = 'kampala_pharma.settings'

# Import Django's WSGI handler
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
```

4. Save the file

## Step 7: Set Up Static Files

1. In the "Web" tab, under "Static files":
2. Add an entry:
   - URL: `/static/`
   - Directory: `/home/yourusername/kpi/static/`
3. Add another entry for media:
   - URL: `/media/`
   - Directory: `/home/yourusername/kpi/media/`

## Step 8: Create and Configure Database

1. Go to the "Databases" tab
2. Set a password for your MySQL database
3. Create a new database named `yourusername$kpi`
4. In the Bash console, run migrations:
   ```bash
   python manage.py migrate
   ```
5. Create a superuser:
   ```bash
   python manage.py createsuperuser
   ```

## Step 9: Collect Static Files

Run in the Bash console:
```bash
python manage.py collectstatic
```

## Step 10: Reload Your Web App

1. Go back to the "Web" tab
2. Click the "Reload" button

## Step 11: Access Your Application

Your application should now be available at:
`https://yourusername.pythonanywhere.com`

## Troubleshooting

- If you encounter errors, check the error logs in the "Web" tab
- Make sure all paths in the WSGI file match your actual directory structure
- Verify your database settings match the MySQL database you created
- Ensure all required packages are installed in your virtual environment

## Notes for the Free Tier

- Free tier has limitations on CPU usage and database size
- Your application will sleep after periods of inactivity
- You'll need to confirm your app every three months to keep it running

Remember to replace `yourusername` with your actual PythonAnywhere username throughout this guide.
