"""
This script lists all files that match the patterns in .gitignore
It helps identify which files would be excluded from the Git repository
"""

import os
import fnmatch
import re
from pathlib import Path

def get_gitignore_patterns():
    """Read patterns from .gitignore file"""
    patterns = []
    with open('.gitignore', 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#'):
                patterns.append(line)
    return patterns

def matches_any_pattern(file_path, patterns):
    """Check if file matches any gitignore pattern"""
    normalized_path = file_path.replace('\\', '/')
    
    for pattern in patterns:
        # Handle comment lines and empty lines
        if not pattern or pattern.startswith('#'):
            continue
            
        # Handle negation pattern (patterns that start with !)
        if pattern.startswith('!'):
            continue  # We'll skip these for simplicity
            
        # Handle directory-only patterns (ending with /)
        if pattern.endswith('/'):
            if not os.path.isdir(file_path):
                continue
            pattern = pattern[:-1]
            
        # Special case for patterns with * and **
        if '*' in pattern:
            # Convert the pattern to a regex that will match properly
            if '**' in pattern:
                # Handle ** pattern (matches across directories)
                regex_pattern = pattern.replace('**', '.*')
            else:
                # Handle * pattern (doesn't match across directories)
                regex_pattern = pattern.replace('*', '[^/]*')
                
            # Convert other glob syntax and anchor appropriately
            regex_pattern = regex_pattern.replace('.', '\\.').replace('?', '.')
            
            # Check if it's a full path match or just a filename match
            if '/' in pattern:
                if re.search(regex_pattern, normalized_path):
                    return True
            else:
                # If no slash, match any component of the path
                file_name = os.path.basename(normalized_path)
                if re.match(f"^{regex_pattern}$", file_name):
                    return True
        else:
            # Direct string matching for simple patterns
            if pattern in normalized_path or normalized_path.endswith('/' + pattern):
                return True
                
    return False

def list_ignored_files():
    """List all files that would be ignored by git"""
    patterns = get_gitignore_patterns()
    ignored_files = []
    
    for root, dirs, files in os.walk('.'):
        # Skip .git directory
        if '.git' in root:
            continue
            
        # Remove leading './'
        root = root[2:] if root.startswith('./') else root
        if root.startswith('.'):
            root = root[1:]
            
        # Check directories
        for d in dirs[:]:
            dir_path = os.path.join(root, d)
            if matches_any_pattern(dir_path, patterns):
                ignored_files.append(dir_path + '/')
                
        # Check files
        for f in files:
            file_path = os.path.join(root, f)
            if matches_any_pattern(file_path, patterns):
                ignored_files.append(file_path)
    
    return ignored_files

def main():
    print("Files that would be excluded from Git repository based on .gitignore:")
    print("="*80)
    
    ignored_files = list_ignored_files()
    
    # Group by extension
    by_extension = {}
    for file in ignored_files:
        ext = os.path.splitext(file)[1]
        if not ext and file.endswith('/'):
            ext = 'directories'
        by_extension.setdefault(ext, []).append(file)
    
    # Print summary by extension
    for ext, files in sorted(by_extension.items()):
        print(f"\n{ext} files ({len(files)}):")
        for file in sorted(files)[:20]:  # Show first 20 of each type
            print(f"  {file}")
        if len(files) > 20:
            print(f"  ... and {len(files) - 20} more")
    
    print("\nTotal files to be excluded:", len(ignored_files))
    
    # Print important directories to be kept
    print("\nImportant directories that WILL be included:")
    core_dirs = [d for d in os.listdir('.') if os.path.isdir(d) 
                and not d.startswith('.') 
                and d not in ['pharma_env', 'env', 'venv', 'media', 'staticfiles']]
    for d in sorted(core_dirs):
        print(f"  {d}/")

if __name__ == "__main__":
    main()
