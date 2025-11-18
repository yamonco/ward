#!/usr/bin/env python3
"""
Ward Security Installer
Python-based installer for Ward Security System
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path
from typing import Optional

class WardInstaller:
    """Ward Security System Installer"""

    def __init__(self):
        self.package_root = Path(__file__).parent.parent.parent
        self.ward_dir = self.package_root / ".ward"

    def copy_ward_files(self, target_dir: Path) -> bool:
        """Copy Ward files to target directory"""
        try:
            # Create .ward directory in target
            target_ward = target_dir / ".ward"
            target_ward.mkdir(exist_ok=True)

            # Copy Ward system files
            if self.ward_dir.exists():
                shutil.copytree(self.ward_dir, target_ward, dirs_exist_ok=True)

            # Copy setup scripts
            for script in ["setup-ward.sh", "ward-cli.sh", "ward-shell"]:
                source = self.package_root / script
                if source.exists():
                    shutil.copy2(source, target_dir)

            # Make scripts executable
            for script_file in target_dir.glob("*.sh"):
                script_file.chmod(0o755)

            return True

        except Exception as e:
            print(f"Error copying Ward files: {e}", file=sys.stderr)
            return False

    def run_setup_script(self, target_dir: Path) -> bool:
        """Run the Ward setup script"""
        setup_script = target_dir / "setup-ward.sh"
        if not setup_script.exists():
            print("Setup script not found", file=sys.stderr)
            return False

        try:
            result = subprocess.run(
                [str(setup_script)],
                cwd=target_dir,
                check=False
            )
            return result.returncode == 0

        except Exception as e:
            print(f"Error running setup script: {e}", file=sys.stderr)
            return False

    def initialize_project(self, target_dir: Optional[Path] = None) -> bool:
        """Initialize Ward Security in a project"""
        if target_dir is None:
            target_dir = Path.cwd()

        print(f"Initializing Ward Security in: {target_dir}")

        # Copy Ward files
        if not self.copy_ward_files(target_dir):
            return False

        # Create basic .ward policy file
        ward_file = target_dir / ".ward"
        if not ward_file.exists():
            ward_content = """# Ward Security Policy
@description: Project initialized with Ward Security
@whitelist: ls cat pwd echo grep sed awk
@allow_comments: true
@max_comments: 5
@comment_prompt: "Explain changes from a security perspective"
"""
            ward_file.write_text(ward_content)

        print("✓ Ward Security initialized successfully")
        print(f"  - Policy file: {ward_file}")
        print("  - Run 'ward-cli status' to check system status")
        print("  - Run 'ward-cli check .' to analyze policies")

        return True

    def main(self) -> int:
        """Main installer entry point"""
        import argparse

        parser = argparse.ArgumentParser(
            prog="ward-init",
            description="Initialize Ward Security in a project"
        )

        parser.add_argument(
            "path",
            nargs="?",
            help="Target directory (default: current directory)"
        )

        parser.add_argument(
            "--here",
            action="store_true",
            help="Initialize in current directory"
        )

        args = parser.parse_args()

        # Determine target directory
        if args.here or not args.path:
            target_dir = Path.cwd()
        else:
            target_dir = Path(args.path).resolve()

        if not target_dir.exists():
            print(f"Error: Directory does not exist: {target_dir}", file=sys.stderr)
            return 1

        # Initialize Ward Security
        if self.initialize_project(target_dir):
            return 0
        else:
            return 1

if __name__ == "__main__":
    sys.exit(WardInstaller().main())