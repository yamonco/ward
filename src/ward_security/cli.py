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

# Import favorites functionality
from .favorites import WardFavorites, WardPlanter
from .indexer import WardIndexer

class WardCLI:
    """Ward Security Command Line Interface"""

    def __init__(self):
        self.ward_root = Path(__file__).parent.parent.parent
        self.ward_cli_path = self.ward_root / ".ward" / "ward-cli.sh"
        self.ward_home = Path.home() / ".ward"
        self.mcp_server_path = self.ward_home / "mcp" / "mcp_server.py"
        self.favorites = WardFavorites()
        self.planter = WardPlanter()
        self.indexer = WardIndexer()

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
        if args.command and args.command[0] in ["mcp-status", "mcp-test", "configure-claude", "favorites", "plant-ward", "ward-info", "search", "bookmark", "recent"]:
            if args.command[0] == "mcp-status":
                return self.mcp_status()
            elif args.command[0] == "mcp-test":
                return self.mcp_test()
            elif args.command[0] == "configure-claude":
                return self.configure_claude()
            elif args.command[0] == "favorites":
                return self.handle_favorites(args.command[1:])
            elif args.command[0] == "plant-ward":
                return self.handle_plant_ward(args.command[1:])
            elif args.command[0] == "ward-info":
                return self.handle_ward_info(args.command[1:])
            elif args.command[0] == "search":
                return self.handle_search(args.command[1:])
            elif args.command[0] == "bookmark":
                return self.handle_bookmark(args.command[1:])
            elif args.command[0] == "recent":
                return self.handle_recent(args.command[1:])

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

def main() -> int:
    """Main entry point for the CLI"""
    cli = WardCLI()
    return cli.main()

if __name__ == "__main__":
    sys.exit(main())