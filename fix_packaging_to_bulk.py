import os
import django
import sys

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kampala_pharma.settings')
django.setup()

from django.db.models import Q
from workflow.models import ProductionPhase, BatchPhaseExecution
from workflow.services import WorkflowService
from bmr.models import BMR

def fix_next_phase_notification():
    print("\n🔧 FIXING PACKAGING TO BULK PACKING WORKFLOW\n")
    
    # Get the latest batch executions where material release is completed
    material_release_completed = BatchPhaseExecution.objects.filter(
        phase__phase_name='packaging_material_release',
        status='completed'
    ).select_related('bmr', 'bmr__product', 'phase')
    
    print(f"Found {material_release_completed.count()} completed material releases")
    
    fixed_count = 0
    
    # Check each BMR to see if the next phase is correctly set
    for execution in material_release_completed:
        bmr = execution.bmr
        product = bmr.product
        
        if product.product_type == 'tablet' and getattr(product, 'tablet_type', None) == 'tablet_2':
            print(f"\nChecking BMR {bmr.bmr_number} for tablet type 2")
            
            # Find the bulk packing phase
            bulk_packing = BatchPhaseExecution.objects.filter(
                bmr=bmr,
                phase__phase_name='bulk_packing'
            ).first()
            
            # Find the secondary packing phase
            secondary_packing = BatchPhaseExecution.objects.filter(
                bmr=bmr,
                phase__phase_name='secondary_packaging'
            ).first()
            
            if bulk_packing and secondary_packing:
                print(f"Found bulk packing (status: {bulk_packing.status}) and secondary packing (status: {secondary_packing.status})")
                
                # Check if the phases are in the correct order
                if bulk_packing.phase.phase_order < secondary_packing.phase.phase_order:
                    print("✅ Phases are in correct order")
                else:
                    print("❌ Phase order is incorrect! Fixing...")
                    # Fix phase order
                    bulk_phase = bulk_packing.phase
                    secondary_phase = secondary_packing.phase
                    bulk_order = bulk_phase.phase_order
                    secondary_order = secondary_phase.phase_order
                    
                    bulk_phase.phase_order = min(bulk_order, secondary_order)
                    secondary_phase.phase_order = bulk_phase.phase_order + 1
                    bulk_phase.save()
                    secondary_phase.save()
                    print(f"✅ Fixed phase order: bulk packing ({bulk_phase.phase_order}), secondary packing ({secondary_phase.phase_order})")
                
                # Make sure bulk packing is activated after material release
                if execution.status == 'completed' and bulk_packing.status == 'not_ready':
                    print("Activating bulk packing after material release...")
                    bulk_packing.status = 'pending'
                    bulk_packing.save()
                    
                    # Make sure secondary packing is not pending yet
                    if secondary_packing.status == 'pending':
                        secondary_packing.status = 'not_ready'
                        secondary_packing.save()
                    
                    print("✅ Fixed phase activation: bulk packing is now pending")
                    fixed_count += 1
                
                # Check for incorrect status transitions
                if bulk_packing.status in ['not_ready', 'pending'] and secondary_packing.status == 'pending':
                    print("❌ Secondary packing activated before bulk packing! Fixing...")
                    secondary_packing.status = 'not_ready'
                    secondary_packing.save()
                    if bulk_packing.status == 'not_ready':
                        bulk_packing.status = 'pending'
                        bulk_packing.save()
                    print("✅ Fixed incorrect phase activation")
                    fixed_count += 1
    
    print(f"\n✨ Fixed {fixed_count} phase transition issues")
    
    # Fix notification messages
    update_notification_templates()
    
    # Fix pointer cursor issue for dropdown
    fix_dropdown_cursor()
    
    # Fix login issues
    fix_login_issues()

