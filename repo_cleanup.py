#!/usr/bin/env python3
"""
Repository Cleanup Script
Removes development files from the main branch while preserving them in a development branch
"""

import os
import shutil
import subprocess
from pathlib import Path

def run_git_command(command):
    """Run a git command and return the result"""
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"Git command failed: {command}")
        print(f"Error: {e.stderr}")
        return None

def backup_to_dev_branch():
    """Create a development branch with all current files before cleanup"""
    print("Creating development branch backup...")
    
    # Create and switch to development branch
    run_git_command("git checkout -b development")
    run_git_command("git add .")
    run_git_command('git commit -m "Backup all development files to development branch"')
    
    # Switch back to main
    run_git_command("git checkout main")
    print("Development branch created with backup")

def should_remove_file(file_path):
    """Determine if a file should be removed from production"""
    file_name = os.path.basename(file_path)
    
    # Remove test/debug/fix files
    if any(file_name.startswith(prefix) for prefix in [
        'test_', 'debug_', 'fix_', 'verify_', 'check_', 'analyze_',
        'create_test_', 'cleanup_', 'emergency_', 'final_', 'quick_',
        'simple_', 'setup_', 'update_', 'populate_', 'generate_',
        'integrate_', 'remove_', 'restore_', 'repair_', 'comprehensive_',
        'permanent_', 'unblock_', 'show_users', 'clear_sessions'
    ]):
        return True
    
    # Remove batch scripts
    if file_name.endswith(('.bat', '.ps1')) and file_name not in ['manage.py']:
        return True
    
    # Remove development documentation
    if file_name.endswith('.md') and any(keyword in file_name.upper() for keyword in [
        'IMPLEMENTATION', 'SUMMARY', 'GUIDE', 'INSTRUCTIONS', 'ANALYSIS',
        'DOCUMENTATION', 'RESOLVED', 'FIXED', 'GUARANTEE', 'TESTING',
        'DEPLOYMENT', 'WORKFLOW_', 'DASHBOARD_', 'BULK_', 'ENHANCED_',
        'ROLE_', 'REPORTS_', 'MACHINES_', 'PACKAGING_', 'MIGRATION_',
        'VISUAL_DIAGRAMS', 'CLEANUP_', 'CLEAN_STRUCTURE'
    ]):
        return True
    
    # Remove development artifacts
    if file_name in [
        'template_debug.log', 'chart_debugger.html', 'rendered_template.html',
        'ERD_Diagram.html', 'batch_analysis.txt', 'batch_analysis_result.txt'
    ]:
        return True
    
    return False

def cleanup_repository():
    """Remove development files from the repository"""
    print("Starting repository cleanup...")
    
    root_dir = Path(".")
    files_to_remove = []
    
    # Scan for files to remove
    for file_path in root_dir.iterdir():
        if file_path.is_file() and should_remove_file(file_path):
            files_to_remove.append(file_path)
    
    # Remove development directories
    dev_dirs = ['backups', '__pycache__']
    for dir_name in dev_dirs:
        dir_path = root_dir / dir_name
        if dir_path.exists():
            files_to_remove.append(dir_path)
    
    print(f"Found {len(files_to_remove)} files/directories to remove:")
    for file_path in files_to_remove[:10]:  # Show first 10
        print(f"  - {file_path}")
    if len(files_to_remove) > 10:
        print(f"  ... and {len(files_to_remove) - 10} more")
    
    # Confirm before proceeding
    response = input("\nProceed with cleanup? (y/N): ")
    if response.lower() != 'y':
        print("Cleanup cancelled")
        return
    
    # Remove files
    for file_path in files_to_remove:
        try:
            if file_path.is_file():
                file_path.unlink()
                print(f"Removed file: {file_path}")
            elif file_path.is_dir():
                shutil.rmtree(file_path)
                print(f"Removed directory: {file_path}")
        except Exception as e:
            print(f"Error removing {file_path}: {e}")
    
    print(f"\nCleanup complete! Removed {len(files_to_remove)} items")

def main():
    """Main cleanup process"""
    print("Repository Cleanup Tool")
    print("=" * 50)
    
    # Check if we're in a git repository
    if not os.path.exists('.git'):
        print("Error: Not in a git repository")
        return
    
    # Step 1: Backup to development branch
    backup_to_dev_branch()
    
    # Step 2: Clean up main branch
    cleanup_repository()
    
    # Step 3: Commit changes
    print("\nCommitting cleanup changes...")
    run_git_command("git add .")
    run_git_command('git commit -m "Clean up repository: remove development files"')
    
    print("\nRepository cleanup complete!")
    print("- Development files backed up to 'development' branch")
    print("- Main branch cleaned for production")
    print("- .gitignore added to prevent future clutter")

if __name__ == "__main__":
    main()
