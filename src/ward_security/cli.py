#!/usr/bin/env python3
"""
Ward Security CLI Interface
Python wrapper for the Ward Security System
"""

import os
import sys
import subprocess
import argparse
from datetime import datetime
from pathlib import Path
from typing import List, Optional

# Import favorites functionality
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from favorites import WardFavorites, WardPlanter
from indexer import WardIndexer

class WardCLI:
    """Ward Security Command Line Interface"""

    def __init__(self):
        self.ward_root = Path(__file__).parent.parent.parent
        self.ward_cli_path = self.ward_root / ".ward" / "ward.sh"
        self.ward_home = Path.home() / ".ward"
        self.mcp_server_path = self.ward_home / "mcp" / "mcp_server.py"
        self.favorites = WardFavorites()
        self.planter = WardPlanter()
        self.indexer = WardIndexer()

    def run_ward_command(self, args: List[str]) -> int:
        """Execute Ward CLI command"""
        if not self.ward_cli_path.exists():
            print("Error: Ward CLI not found. Please run 'ward init' first.", file=sys.stderr)
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

    def run_mcp_server(self) -> int:
        """Run Ward as MCP server"""
        try:
            from .mcp_server import main as mcp_main
            return mcp_main()
        except ImportError:
            print("Error: MCP server not available. Install with: pip install mcp", file=sys.stderr)
            return 1
        except Exception as e:
            print(f"Error running MCP server: {e}", file=sys.stderr)
            return 1

    def main(self) -> int:
        """Main CLI entry point - simplified interface"""
        parser = argparse.ArgumentParser(
            prog="ward",
            description="Ward Security System - AI-powered terminal protection"
        )

        # Read version from pyproject.toml
        version = "2.0.3"  # Will be updated during build
        try:
            try:
                import tomllib
            except ImportError:
                import tomli as tomllib

            pyproject_path = Path(__file__).parent.parent.parent / "pyproject.toml"
            if pyproject_path.exists():
                with open(pyproject_path, "rb") as f:
                    pyproject = tomllib.load(f)
                    version = pyproject["project"]["version"]
        except (ImportError, FileNotFoundError, KeyError):
            pass

        parser.add_argument(
            "--version",
            action="version",
            version=f"Ward Security v{version}"
        )

        parser.add_argument(
            "--mcp",
            action="store_true",
            help="Run Ward as MCP server"
        )

        # Create subparsers for commands
        subparsers = parser.add_subparsers(
            dest="command",
            title="Commands",
            description="Available commands",
            metavar="COMMAND"
        )

        # Core commands
        subparsers.add_parser("status", help="Show Ward system status")
        subparsers.add_parser("validate", help="Validate security policies")

        # Path analysis
        check_parser = subparsers.add_parser("check", help="Check security policies for path")
        check_parser.add_argument("path", nargs="?", default=".", help="Path to check (default: current directory)")

        # Init command
        init_parser = subparsers.add_parser("init", help="Initialize Ward in a directory")
        init_parser.add_argument("path", nargs="?", default=".", help="Directory path to initialize (default: current directory)")
        init_parser.add_argument("--description", help="Custom description for the Ward policy")

        # MCP integration
        subparsers.add_parser("mcp-status", help="Check MCP server status")
        subparsers.add_parser("mcp-test", help="Test MCP server functionality")
        subparsers.add_parser("configure-claude", help="Configure Claude Desktop integration")

        # Favorites management
        fav_parser = subparsers.add_parser("favorites", help="Manage favorites")
        fav_subparsers = fav_parser.add_subparsers(dest="fav_action")

        fav_list = fav_subparsers.add_parser("list", help="List favorites")
        fav_add = fav_subparsers.add_parser("add", help="Add to favorites")
        fav_add.add_argument("path", help="Path to add")
        fav_add.add_argument("description", nargs="*", help="Description")
        fav_comment = fav_subparsers.add_parser("comment", help="Add comment")
        fav_comment.add_argument("path", help="Path to comment on")
        fav_comment.add_argument("comment", help="Comment text")
        fav_comment.add_argument("author", nargs="?", default="CLI User", help="Comment author")

        # Ward management
        plant_parser = subparsers.add_parser("plant", help="Plant a Ward (protection)")
        plant_parser.add_argument("path", nargs="?", default=".", help="Path to protect (defaults to current directory)")
        plant_parser.add_argument("description", nargs="*", help="Description (optional - if not provided, creates description-only Ward with all permissions)")

        lock_parser = subparsers.add_parser("lock", help="Lock directory with restriction message")
        lock_parser.add_argument("message", help="Lock restriction message")
        lock_parser.add_argument("path", nargs="?", default=".", help="Path to lock (defaults to current directory)")

        unlock_parser = subparsers.add_parser("unlock", help="Unlock directory with permission message")
        unlock_parser.add_argument("message", help="Unlock permission message")
        unlock_parser.add_argument("path", nargs="?", default=".", help="Path to unlock (defaults to current directory)")

        info_parser = subparsers.add_parser("info", help="Get Ward information")
        info_parser.add_argument("path", help="Path to check")

        # Add command with subcommands
        add_parser = subparsers.add_parser("add", help="Add various items to Ward")
        add_subparsers = add_parser.add_subparsers(dest="add_action")

        add_comment_parser = add_subparsers.add_parser("comment", help="Add comment to current directory")
        add_comment_parser.add_argument("comment", help="Comment text")
        add_comment_parser.add_argument("path", nargs="?", default=".", help="Path to comment on (defaults to current directory)")

        # Search and bookmarks
        search_parser = subparsers.add_parser("search", help="Search through indexed folders")
        search_parser.add_argument("query", help="Search query")
        search_parser.add_argument("--in", choices=["all", "name", "files", "directories", "types"], default="all", help="Search scope")
        search_parser.add_argument("--limit", type=int, default=20, help="Result limit")

        bookmark_parser = subparsers.add_parser("bookmark", help="Manage bookmarks")
        bookmark_subparsers = bookmark_parser.add_subparsers(dest="bookmark_action")

        bookmark_add = bookmark_subparsers.add_parser("add", help="Add bookmark")
        bookmark_add.add_argument("path", help="Path to bookmark")
        bookmark_add.add_argument("--category", default="default", help="Bookmark category")
        bookmark_add.add_argument("--name", help="Bookmark name")
        bookmark_add.add_argument("--desc", help="Description")
        bookmark_add.add_argument("--tags", help="Comma-separated tags")

        bookmark_list = bookmark_subparsers.add_parser("list", help="List bookmarks")
        bookmark_list.add_argument("--category", help="Filter by category")
        bookmark_list.add_argument("--tags", help="Filter by tags")

        recent_parser = subparsers.add_parser("recent", help="Show recent access")
        recent_parser.add_argument("--hours", type=int, default=24, help="Hours to look back")
        recent_parser.add_argument("--limit", type=int, default=20, help="Result limit")

        # MCP server command
        subparsers.add_parser("mcp-server", help="Run Ward as MCP server")

        # Environment activation
        subparsers.add_parser("activate", help="Activate Ward environment with prompt enhancement")
        subparsers.add_parser("deactivate", help="Deactivate Ward environment and restore prompt")

        # Help and version
        subparsers.add_parser("help", help="Show this help message")

        args = parser.parse_args()

        # Handle commands
        if args.command == "mcp-server":
            return self.run_mcp_server()
        elif args.command == "status" or args.command is None:
            return self.handle_status_command()
        elif args.command == "validate":
            return self.handle_validate_command()
        elif args.command == "check":
            return self.handle_check_command(args)
        elif args.command == "init":
            return self.handle_init_command(args)
        elif args.command == "mcp-status":
            return self.mcp_status()
        elif args.command == "mcp-test":
            return self.mcp_test()
        elif args.command == "configure-claude":
            return self.configure_claude()
        elif args.command == "favorites":
            return self.handle_favorites_command(args)
        elif args.command == "plant":
            return self.handle_plant_command(args)
        elif args.command == "lock":
            return self.handle_lock_command(args)
        elif args.command == "unlock":
            return self.handle_unlock_command(args)
        elif args.command == "info":
            return self.handle_ward_info_command(args)
        elif args.command == "add":
            return self.handle_add_command(args)
        elif args.command == "search":
            return self.handle_search_command(args)
        elif args.command == "bookmark":
            return self.handle_bookmark_command(args)
        elif args.command == "recent":
            return self.handle_recent_command(args)
        elif args.command == "activate":
            return self.handle_activate_command()
        elif args.command == "deactivate":
            return self.handle_deactivate_command()
        elif args.command == "help":
            parser.print_help()
            return 0
        else:
            # Fallback to bash CLI for unknown commands
            return self.run_ward_command([args.command] if args.command else [])

    def mcp_status(self) -> int:
        """Check MCP server status"""
        print("🤖 Ward MCP Server Status")
        print("=" * 30)

        # Check multiple potential MCP server locations
        mcp_paths = [
            self.mcp_server_path,  # ~/.ward/mcp/mcp_server.py
            Path.home() / ".local/share/uv/tools/ward-security/lib/python3.11/site-packages/ward_security/mcp_server.py",
            Path(__file__).parent / "mcp_server.py",  # Same directory as CLI
        ]

        mcp_found = False
        mcp_location = None

        for mcp_path in mcp_paths:
            if mcp_path.exists():
                mcp_found = True
                mcp_location = mcp_path
                break

        if not mcp_found:
            print("❌ MCP server not found")
            print("Checked locations:")
            for mcp_path in mcp_paths:
                print(f"  • {mcp_path}")
            return 1

        try:
            # Test if MCP server can be imported
            import subprocess

            # Test if the MCP server file exists and can be executed as Python
            if mcp_location.name == "mcp_server.py":
                # Test basic Python syntax by trying to compile the file
                result = subprocess.run(
                    [sys.executable, "-m", "py_compile", str(mcp_location)],
                    capture_output=True,
                    text=True,
                    timeout=10
                )

                if result.returncode == 0:
                    print("✅ MCP server file is valid Python")
                else:
                    print("❌ MCP server file has syntax errors")
                    print("Error:", result.stderr)
                    return 1
            else:
                # Test direct import from the found location
                result = subprocess.run(
                    [sys.executable, "-c", f"import sys; sys.path.insert(0, '{mcp_location.parent}'); from ward_security.mcp_server import app; print('✅ MCP server can be imported')"],
                    capture_output=True,
                    text=True,
                    timeout=10
                )

            if result.returncode == 0:
                print("✅ MCP server is properly configured")
                print(f"📍 Location: {mcp_location}")
                print("🚀 Ready for AI assistant integration")

                # Check if MCP dependencies are available
                try:
                    import mcp
                    print("✅ MCP library available")
                except ImportError:
                    print("⚠️  MCP library not found - install with: pip install mcp")

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

        # Check multiple potential MCP server locations (same logic as mcp_status)
        mcp_paths = [
            self.mcp_server_path,  # ~/.ward/mcp/mcp_server.py
            Path.home() / ".local/share/uv/tools/ward-security/lib/python3.11/site-packages/ward_security/mcp_server.py",
            Path(__file__).parent / "mcp_server.py",  # Same directory as CLI
        ]

        mcp_found = False
        mcp_location = None

        for mcp_path in mcp_paths:
            if mcp_path.exists():
                mcp_found = True
                mcp_location = mcp_path
                break

        if not mcp_found:
            print("❌ MCP server not found")
            print("Checked locations:")
            for mcp_path in mcp_paths:
                print(f"  • {mcp_path}")
            return 1

        try:
            # Test basic MCP server functionality
            result = subprocess.run(
                [sys.executable, str(mcp_location)],
                input='{"jsonrpc": "2.0", "id": 1, "method": "initialize"}\n',
                capture_output=True,
                text=True,
                timeout=10
            )

            if "result" in result.stdout or "error" in result.stdout:
                print("✅ MCP server is responding correctly")
                print("🔧 Ready for AI assistant integration")
                print(f"📍 Location: {mcp_location}")
                return 0
            else:
                print("❌ MCP server not responding properly")
                print("Output:", result.stdout)
                if result.stderr:
                    print("Error:", result.stderr)
                return 1

        except subprocess.TimeoutExpired:
            print("❌ MCP server test timed out")
            return 1
        except Exception as e:
            print(f"❌ Error testing MCP server: {e}")
            return 1

    def handle_favorites(self, args: List[str]) -> int:
        """Handle favorites commands"""
        if not args:
            return self.favorites_list()

        command = args[0]
        if command == "list":
            return self.favorites_list()
        elif command == "add":
            if len(args) < 2:
                print("Usage: ward favorites add <path> [description]", file=sys.stderr)
                return 1
            path = args[1]
            description = " ".join(args[2:]) if len(args) > 2 else ""
            return self.favorites_add(path, description)
        elif command == "comment":
            if len(args) < 3:
                print("Usage: ward favorites comment <path> <comment> [author]", file=sys.stderr)
                return 1
            path = args[1]
            comment = args[2]
            author = args[3] if len(args) > 3 else "CLI User"
            return self.favorites_comment(path, comment, author)
        else:
            print(f"Unknown favorites command: {command}", file=sys.stderr)
            print("Available commands: list, add, comment", file=sys.stderr)
            return 1

    def handle_plant_ward(self, args: List[str]) -> int:
        """Handle ward planting command"""
        if not args:
            print("Usage: ward plant-ward <path> [description]", file=sys.stderr)
            return 1

        path = args[0]
        description = " ".join(args[1:]) if len(args) > 1 else ""
        return self.plant_ward_cli(path, description)

    def handle_ward_info(self, args: List[str]) -> int:
        """Handle ward info command"""
        if not args:
            print("Usage: ward ward-info <path>", file=sys.stderr)
            return 1

        path = args[0]
        return self.ward_info_cli(path)

    def favorites_list(self) -> int:
        """List all favorites"""
        favorites = self.favorites.get_favorites()

        if not favorites:
            print("📋 No favorites found. Use 'ward favorites add <path>' to add Ward-protected directories.")
            return 0

        print("📋 Ward Favorites:")
        print("=" * 50)
        print()

        for i, fav in enumerate(favorites, 1):
            status = "🛡️ Protected" if fav["ward_status"]["protected"] else "❌ Unprotected"
            exists = "✅" if fav["exists"] else "❌"

            print(f"{i}. {fav['path']} {exists}")
            print(f"   📝 Description: {fav['description'] or 'No description'}")
            print(f"   🛡️ Status: {status}")
            print(f"   📅 Added: {fav['added_date'][:10]}")
            print(f"   🔄 Access count: {fav['access_count']}")

            if fav["recent_comments"]:
                print("   💬 Recent comments:")
                for comment in fav["recent_comments"]:
                    truncated = comment['comment'][:50] + ('...' if len(comment['comment']) > 50 else '')
                    print(f"      • {comment['author']}: {truncated}")

            print()

        return 0

    def favorites_add(self, path: str, description: str) -> int:
        """Add directory to favorites"""
        result = self.favorites.add_favorite(path, description)

        if result["success"]:
            self.favorites.update_access(path)
            print(f"✅ Added to favorites:")
            print(f"{path}")
            print()
            print(f"📝 Description: {description or 'No description'}")
            return 0
        else:
            print(f"❌ Failed to add to favorites: {result['error']}", file=sys.stderr)
            return 1

    def favorites_comment(self, path: str, comment: str, author: str) -> int:
        """Add comment to favorited directory"""
        result = self.favorites.add_comment(path, comment, author)

        if result["success"]:
            print(f"✅ Comment added to:")
            print(f"{path}")
            print()
            print(f"💬 {author}: {comment}")
            return 0
        else:
            print(f"❌ Failed to add comment: {result['error']}", file=sys.stderr)
            return 1

    def plant_ward_cli(self, path: str, description: str) -> int:
        """Plant a Ward via CLI"""
        result = self.planter.plant_ward(path, description, False)  # CLI initiated, not AI

        if result["success"]:
            print(f"✅ Ward planted successfully!")
            print()
            print(f"📍 Location: {result['ward_file']}")
            print(f"🔐 Password file: {result['password_file']}")
            print()
            print("⚠️ IMPORTANT SECURITY NOTICE:")
            print("• A password has been generated and stored for security")
            print("• To modify/remove this Ward, manually edit the password file")
            print("• The password file location is provided for manual user intervention")
            return 0
        else:
            print(f"❌ Failed to plant Ward: {result['error']}", file=sys.stderr)
            return 1

    def ward_info_cli(self, path: str) -> int:
        """Get Ward info via CLI"""
        info = self.planter.get_ward_info(path)

        if not info["protected"]:
            print(f"❌ No Ward found at: {path}")
            return 1

        print(f"🛡️ Ward Information for: {path}")
        print("=" * 50)
        print()
        print(f"📁 Ward file: {info['ward_file']}")
        print(f"🔐 Password protected: {'Yes' if info['password_protected'] else 'No'}")

        if info["password_protected"]:
            print(f"🗝️ Password file: {info['password_file']}")
            print()
            print("⚠️ WARNING: This Ward is password-protected.")
            print("Manual user intervention required for removal.")

        if info.get("readable"):
            print()
            print("📄 Ward Policy Content:")
            print("-" * 30)
            print(info.get("content", "Unable to read content"))
        else:
            print()
            print("❌ Ward policy file is not readable (permissions issue)")

        return 0

    def handle_favorites_command(self, args) -> int:
        """Handle favorites command with simplified interface"""
        if args.fav_action == "list" or args.fav_action is None:
            return self.favorites_list()
        elif args.fav_action == "add":
            description = " ".join(args.description) if args.description else ""
            return self.favorites_add(args.path, description)
        elif args.fav_action == "comment":
            return self.favorites_comment(args.path, args.comment, args.author)
        else:
            print(f"Unknown favorites command: {args.fav_action}", file=sys.stderr)
            return 1

    def handle_plant_command(self, args) -> int:
        """Handle plant command"""
        if args.description:
            description = " ".join(args.description)
        else:
            # No description provided - create a default description-only Ward
            description = f"이 폴더는 건드리면 안된다"

        result = self.plant_ward_cli(args.path, description)

        # Show planted result after successful planting
        if result == 0:
            print()
            print("🌱 **심어진 결과 (Planted Result):**")
            print("=" * 50)
            self.ward_info_cli(args.path)

        return result

    def handle_ward_info_command(self, args) -> int:
        """Handle info command"""
        return self.ward_info_cli(args.path)

    def handle_lock_command(self, args) -> int:
        """Handle lock command"""
        print(f"🔒 Locking directory: {args.path}")
        print(f"📝 Lock message: {args.message}")

        # Create a restrictive Ward configuration
        lock_description = f"🔒 LOCKED: {args.message}"
        result = self.plant_ward_cli(args.path, lock_description)

        if result == 0:
            print()
            print("✅ Directory locked successfully!")
            print(f"📍 Location: {args.path}")
            print(f"🔒 Restriction: {args.message}")
            print()
            print("🛡️ Lock Status:")
            print("=" * 40)
            self.ward_info_cli(args.path)

        return result

    def handle_unlock_command(self, args) -> int:
        """Handle unlock command"""
        print(f"🔓 Unlocking directory: {args.path}")
        print(f"📝 Unlock message: {args.message}")

        # Create a permissive Ward configuration
        unlock_description = f"🔓 UNLOCKED: {args.message}"
        result = self.plant_ward_cli(args.path, unlock_description)

        if result == 0:
            print()
            print("✅ Directory unlocked successfully!")
            print(f"📍 Location: {args.path}")
            print(f"🔓 Permission: {args.message}")
            print()
            print("🛡️ Unlock Status:")
            print("=" * 40)
            self.ward_info_cli(args.path)

        return result

    def handle_add_command(self, args) -> int:
        """Handle add command with subcommands"""
        if args.add_action == "comment":
            print(f"💬 Adding comment to: {args.path}")
            print(f"📝 Comment: {args.comment}")

            # For now, create a simple comment file (can be enhanced later)
            comment_file = Path(args.path) / ".ward_comment.txt"
            try:
                with open(comment_file, 'w', encoding='utf-8') as f:
                    f.write(f"💬 Comment: {args.comment}\n")
                    f.write(f"📅 Added: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                    f.write(f"👤 By: CLI User\n")

                print("✅ Comment added successfully!")
                print(f"📍 Location: {comment_file}")
                print(f"📝 Content: {args.comment}")
                return 0

            except Exception as e:
                print(f"❌ Failed to add comment: {e}", file=sys.stderr)
                return 1
        elif args.add_action is None:
            # No subcommand provided - show usage
            print("Usage: ward add <subcommand> [options]")
            print("Subcommands:")
            print("  comment    Add a comment to current directory")
            print("\nUse 'ward add <subcommand> --help' for detailed help")
            return 1
        else:
            print(f"Unknown add command: {args.add_action}", file=sys.stderr)
            return 1

    def handle_search_command(self, args) -> int:
        """Handle search command"""
        return self.search_folders(args.query, getattr(args, 'in'), args.limit)

    def handle_bookmark_command(self, args) -> int:
        """Handle bookmark command"""
        if args.bookmark_action == "add":
            tags = [tag.strip() for tag in args.tags.split(",")] if args.tags else []
            return self.add_bookmark(args.path, args.category, args.name, args.desc or "", tags)
        elif args.bookmark_action == "list":
            tags = [tag.strip() for tag in args.tags.split(",")] if args.tags else []
            return self.list_bookmarks(args.category or "", tags)
        elif args.bookmark_action is None:
            # No subcommand provided - show usage
            print("Usage: ward bookmark <subcommand> [options]")
            print("Subcommands:")
            print("  add    Add a new bookmark")
            print("  list   List existing bookmarks")
            print("\nUse 'ward bookmark <subcommand> --help' for detailed help")
            return 1
        else:
            print(f"Unknown bookmark command: {args.bookmark_action}", file=sys.stderr)
            return 1

    def handle_recent_command(self, args) -> int:
        """Handle recent command"""
        return self.show_recent(args.hours, args.limit)

    def handle_search(self, args: List[str]) -> int:
        """Handle search command"""
        if not args:
            print("Usage: ward search <query> [--in all|name|files|directories|types] [--limit N]", file=sys.stderr)
            return 1

        query = args[0]
        search_in = "all"
        limit = 20

        # Parse optional arguments
        i = 1
        while i < len(args):
            if args[i] == "--in" and i + 1 < len(args):
                search_in = args[i + 1]
                i += 2
            elif args[i] == "--limit" and i + 1 < len(args):
                try:
                    limit = int(args[i + 1])
                except ValueError:
                    print("Error: --limit must be a number", file=sys.stderr)
                    return 1
                i += 2
            else:
                i += 1

        return self.search_folders(query, search_in, limit)

    def handle_bookmark(self, args: List[str]) -> int:
        """Handle bookmark command"""
        if not args:
            return self.list_bookmarks("", [])

        command = args[0]
        if command == "add":
            if len(args) < 2:
                print("Usage: ward bookmark add <path> [--category CAT] [--name NAME] [--desc DESC] [--tags TAG1,TAG2]", file=sys.stderr)
                return 1

            path = args[1]
            category = "default"
            name = None
            description = ""
            tags = []

            # Parse optional arguments
            i = 2
            while i < len(args):
                if args[i] == "--category" and i + 1 < len(args):
                    category = args[i + 1]
                    i += 2
                elif args[i] == "--name" and i + 1 < len(args):
                    name = args[i + 1]
                    i += 2
                elif args[i] == "--desc" and i + 1 < len(args):
                    description = args[i + 1]
                    i += 2
                elif args[i] == "--tags" and i + 1 < len(args):
                    tags = [tag.strip() for tag in args[i + 1].split(",")]
                    i += 2
                else:
                    i += 1

            return self.add_bookmark(path, category, name, description, tags)

        elif command == "list":
            category = None
            tags = []

            # Parse optional arguments
            i = 1
            while i < len(args):
                if args[i] == "--category" and i + 1 < len(args):
                    category = args[i + 1]
                    i += 2
                elif args[i] == "--tags" and i + 1 < len(args):
                    tags = [tag.strip() for tag in args[i + 1].split(",")]
                    i += 2
                else:
                    i += 1

            return self.list_bookmarks(category, tags)

        else:
            print(f"Unknown bookmark command: {command}", file=sys.stderr)
            print("Available commands: add, list", file=sys.stderr)
            return 1

    def handle_recent(self, args: List[str]) -> int:
        """Handle recent command"""
        hours = 24
        limit = 20

        # Parse optional arguments
        i = 0
        while i < len(args):
            if args[i] == "--hours" and i + 1 < len(args):
                try:
                    hours = int(args[i + 1])
                except ValueError:
                    print("Error: --hours must be a number", file=sys.stderr)
                    return 1
                i += 2
            elif args[i] == "--limit" and i + 1 < len(args):
                try:
                    limit = int(args[i + 1])
                except ValueError:
                    print("Error: --limit must be a number", file=sys.stderr)
                    return 1
                i += 2
            else:
                i += 1

        return self.show_recent(hours, limit)

    def search_folders(self, query: str, search_in: str, limit: int) -> int:
        """Search through indexed folders"""
        result = self.indexer.search_folders(query, search_in, limit)

        if result["success"]:
            print(f"🔍 Search Results for '{result['query']}' (in {result['search_in']}):")
            print(f"Found {result['total_results']} results")
            print("=" * 50)
            print()

            for i, match in enumerate(result["results"], 1):
                print(f"{i}. 📁 {match['path']} (Score: {match['score']})")
                print(f"   📊 {match['total_files']} files, {match['total_dirs']} directories")
                print(f"   💾 Size: {match['total_size']:,} bytes")
                print(f"   🔍 Matches: {', '.join(match['matches'][:3])}", end="")
                if len(match['matches']) > 3:
                    print(f" (+{len(match['matches'])-3} more)")
                else:
                    print()
                print()

            return 0
        else:
            print(f"❌ Search failed: {result.get('error', 'Unknown error')}", file=sys.stderr)
            return 1

    def add_bookmark(self, path: str, category: str, name: str, description: str, tags: List[str]) -> int:
        """Add a bookmark"""
        result = self.indexer.add_bookmark(path, category, name, description, tags)

        if result["success"]:
            print("✅ Bookmark added successfully!")
            print()
            print(f"📁 Path: {path}")
            print(f"📂 Category: {category}")
            print(f"🏷️ Tags: {', '.join(tags) if tags else 'None'}")
            print(f"📝 Description: {description or 'No description'}")

            # Record access for recent history
            self.indexer.record_access(path, "bookmark_add")
            return 0
        else:
            print(f"❌ Failed to add bookmark: {result.get('error', 'Unknown error')}", file=sys.stderr)
            return 1

    def list_bookmarks(self, category: str, tags: List[str]) -> int:
        """List bookmarks"""
        bookmarks = self.indexer.get_bookmarks(category, tags)

        if not bookmarks:
            filter_info = []
            if category:
                filter_info.append(f"category: {category}")
            if tags:
                filter_info.append(f"tags: {', '.join(tags)}")

            filter_text = f" (filters: {', '.join(filter_info)})" if filter_info else ""
            print(f"📋 No bookmarks found{filter_text}. Use 'ward bookmark add' to add bookmarks.")
            return 0

        print("📋 Ward Bookmarks:")
        print("=" * 50)
        print()

        # Group by category
        categories = {}
        for bookmark in bookmarks:
            cat = bookmark["category"]
            if cat not in categories:
                categories[cat] = []
            categories[cat].append(bookmark)

        for category, cat_bookmarks in categories.items():
            print(f"📂 {category.upper()} ({len(cat_bookmarks)} bookmarks)")
            print("-" * 30)

            for i, bookmark in enumerate(cat_bookmarks, 1):
                print(f"  {i}. 📁 {bookmark['name']}")
                print(f"     📍 {bookmark['path']}")
                print(f"     🏷️ Tags: {', '.join(bookmark['tags']) if bookmark['tags'] else 'None'}")
                print(f"     🔄 Access count: {bookmark['access_count']}")
                if bookmark['description']:
                    print(f"     📝 {bookmark['description']}")
                print()

        return 0

    def show_recent(self, hours: int, limit: int) -> int:
        """Show recent access"""
        recent_access = self.indexer.get_recent_access(hours, limit)

        if not recent_access:
            print(f"📋 No recent access found in the last {hours} hours.")
            return 0

        print(f"📋 Recent Access (last {hours} hours):")
        print("=" * 50)
        print()

        from datetime import datetime
        for i, entry in enumerate(recent_access, 1):
            timestamp = datetime.fromisoformat(entry["timestamp"])
            time_str = timestamp.strftime("%Y-%m-%d %H:%M:%S")

            print(f"{i}. 📁 {entry['folder_name']}")
            print(f"   📍 {entry['path']}")
            print(f"   ⏰ {time_str}")
            print(f"   🔧 Action: {entry['action']}")
            print()

        return 0

    def handle_activate_command(self) -> int:
        """Activate Ward environment with prompt enhancement"""
        print("🛡️ Activating Ward Environment...")

        # Check if .ward file exists in current directory
        current_dir = Path.cwd()
        ward_file = current_dir / ".ward"

        if not ward_file.exists():
            print("❌ No .ward policy found in current directory")
            print("💡 Initialize Ward first: ward init")
            return 1

        try:
            # Save original PS1 if not already saved
            original_ps1 = os.environ.get("WARD_ORIGINAL_PS1")
            if not original_ps1:
                original_ps1 = os.environ.get("PS1", "")
                os.environ["WARD_ORIGINAL_PS1"] = original_ps1

            # Create Ward-enhanced prompt
            current_ps1 = os.environ.get("PS1", "")
            ward_prefix = "🛡️ "

            # Check if Ward prefix already exists
            if ward_prefix not in current_ps1:
                new_ps1 = f"{ward_prefix}{current_ps1}"
                os.environ["PS1"] = new_ps1

                # Create activation script for persistence
                activation_script = Path.home() / ".ward-activate.sh"
                with open(activation_script, 'w') as f:
                    f.write(f"""#!/bin/bash
# Ward Environment Activation
export WARD_ACTIVE=true
export WARD_ORIGINAL_PS1="${original_ps1}"
export PS1="{new_ps1}"
echo "🛡️ Ward environment activated!"
echo "💡 Run 'ward deactivate' to restore original prompt"
""")
                activation_script.chmod(0o755)

                print("✅ Ward environment activated!")
                print(f"📌 Original prompt saved: {original_ps1[:50]}{'...' if len(original_ps1) > 50 else ''}")
                print("💡 Your prompt now shows 🛡️ to indicate Ward is active")
                print("🔧 Ward protection is now monitoring this directory")
                print()
                print("To restore original prompt later:")
                print("   ward deactivate")
                print()
                print("⚠️  Note: For permanent prompt changes, run:")
                print(f"   source {activation_script}")
                return 0
            else:
                print("✅ Ward environment is already active!")
                return 1

        except Exception as e:
            print(f"❌ Error activating Ward environment: {e}")
            return 1

    def handle_deactivate_command(self) -> int:
        """Deactivate Ward environment and restore original prompt"""
        print("🔓 Deactivating Ward Environment...")

        try:
            # Restore original PS1
            original_ps1 = os.environ.get("WARD_ORIGINAL_PS1")
            if original_ps1:
                os.environ["PS1"] = original_ps1
                print("✅ Original prompt restored!")
                print("🛡️ Ward environment deactivated")

                # Remove activation script if it exists
                activation_script = Path.home() / ".ward-activate.sh"
                if activation_script.exists():
                    activation_script.unlink()
                    print("🗑️  Activation script removed")

                return 0
            else:
                print("⚠️  No original prompt found - cannot restore")
                print("💡 You may need to manually reset your PS1")
                return 1

        except Exception as e:
            print(f"❌ Error deactivating Ward environment: {e}")
            return 1

    def handle_status_command(self) -> int:
        """Handle status command"""
        print("🔍 Ward Security System Status")
        print("=" * 30)

        # Check if current directory has .ward file
        current_dir = Path.cwd()
        ward_file = current_dir / ".ward"

        if ward_file.exists():
            print(f"✅ Ward protection active in: {current_dir}")
            print(f"📁 Policy file: {ward_file}")

            # Read and display basic policy info
            try:
                with open(ward_file, 'r') as f:
                    content = f.read()
                    for line in content.split('\n'):
                        if line.startswith('@description:'):
                            print(f"📝 {line}")
                            break
            except Exception:
                pass
        else:
            print(f"❌ No Ward protection in: {current_dir}")
            print("💡 Initialize with: ward init")

        return 0

    def handle_validate_command(self) -> int:
        """Handle validate command"""
        print("🔒 Validating Ward Security Policies")
        print("=" * 35)

        current_dir = Path.cwd()
        ward_file = current_dir / ".ward"

        if not ward_file.exists():
            print("❌ No .ward policy found to validate")
            print("💡 Initialize first: ward init")
            return 1

        try:
            with open(ward_file, 'r') as f:
                content = f.read()

            if '@whitelist:' in content and '@blacklist:' in content:
                print("✅ Policy structure is valid")

                # Count rules
                whitelist_count = content.count('@whitelist:')
                blacklist_count = content.count('@blacklist:')

                print(f"📋 Whitelist rules: {whitelist_count}")
                print(f"🚫 Blacklist rules: {blacklist_count}")

            else:
                print("⚠️  Incomplete policy - missing whitelist or blacklist")
                return 1

        except Exception as e:
            print(f"❌ Error reading policy file: {e}")
            return 1

        return 0

    def handle_check_command(self, args) -> int:
        """Handle check command"""
        target_path = Path(args.path).resolve()
        ward_file = target_path / ".ward"

        if not ward_file.exists():
            print(f"❌ No .ward policy found in {args.path}")
            print()
            print("💡 Initialize Ward first:")
            print(f"   ward init {args.path}")
            print()
            print("Or initialize in current directory:")
            print("   ward init")
            return 1

        print(f"🔍 Checking Ward policies for: {args.path}")
        print("=" * 40)
        print(f"✅ .ward policy found: {ward_file}")

        # Read and display policy summary
        try:
            with open(ward_file, 'r') as f:
                content = f.read()

            if '@description:' in content:
                for line in content.split('\n'):
                    if line.startswith('@description:'):
                        print(f"📝 {line}")
                        break

            print("📋 Policy active - use specific commands for detailed analysis")

        except Exception as e:
            print(f"⚠️  Warning reading policy: {e}")

        return 0

    def handle_init_command(self, args) -> int:
        """Handle init command with legacy installation warnings"""
        path = args.path or "."

        # Check for legacy installations and warn user
        legacy_ward = Path.home() / ".ward"
        local_bin_ward = Path.home() / ".local/bin" / "ward"

        if legacy_ward.exists():
            print("⚠️  WARNING: Legacy Ward installation detected!")
            print(f"   Found at: {legacy_ward}")
            print("   This may cause conflicts with UV installation")
            print("   Consider removing with: rm -rf ~/.ward")
            print()

        if local_bin_ward.exists() or local_bin_ward.is_symlink():
            print("⚠️  WARNING: Legacy Ward binary found!")
            print(f"   Found at: {local_bin_ward}")
            print("   This may cause conflicts with UV installation")
            print("   Consider removing with: rm -f ~/.local/bin/ward")
            print()

        # Create directory if it doesn't exist
        target_path = Path(path).resolve()
        target_path.mkdir(parents=True, exist_ok=True)

        # Check if .ward already exists
        ward_file = target_path / ".ward"
        if ward_file.exists():
            print(f"❌ .ward file already exists in {path}")
            return 1

        # Create basic .ward file content
        description = getattr(args, 'description', 'AI-Assisted Development Project')
        ward_content = f"""# Ward Security Configuration
@description: {description}
@whitelist: ls cat pwd echo grep sed awk git python npm node code vim
@blacklist: rm -rf / sudo su chmod chown docker kubectl
@allow_comments: true
@max_comments: 5
@comment_prompt: "Explain changes from a security perspective"
"""

        # Write .ward file
        with open(ward_file, 'w') as f:
            f.write(ward_content)

        print(f"✅ Ward initialized in {path}")
        print(f"📁 Policy file: {ward_file}")
        print()
        print("💡 Tip: Use UV-installed Ward for best experience:")
        print("   export PATH=\"$HOME/.local/share/uv/tools/ward-security/bin:$PATH\"")
        return 0

def main() -> int:
    """Main entry point for the CLI"""
    cli = WardCLI()
    return cli.main()

if __name__ == "__main__":
    sys.exit(main())