def update_notification_templates():
    print("\n🔧 FIXING NOTIFICATION MESSAGES\n")
    
    # Create a template in dashboards/templates/notifications/
    os.makedirs('dashboards/templates/notifications', exist_ok=True)
    
    notification_content = """{% load static %}

<!-- Notification Template -->
{% if notification %}
<div class="alert alert-{{ notification.type }} alert-dismissible fade show" role="alert">
    {% if notification.icon %}
    <i class="{{ notification.icon }} me-2"></i>
    {% endif %}
    <strong>{{ notification.title }}</strong>{% if notification.message %}: {{ notification.message }}{% endif %}
    {% if notification.next_phase %}
    <br><span class="small text-muted">Next phase: {{ notification.next_phase }}</span>
    {% endif %}
    <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
</div>
{% endif %}

<!-- Systematic Notification Generation -->
{% if bmr and completed_phase %}
<div class="alert alert-success alert-dismissible fade show" role="alert">
    <i class="fas fa-check-circle me-2"></i>
    <strong>Completed {{ completed_phase.phase.get_phase_name_display }} phase for BMR {{ bmr.bmr_number }}</strong>
    {% if next_phase %}
    <br><span class="small text-muted">Next phase: {{ next_phase.phase.get_phase_name_display }}</span>
    {% endif %}
    <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
</div>
{% endif %}
"""
    
    notification_path = 'dashboards/templates/notifications/phase_notification.html'
    with open(notification_path, 'w') as f:
        f.write(notification_content)
    
    print(f"✅ Created standardized notification template at {notification_path}")
    
    # Add to packaging dashboard view
    view_path = 'dashboards/views.py'
    
    with open(view_path, 'r') as f:
        view_content = f.read()
    
    # Add notification context to packaging_dashboard
    if 'def packaging_dashboard' in view_content:
        packaging_dashboard_start = view_content.find('def packaging_dashboard')
        render_start = view_content.find('return render(', packaging_dashboard_start)
        context_end = view_content.find(')', render_start)
        
        if packaging_dashboard_start > 0 and render_start > packaging_dashboard_start and context_end > render_start:
            # Add context variables for notifications
            context_part = view_content[render_start:context_end]
            if 'completed_phase' not in context_part and 'next_phase' not in context_part:
                # Get the indentation level
                indent = 4  # Default
                for i in range(render_start-1, 0, -1):
                    if view_content[i] == '\n':
                        indent = render_start - i - 1
                        break
                
                # Add get_next_phase logic before render
                next_phase_code = f"\n{' ' * indent}# Get next phase info for notification\n"
                next_phase_code += f"{' ' * indent}completed_phase = request.session.pop('completed_phase', None)\n"
                next_phase_code += f"{' ' * indent}bmr_id = request.session.pop('completed_bmr', None)\n"
                next_phase_code += f"{' ' * indent}bmr = None\n"
                next_phase_code += f"{' ' * indent}next_phase = None\n"
                next_phase_code += f"{' ' * indent}if bmr_id:\n"
                next_phase_code += f"{' ' * indent}    try:\n"
                next_phase_code += f"{' ' * indent}        bmr = BMR.objects.get(id=bmr_id)\n"
                next_phase_code += f"{' ' * indent}        # For tablet type 2, make sure bulk packing comes before secondary packing\n"
                next_phase_code += f"{' ' * indent}        if bmr.product.product_type == 'tablet' and getattr(bmr.product, 'tablet_type', None) == 'tablet_2':\n"
                next_phase_code += f"{' ' * indent}            # Check if material release was just completed\n"
                next_phase_code += f"{' ' * indent}            if completed_phase == 'packaging_material_release':\n"
                next_phase_code += f"{' ' * indent}                next_phase = BatchPhaseExecution.objects.filter(bmr=bmr, phase__phase_name='bulk_packing').first()\n"
                next_phase_code += f"{' ' * indent}        if not next_phase:\n"
                next_phase_code += f"{' ' * indent}            next_phase = WorkflowService.get_next_phase(bmr)\n"
                next_phase_code += f"{' ' * indent}    except BMR.DoesNotExist:\n"
                next_phase_code += f"{' ' * indent}        pass\n"
                
                view_content = view_content[:render_start] + next_phase_code + view_content[render_start:]
                
                # Update the context with notification variables
                context_end = view_content.find(')', render_start)
                if context_end > render_start and view_content[context_end-1] == '}':
                    # Add to existing context dictionary
                    view_content = view_content[:context_end-1] + ", 'completed_phase': completed_phase, 'bmr': bmr, 'next_phase': next_phase}" + view_content[context_end:]
                else:
                    # Create new context if none exists
                    view_content = view_content[:context_end] + ", {'completed_phase': completed_phase, 'bmr': bmr, 'next_phase': next_phase}" + view_content[context_end:]
                
                # Write updated view
                with open(view_path, 'w') as f:
                    f.write(view_content)
                
                print("✅ Added notification context to packaging_dashboard view")
    
    # Update the complete_phase method in services.py to store notification data
    services_path = 'workflow/services.py'
    
    with open(services_path, 'r') as f:
        services_content = f.read()
    
    # Add notification session data to complete_phase method
    if 'def complete_phase' in services_content:
        complete_phase_start = services_content.find('def complete_phase')
        method_end = services_content.find('return', complete_phase_start)
        
        if complete_phase_start > 0 and method_end > complete_phase_start:
            session_code = """            
            # Store notification data in session if available
            from django.contrib import messages
            if hasattr(completed_by, 'request') and hasattr(completed_by.request, 'session'):
                completed_by.request.session['completed_phase'] = phase_name
                completed_by.request.session['completed_bmr'] = bmr.id
                if next_phase:
                    next_phase_name = next_phase.phase.get_phase_name_display()
                    if bmr.product.product_type == 'tablet' and getattr(bmr.product, 'tablet_type', None) == 'tablet_2' and phase_name == 'packaging_material_release':
                        next_phase_name = 'Bulk Packing'  # Force correct next phase name
            """
            
            # Find a good insertion point
            insertion_point = services_content.find('return next_phase', complete_phase_start)
            if insertion_point > 0:
                # Insert before the return statement
                indent = 0
                for i in range(insertion_point-1, 0, -1):
                    if services_content[i] == '\n':
                        for j in range(i+1, insertion_point):
                            if services_content[j] == ' ':
                                indent += 1
                            else:
                                break
                        break
                
                # Apply proper indentation to the session code
                session_code = '\n'.join([' ' * indent + line for line in session_code.split('\n')])
                
                # Insert the code
                services_content = services_content[:insertion_point] + session_code + services_content[insertion_point:]
                
                # Write updated services
                with open(services_path, 'w') as f:
                    f.write(services_content)
                
                print("✅ Added notification session data to complete_phase method")
    
    # Update packaging store dashboard template
    template_path = 'templates/dashboards/packaging_dashboard.html'
    
    if os.path.exists(template_path):
        with open(template_path, 'r') as f:
            template_content = f.read()
        
        # Add notification include
        notification_include = "{% include 'notifications/phase_notification.html' %}"
        
        # Find a good place to insert the notification
        content_start = template_content.find('<div class="container')
        if content_start > 0:
            template_content = template_content[:content_start] + notification_include + "\n\n" + template_content[content_start:]
            
            # Write updated template
            with open(template_path, 'w') as f:
                f.write(template_content)
            
            print(f"✅ Added notification include to {template_path}")
    
    print("✅ Notification message fix completed")

