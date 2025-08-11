import os
import django
import sys

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kampala_pharma.settings')
django.setup()

def fix_admin_dashboard_url():
    print("\n🔧 FIXING ADMIN DASHBOARD URL\n")
    
    # The correct URL for the admin dashboard based on urls.py
    # The pattern is dashboard/admin-overview/ (NOT dashboards/admin/)
    correct_url = '/dashboard/admin-overview/'
    
    # Create a verification page that will redirect to the correct URL
    verification_content = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Admin Dashboard Redirect</title>
    <script>
        // Redirect to the correct admin dashboard URL
        window.location.href = '""" + correct_url + """';
    </script>
    <style>
        body {
            font-family: Arial, sans-serif;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            height: 100vh;
            margin: 0;
            background-color: #f8f9fa;
        }
        .redirect-message {
            background-color: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
            text-align: center;
            max-width: 500px;
        }
        h1 {
            color: #0056b3;
            margin-bottom: 20px;
        }
        p {
            margin-bottom: 15px;
            color: #333;
        }
        a {
            display: inline-block;
            background-color: #0056b3;
            color: white;
            padding: 10px 20px;
            text-decoration: none;
            border-radius: 5px;
            font-weight: bold;
            margin-top: 15px;
        }
        a:hover {
            background-color: #003d7f;
        }
    </style>
</head>
<body>
    <div class="redirect-message">
        <h1>Redirecting to Admin Dashboard</h1>
        <p>The URL has changed. You are being redirected to the correct admin dashboard URL.</p>
        <p>If you are not redirected automatically, click the button below:</p>
        <a href=\"""" + correct_url + """\">Go to Admin Dashboard</a>
    </div>
</body>
</html>
    """
    
    # Create a directory for the verification page if it doesn't exist
    os.makedirs('templates/dashboards/admin', exist_ok=True)
    
    # Write the verification page
    with open('templates/dashboards/admin/index.html', 'w') as f:
        f.write(verification_content)
    
    print("✅ Created redirect page for old admin dashboard URL")
    
    # Update the Django URLs to handle the old URL pattern
    urls_py_path = 'dashboards/urls.py'
    
    with open(urls_py_path, 'r') as f:
        urls_content = f.read()
    
    # Check if we already have a redirect URL
    if "path('admin/', views.admin_redirect" not in urls_content:
        # Add the redirect view import
        if "from django.views.generic.base import RedirectView" not in urls_content:
            urls_content = urls_content.replace("from . import views", "from . import views\nfrom django.views.generic.base import RedirectView")
            print("✅ Added RedirectView import")
        
        # Add the redirect URL pattern before the admin-overview path
        admin_overview_line = "path('admin-overview/', views.admin_dashboard, name='admin_dashboard'),"
        if admin_overview_line in urls_content:
            redirect_line = "    # Redirect for old URL pattern\n    path('admin/', views.admin_redirect, name='admin_redirect'),\n    "
            urls_content = urls_content.replace(admin_overview_line, redirect_line + admin_overview_line)
            print("✅ Added redirect URL pattern")
        
        with open(urls_py_path, 'w') as f:
            f.write(urls_content)
    else:
        print("✅ Redirect URL pattern already exists")
    
    # Create or update the redirect view
    views_py_path = 'dashboards/views.py'
    
    with open(views_py_path, 'r') as f:
        views_content = f.read()
    
    # Add the redirect view if it doesn't exist
    if "def admin_redirect(request):" not in views_content:
        redirect_view = """
# Redirect view for old admin dashboard URL
def admin_redirect(request):
    # Render the redirect template that will handle the client-side redirect
    return render(request, 'dashboards/admin/index.html')
"""
        # Add the view at the end of the file
        views_content += "\n" + redirect_view
        
        with open(views_py_path, 'w') as f:
            f.write(views_content)
        
        print("✅ Added admin_redirect view")
    else:
        print("✅ admin_redirect view already exists")
    
    print("\n✨ URL FIX APPLIED")
    print("1. Created a redirect from /dashboard/admin/ to /dashboard/admin-overview/")
    print("2. The admin dashboard can now be accessed at EITHER URL")
    print("3. Please update any bookmarks to use the correct URL")
    
    print("\n🌐 CORRECT ADMIN DASHBOARD URLs:")
    print("- http://localhost:8000/dashboard/admin-overview/")
    print("- http://localhost:8000/dashboard/admin/ (will redirect)")

if __name__ == "__main__":
    fix_admin_dashboard_url()
