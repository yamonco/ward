#!/usr/bin/env python3
"""
Ward Security CLI Interface
Python wrapper for the Ward Security System
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path
from typing import List, Optional

class WardCLI:
    """Ward Security Command Line Interface"""

    def __init__(self):
        self.ward_root = Path(__file__).parent.parent.parent
        self.ward_cli_path = self.ward_root / ".ward" / "ward-cli.sh"

    def run_ward_command(self, args: List[str]) -> int:
        """Execute Ward CLI command"""
        if not self.ward_cli_path.exists():
            print("Error: Ward CLI not found. Please run 'ward-init' first.", file=sys.stderr)
            return 1

        try:
            # Ensure the CLI is executable
            os.chmod(self.ward_cli_path, 0o755)

            # Execute the bash CLI
            result = subprocess.run(
                [str(self.ward_cli_path)] + args,
                cwd=self.ward_root,
                check=False
            )
            return result.returncode

        except Exception as e:
            print(f"Error executing Ward command: {e}", file=sys.stderr)
            return 1

    def main(self) -> int:
        """Main CLI entry point"""
        parser = argparse.ArgumentParser(
            prog="ward",
            description="Ward Security System - Enterprise file system protection"
        )

        parser.add_argument(
            "--version",
            action="version",
            version="Ward Security v2.0.0"
        )

        parser.add_argument(
            "-v", "--verbose",
            action="store_true",
            help="Enable verbose output"
        )

        parser.add_argument(
            "-q", "--quiet",
            action="store_true",
            help="Suppress non-error output"
        )

        parser.add_argument(
            "command",
            nargs="*",
            help="Ward command and arguments"
        )

        args = parser.parse_args()

        # Convert Python args to bash CLI format
        ward_args = []
        if args.verbose:
            ward_args.append("--verbose")
        if args.quiet:
            ward_args.append("--quiet")

        ward_args.extend(args.command)

        return self.run_ward_command(ward_args)

def main() -> int:
    """Main entry point for the CLI"""
    cli = WardCLI()
    return cli.main()

if __name__ == "__main__":
    sys.exit(main())