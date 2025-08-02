#!/usr/bin/env python
import os
import sys
import django

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kampala_pharma.settings')
django.setup()

from django.contrib.sessions.models import Session

def clear_sessions():
    """Clear all sessions to fix CSRF issues"""
    count = Session.objects.count()
    Session.objects.all().delete()
    print(f"Cleared {count} sessions")
    print("Please restart the Django server and try again")

if __name__ == '__main__':
    clear_sessions()
