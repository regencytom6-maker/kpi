"""
Helper script to prepare files for Git repository
This lists important project files that should be committed,
and identifies development/temporary files that should be excluded
"""

import os
import fnmatch
import re
from pathlib import Path

def should_include_file(file_path):
    """Check if file should be included in Git repository"""
    # Skip virtual environment
    if 'pharma_env' in file_path:
        return False
        
    # Skip common development patterns
    exclude_patterns = [
        '*.pyc', '__pycache__', '*.log', 'db.sqlite3',
        'debug_*.py', 'fix_*.py', 'test_*.py', '*_test.py',
        'comprehensive_*.py', 'emergency_*.py', 'analyze_*.py',
        'check_*.py', 'create_test_*.py', '*_debug.py',
        '*_IMPLEMENTATION.md', '*_GUIDE.md', '*_DOCUMENTATION.md',
        '*_SUMMARY.md', 'WORKFLOW_*.md', 'DASHBOARD_*.md',
        'chart_debugger.html', '.vscode', '.idea'
    ]
    
    for pattern in exclude_patterns:
        if fnmatch.fnmatch(file_path, pattern):
            return False
            
    return True

def list_important_files():
    """List important project files to be included in Git"""
    important_files = []
    
    # Key project directories to focus on
    core_dirs = ['core', 'pharma', 'templates', 'static', 'media']
    
    for root, dirs, files in os.walk('.'):
        # Skip .git directory if it exists
        if '.git' in root:
            continue
            
        # Normalize path
        root = root[2:] if root.startswith('./') else root
        if root == '':
            root = '.'
            
        # Process files
        for file in files:
            file_path = os.path.join(root, file)
            if should_include_file(file_path):
                important_files.append(file_path)
    
    return important_files

def group_by_type(files):
    """Group files by their types"""
    by_type = {}
    
    for file in files:
        # Get file extension
        ext = os.path.splitext(file)[1].lower()
        
        # Group by common types
        if ext == '.py' and 'migrations' in file:
            file_type = 'Migrations'
        elif ext == '.py' and any(p in file for p in ['models.py', 'views.py', 'urls.py', 'admin.py']):
            file_type = 'Core Django Files'
        elif ext == '.py':
            file_type = 'Python Files'
        elif ext in ['.html', '.htm']:
            file_type = 'Templates'
        elif ext in ['.css', '.js']:
            file_type = 'Static Files'
        elif ext in ['.md', '.txt', '.rst']:
            file_type = 'Documentation'
        elif ext in ['.png', '.jpg', '.jpeg', '.gif', '.svg']:
            file_type = 'Images'
        elif ext in ['.json', '.yml', '.yaml']:
            file_type = 'Configuration'
        else:
            file_type = f'Other ({ext})'
            
        by_type.setdefault(file_type, []).append(file)
    
    return by_type

def main():
    print("Important files to include in Git repository:")
    print("="*80)
    
    important_files = list_important_files()
    grouped_files = group_by_type(important_files)
    
    # Print summary by type
    for file_type, files in sorted(grouped_files.items()):
        print(f"\n{file_type} ({len(files)}):")
        for file in sorted(files)[:15]:  # Show first 15 of each type
            print(f"  {file}")
        if len(files) > 15:
            print(f"  ... and {len(files) - 15} more")
    
    print("\nTotal files to be included:", len(important_files))
    
    # Print important directories
    print("\nKey project directories:")
    core_dirs = [d for d in os.listdir('.') if os.path.isdir(d) 
                and not d.startswith('.') 
                and not d in ['pharma_env', 'env', 'venv', '.git']]
    for d in sorted(core_dirs):
        print(f"  {d}/")

if __name__ == "__main__":
    main()
