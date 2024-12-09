#!/usr/bin/env python3
import os
import stat
from pathlib import Path
import shutil

def install_hooks():
    # Get the project root directory
    project_root = Path(__file__).parent.parent
    hooks_dir = project_root / '.git' / 'hooks'
    source_dir = project_root / 'scripts' / 'git-hooks'

    # Create hooks directory if it doesn't exist
    hooks_dir.mkdir(exist_ok=True)

    # Copy each hook and make it executable
    for hook_file in source_dir.glob('*'):
        if not hook_file.name.startswith('.'):
            dest_file = hooks_dir / hook_file.name
            shutil.copy2(hook_file, dest_file)
            
            # Make the hook executable
            st = os.stat(dest_file)
            os.chmod(dest_file, st.st_mode | stat.S_IEXEC)
            print(f"Installed: {hook_file.name}")

if __name__ == '__main__':
    install_hooks() 