def fix_dropdown_cursor():
    print("\n🔧 FIXING DROPDOWN CURSOR\n")
    
    # Update the base template CSS
    base_path = 'templates/dashboards/dashboard_base.html'
    
    if os.path.exists(base_path):
        with open(base_path, 'r') as f:
            base_content = f.read()
        
        # Add CSS for dropdown cursor
        dropdown_css = """
        /* Fix dropdown cursor */
        .dropdown-toggle {
            cursor: pointer !important;
        }
        .nav-link[data-bs-toggle="dropdown"] {
            cursor: pointer !important;
        }
        """
        
        # Find where to insert the CSS
        style_end = base_content.find('</style>')
        if style_end > 0:
            base_content = base_content[:style_end] + dropdown_css + base_content[style_end:]
            
            # Write updated base template
            with open(base_path, 'w') as f:
                f.write(base_content)
            
            print("✅ Added dropdown cursor CSS to base template")
    
    print("✅ Dropdown cursor fix completed")

def fix_login_issues():
    print("\n🔧 FIXING LOGIN ISSUES\n")
    
    # Check for login view
    from django.apps import apps
    if apps.is_installed('accounts'):
        accounts_path = 'accounts/views.py'
        if os.path.exists(accounts_path):
            with open(accounts_path, 'r') as f:
                accounts_content = f.read()
            
            # Check if there are session expiry settings
            if 'request.session.set_expiry' not in accounts_content:
                # Find the login view
                login_view_start = accounts_content.find('def login_view')
                login_success = accounts_content.find('login(request, user', login_view_start)
                
                if login_view_start > 0 and login_success > login_view_start:
                    # Get the indentation level
                    indent = 0
                    for i in range(login_success-1, 0, -1):
                        if accounts_content[i] == '\n':
                            for j in range(i+1, login_success):
                                if accounts_content[j] == ' ':
                                    indent += 1
                                else:
                                    break
                            break
                    
                    # Add session expiry setting after login
                    session_code = f"\n{' ' * indent}# Set session expiry to 12 hours (12 * 60 * 60 = 43200 seconds)\n"
                    session_code += f"{' ' * indent}request.session.set_expiry(43200)"
                    
                    # Find where to insert (after the login call)
                    insert_after = accounts_content.find(')', login_success)
                    if insert_after > login_success:
                        accounts_content = accounts_content[:insert_after+1] + session_code + accounts_content[insert_after+1:]
                        
                        # Write updated accounts view
                        with open(accounts_path, 'w') as f:
                            f.write(accounts_content)
                        
                        print("✅ Added session expiry setting to login view")
    
    # Create session timeout middleware if it doesn't exist
    middleware_dir = 'accounts/middleware'
    middleware_path = f'{middleware_dir}/session_timeout.py'
    
    os.makedirs(middleware_dir, exist_ok=True)
    
    if not os.path.exists(middleware_path):
        middleware_content = """import time
from django.conf import settings
from django.contrib import auth
from django.contrib.auth import logout
from django.utils.deprecation import MiddlewareMixin

class SessionTimeoutMiddleware(MiddlewareMixin):
    def process_request(self, request):
        # Skip for non-authenticated users
        if not request.user.is_authenticated:
            return None
            
        # Skip for AJAX requests
        if request.META.get('HTTP_X_REQUESTED_WITH') == 'XMLHttpRequest':
            return None
        
        # Get current time and last activity time
        current_time = time.time()
        last_activity = request.session.get('last_activity')
        
        # Set default session timeout (12 hours = 43200 seconds)
        session_timeout = getattr(settings, 'SESSION_TIMEOUT', 43200)
        
        # Update last activity time
        request.session['last_activity'] = current_time
        
        # If no last activity or session expired, ignore
        if not last_activity:
            return None
            
        # Check if session has expired
        if current_time - last_activity > session_timeout:
            # Logout user and display message
            auth.logout(request)
            # Let the logout view handle the redirect
            
        return None
"""
        
        with open(middleware_path, 'w') as f:
            f.write(middleware_content)
        
        # Create __init__.py file
        init_path = f'{middleware_dir}/__init__.py'
        if not os.path.exists(init_path):
            with open(init_path, 'w') as f:
                f.write('')
        
        print(f"✅ Created session timeout middleware at {middleware_path}")
    
    # Add middleware to settings if needed
    settings_path = 'kampala_pharma/settings.py'
    if os.path.exists(settings_path):
        with open(settings_path, 'r') as f:
            settings_content = f.read()
        
        # Check if middleware is already added
        if 'accounts.middleware.session_timeout.SessionTimeoutMiddleware' not in settings_content:
            # Find middleware section
            middleware_start = settings_content.find('MIDDLEWARE = [')
            if middleware_start > 0:
                middleware_end = settings_content.find(']', middleware_start)
                if middleware_end > middleware_start:
                    # Add our middleware
                    middleware_list = settings_content[middleware_start:middleware_end].strip()
                    last_line = middleware_list.rfind('\n')
                    indent = 0
                    for i in range(last_line+1, len(middleware_list)):
                        if middleware_list[i] == ' ':
                            indent += 1
                        else:
                            break
                    
                    # Add our middleware with proper indentation
                    new_middleware = f"\n{' ' * indent}'accounts.middleware.session_timeout.SessionTimeoutMiddleware',"
                    settings_content = settings_content[:middleware_end] + new_middleware + settings_content[middleware_end:]
                    
                    # Add session timeout setting
                    timeout_setting = "\n# Session timeout setting (12 hours = 43200 seconds)\nSESSION_TIMEOUT = 43200\n"
                    settings_content += timeout_setting
                    
                    # Write updated settings
                    with open(settings_path, 'w') as f:
                        f.write(settings_content)
                    
                    print("✅ Added session timeout middleware to settings")
    
    print("✅ Login issues fix completed")

if __name__ == "__main__":
    fix_next_phase_notification()
