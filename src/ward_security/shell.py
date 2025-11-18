#!/usr/bin/env python3
"""
Ward Security Shell Interface
Python wrapper for Ward Security Shell
"""

import os
import sys
import subprocess
from pathlib import Path

class WardShell:
    """Ward Security Shell Interface"""

    def __init__(self):
        self.ward_root = Path(__file__).parent.parent.parent
        self.ward_shell_path = self.ward_root / "ward-shell"

    def launch_shell(self) -> int:
        """Launch Ward Security Shell"""
        if not self.ward_shell_path.exists():
            print("Error: Ward Shell not found. Please run 'ward-init' first.", file=sys.stderr)
            return 1

        try:
            # Ensure the shell is executable
            os.chmod(self.ward_shell_path, 0o755)

            # Execute the Ward shell
            result = subprocess.run(
                [str(self.ward_shell_path)],
                cwd=self.ward_root,
                check=False
            )
            return result.returncode

        except Exception as e:
            print(f"Error launching Ward shell: {e}", file=sys.stderr)
            return 1

def main() -> int:
    """Main shell entry point"""
    shell = WardShell()
    return shell.launch_shell()

if __name__ == "__main__":
    sys.exit(main())