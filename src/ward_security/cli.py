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
        self.ward_home = Path.home() / ".ward"
        self.mcp_server_path = self.ward_home / "mcp" / "mcp_server.py"

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

        # Handle special MCP commands
        if args.command and args.command[0] in ["mcp-status", "mcp-test", "configure-claude"]:
            if args.command[0] == "mcp-status":
                return self.mcp_status()
            elif args.command[0] == "mcp-test":
                return self.mcp_test()
            elif args.command[0] == "configure-claude":
                return self.configure_claude()

        # Convert Python args to bash CLI format
        ward_args = []
        if args.verbose:
            ward_args.append("--verbose")
        if args.quiet:
            ward_args.append("--quiet")

        ward_args.extend(args.command)

        return self.run_ward_command(ward_args)

    def mcp_status(self) -> int:
        """Check MCP server status"""
        print("🤖 Ward MCP Server Status")
        print("=" * 30)

        if not self.mcp_server_path.exists():
            print("❌ MCP server not found")
            print(f"Expected at: {self.mcp_server_path}")
            return 1

        try:
            # Test if MCP server can be imported
            import sys
            sys.path.insert(0, str(self.mcp_server_path.parent))

            # Simple import test
            import subprocess
            result = subprocess.run(
                [sys.executable, "-c", "from mcp_server import app; print('✅ MCP server can be imported')"],
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode == 0:
                print("✅ MCP server is properly configured")
                print(f"📍 Location: {self.mcp_server_path}")
                return 0
            else:
                print("❌ MCP server configuration error")
                print("Error:", result.stderr)
                return 1

        except Exception as e:
            print(f"❌ Error checking MCP server: {e}")
            return 1

    def configure_claude(self) -> int:
        """Configure Claude Desktop for Ward integration"""
        configure_script = self.ward_root / "configure-claude-desktop.sh"

        if not configure_script.exists():
            print("❌ Claude Desktop configuration script not found")
            return 1

        try:
            os.chmod(config_script, 0o755)
            result = subprocess.run([str(config_script)], cwd=self.ward_root)
            return result.returncode
        except Exception as e:
            print(f"❌ Error configuring Claude Desktop: {e}")
            return 1

    def mcp_test(self) -> int:
        """Test MCP server functionality"""
        print("🧪 Testing Ward MCP Server")
        print("=" * 30)

        if not self.mcp_server_path.exists():
            print("❌ MCP server not found. Please run setup first.")
            return 1

        try:
            # Test basic MCP server functionality
            result = subprocess.run(
                [sys.executable, str(self.mcp_server_path)],
                input='{"jsonrpc": "2.0", "id": 1, "method": "initialize"}',
                capture_output=True,
                text=True,
                timeout=10
            )

            if "result" in result.stdout or "error" in result.stdout:
                print("✅ MCP server is responding correctly")
                print("🔧 Ready for AI assistant integration")
                return 0
            else:
                print("❌ MCP server not responding properly")
                print("Output:", result.stdout)
                return 1

        except subprocess.TimeoutExpired:
            print("❌ MCP server test timed out")
            return 1
        except Exception as e:
            print(f"❌ Error testing MCP server: {e}")
            return 1

def main() -> int:
    """Main entry point for the CLI"""
    cli = WardCLI()
    return cli.main()

if __name__ == "__main__":
    sys.exit(main())