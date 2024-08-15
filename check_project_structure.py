import os
import sys
import importlib
from pathlib import Path

def check_file_exists(file_path):
    return os.path.exists(file_path)

def check_import(module_name):
    try:
        importlib.import_module(module_name)
        return True
    except ImportError:
        return False

def main():
    project_root = Path(__file__).parent.absolute()
    src_dir = project_root / 'src'

    print("Checking project structure and imports...")

    # Check for necessary files
    files_to_check = [
        project_root / '__init__.py',
        project_root / 'setup.py',
        project_root / 'requirements.txt',
        src_dir / '__init__.py',
        src_dir / 'OSBY.py',
        src_dir / 'utilities' / '__init__.py',
        src_dir / 'utilities' / 'api' / '__init__.py',
        src_dir / 'utilities' / 'api' / 'events_server.py',
        src_dir / 'utilities' / 'api' / 'events_client.py',
    ]

    for file_path in files_to_check:
        if check_file_exists(str(file_path)):
            print(f"✅ {file_path.relative_to(project_root)} exists")
        else:
            print(f"❌ {file_path.relative_to(project_root)} does not exist")

    # Add project root and src to Python path
    sys.path.insert(0, str(project_root))
    sys.path.insert(0, str(src_dir))

    # Check imports
    imports_to_check = [
        'utilities.settings',
        'utilities.api.events_server',
        'utilities.api.events_client',
    ]

    for module_name in imports_to_check:
        if check_import(module_name):
            print(f"✅ Successfully imported {module_name}")
        else:
            print(f"❌ Failed to import {module_name}")

    print("\nProject check completed.")

if __name__ == "__main__":
    main()
