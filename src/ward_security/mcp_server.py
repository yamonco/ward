#!/usr/bin/env python3
"""
Ward Security MCP Server
Provides Ward security features through Model Context Protocol (MCP)

This server enables AI assistants like Claude, Copilot, and ChatGPT
to interact with Ward security policies through standardized MCP interface.
"""

import asyncio
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional
from datetime import datetime

try:
    from mcp.server import Server
    from mcp.server.stdio import stdio_server
    from mcp.types import Tool, Resource, TextContent, ImageContent
except ImportError:
    print("Error: MCP dependencies not installed. Please run: pip install mcp")
    sys.exit(1)

# Import Ward favorites, planter, and indexer
try:
    from .favorites import WardFavorites, WardPlanter
    from .indexer import WardIndexer
except ImportError:
    # Handle direct execution case
    sys.path.insert(0, os.path.dirname(__file__))
    from favorites import WardFavorites, WardPlanter
    from indexer import WardIndexer

app = Server("ward-security")

class WardMCPBridge:
    """Bridge between Ward CLI and MCP protocol"""

    def __init__(self):
        self.ward_root = Path.home() / ".ward"
        self.ward_cli = self.ward_root / "ward"

    def run_ward_command(self, cmd: List[str]) -> Dict[str, Any]:
        """Execute Ward CLI command and return structured result"""
        try:
            if not self.ward_cli.exists():
                return {
                    "success": False,
                    "error": "Ward CLI not found. Please run 'setup-ward.sh' first.",
                    "output": ""
                }

            result = subprocess.run(
                [str(self.ward_cli)] + cmd,
                capture_output=True,
                text=True,
                timeout=30
            )

            return {
                "success": result.returncode == 0,
                "output": result.stdout.strip(),
                "error": result.stderr.strip() if result.stderr else None
            }
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "error": "Command timeout after 30 seconds",
                "output": ""
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Error executing Ward command: {str(e)}",
                "output": ""
            }

ward_bridge = WardMCPBridge()
ward_favorites = WardFavorites()
ward_planter = WardPlanter()
ward_indexer = WardIndexer()

@app.list_tools()
async def list_tools() -> List[Tool]:
    """List available Ward security tools"""
    return [
        Tool(
            name="ward_check",
            description="Check Ward security policies for a specific path",
            inputSchema={
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Path to check (default: current directory)"
                    }
                }
            }
        ),
        Tool(
            name="ward_status",
            description="Get overall Ward security system status",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),
        Tool(
            name="ward_validate",
            description="Validate all Ward security policies",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),
        Tool(
            name="ward_allow_operation",
            description="Allow AI operation in specific scope with justification",
            inputSchema={
                "type": "object",
                "properties": {
                    "operation": {
                        "type": "string",
                        "description": "Operation type (e.g., 'file_modification', 'system_access')"
                    },
                    "scope": {
                        "type": "string",
                        "description": "Scope/path where operation is allowed"
                    },
                    "justification": {
                        "type": "string",
                        "description": "Reason for allowing this operation"
                    },
                    "duration": {
                        "type": "string",
                        "description": "How long to allow this (e.g., '1h', '30m', 'session')"
                    }
                },
                "required": ["operation", "justification"]
            }
        ),
        Tool(
            name="ward_ai_log",
            description="Get recent AI activity log",
            inputSchema={
                "type": "object",
                "properties": {
                    "timeframe": {
                        "type": "string",
                        "description": "Time period (e.g., '1h', '24h', '1d')",
                        "default": "1h"
                    }
                }
            }
        ),
        Tool(
            name="ward_create_policy",
            description="Create or update Ward security policy for AI",
            inputSchema={
                "type": "object",
                "properties": {
                    "description": {
                        "type": "string",
                        "description": "Description of the security policy"
                    },
                    "whitelist": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Allowed commands"
                    },
                    "blacklist": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Blocked commands"
                    },
                    "ai_mode": {
                        "type": "string",
                        "description": "AI mode (enabled, restricted, read_only)",
                        "enum": ["enabled", "restricted", "read_only"]
                    },
                    "ai_guidance": {
                        "type": "boolean",
                        "description": "Enable AI guidance and hints"
                    }
                },
                "required": ["description"]
            }
        ),
        Tool(
            name="ward_favorites_list",
            description="List all Ward-favorited directories with metadata",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),
        Tool(
            name="ward_favorites_add",
            description="Add a Ward-protected directory to favorites",
            inputSchema={
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Path to the Ward-protected directory"
                    },
                    "description": {
                        "type": "string",
                        "description": "Description of the favorite"
                    }
                },
                "required": ["path"]
            }
        ),
        Tool(
            name="ward_favorites_comment",
            description="Add a comment to a favorited directory",
            inputSchema={
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Path to the favorited directory"
                    },
                    "comment": {
                        "type": "string",
                        "description": "Comment to add"
                    },
                    "author": {
                        "type": "string",
                        "description": "Author of the comment (default: AI)",
                        "default": "AI"
                    }
                },
                "required": ["path", "comment"]
            }
        ),
        Tool(
            name="ward_plant",
            description="Plant a Ward in a directory with password protection",
            inputSchema={
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Path where to plant the Ward"
                    },
                    "description": {
                        "type": "string",
                        "description": "Description for the Ward policy"
                    },
                    "ai_initiated": {
                        "type": "boolean",
                        "description": "Whether this is AI-initiated (requires user confirmation)",
                        "default": true
                    }
                },
                "required": ["path"]
            }
        ),
        Tool(
            name="ward_info",
            description="Get Ward information including password protection status",
            inputSchema={
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Path to check for Ward information"
                    }
                },
                "required": ["path"]
            }
        ),
        Tool(
            name="ward_search",
            description="Search through Ward-protected folders",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query"
                    },
                    "search_in": {
                        "type": "string",
                        "description": "Where to search (all, name, files, directories, types)",
                        "enum": ["all", "name", "files", "directories", "types"],
                        "default": "all"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of results",
                        "default": 20
                    }
                },
                "required": ["query"]
            }
        ),
        Tool(
            name="ward_bookmark_add",
            description="Add a Ward-protected folder to bookmarks",
            inputSchema={
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Path to the Ward-protected folder"
                    },
                    "category": {
                        "type": "string",
                        "description": "Bookmark category",
                        "default": "default"
                    },
                    "name": {
                        "type": "string",
                        "description": "Custom name for bookmark"
                    },
                    "description": {
                        "type": "string",
                        "description": "Description of the bookmark"
                    },
                    "tags": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Tags for categorization"
                    }
                },
                "required": ["path"]
            }
        ),
        Tool(
            name="ward_bookmark_list",
            description="List bookmarks with optional filtering",
            inputSchema={
                "type": "object",
                "properties": {
                    "category": {
                        "type": "string",
                        "description": "Filter by category"
                    },
                    "tags": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Filter by tags"
                    }
                }
            }
        ),
        Tool(
            name="ward_recent",
            description="Get recently accessed Ward-protected folders",
            inputSchema={
                "type": "object",
                "properties": {
                    "hours": {
                        "type": "integer",
                        "description": "Time window in hours",
                        "default": 24
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of results",
                        "default": 20
                    }
                }
            }
        ),
        Tool(
            name="ward_index",
            description="Index a Ward-protected folder for search",
            inputSchema={
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Path to the Ward-protected folder to index"
                    }
                },
                "required": ["path"]
            }
        ),
        Tool(
            name="ward_label_add",
            description="Add labels to a Ward-protected folder for AI understanding",
            inputSchema={
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Path to the Ward-protected folder"
                    },
                    "labels": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Labels to add (e.g., ['frontend', 'api', 'database'])"
                    },
                    "description": {
                        "type": "string",
                        "description": "Description of the folder's purpose"
                    }
                },
                "required": ["path", "labels"]
            }
        ),
        Tool(
            name="ward_label_list",
            description="List folders with specific labels or all labeled folders",
            inputSchema={
                "type": "object",
                "properties": {
                    "label": {
                        "type": "string",
                        "description": "Filter by specific label (optional)"
                    }
                }
            }
        ),
        Tool(
            name="ward_label_suggest",
            description="Get AI-friendly label suggestions for a folder",
            inputSchema={
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Path to the Ward-protected folder to analyze"
                    }
                },
                "required": ["path"]
            }
        ),
        Tool(
            name="ward_labels_available",
            description="Get list of all available labels with descriptions",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        )
    ]

@app.call_tool()
async def call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
    """Execute Ward security tools"""

    try:
        if name == "ward_check":
            path = arguments.get("path", ".")
            result = ward_bridge.run_ward_command(["check", path])
            return [TextContent(type="text", text=result["output"] or result["error"])]

        elif name == "ward_status":
            result = ward_bridge.run_ward_command(["status"])
            return [TextContent(type="text", text=result["output"] or result["error"])]

        elif name == "ward_validate":
            result = ward_bridge.run_ward_command(["validate"])
            return [TextContent(type="text", text=result["output"] or result["error"])]

        elif name == "ward_allow_operation":
            operation = arguments["operation"]
            justification = arguments["justification"]
            scope = arguments.get("scope", ".")
            duration = arguments.get("duration", "session")

            cmd = ["ai", "allow", operation, "--justification", justification, "--scope", scope]
            if duration != "session":
                cmd.extend(["--duration", duration])

            result = ward_bridge.run_ward_command(cmd)
            return [TextContent(type="text", text=result["output"] or result["error"])]

        elif name == "ward_ai_log":
            timeframe = arguments.get("timeframe", "1h")
            result = ward_bridge.run_ward_command(["ai", "log", "--last", timeframe])
            return [TextContent(type="text", text=result["output"] or result["error"])]

        elif name == "ward_create_policy":
            # Build .ward file content
            description = arguments["description"]
            whitelist = arguments.get("whitelist", [])
            blacklist = arguments.get("blacklist", [])
            ai_mode = arguments.get("ai_mode", "enabled")
            ai_guidance = arguments.get("ai_guidance", True)

            ward_content = f"@description: {description}\n"
            if whitelist:
                ward_content += f"@whitelist: {' '.join(whitelist)}\n"
            if blacklist:
                ward_content += f"@blacklist: {' '.join(blacklist)}\n"
            if ai_mode:
                ward_content += f"@ai_mode: {ai_mode}\n"
            if ai_guidance:
                ward_content += "@ai_guidance: true\n"

            # Write .ward file
            ward_file = Path(".ward")
            with open(ward_file, 'w') as f:
                f.write(ward_content)

            # Validate the created policy
            result = ward_bridge.run_ward_command(["validate"])

            response = f"✅ Created .ward security policy:\n\n{ward_content}\n"
            if result["output"]:
                response += f"\n📋 Validation result:\n{result['output']}"
            if result["error"]:
                response += f"\n⚠️ Validation warnings:\n{result['error']}"

            return [TextContent(type="text", text=response)]

        elif name == "ward_favorites_list":
            favorites = ward_favorites.get_favorites()

            if not favorites:
                return [TextContent(type="text", text="📋 No favorites found. Use 'ward_favorites_add' to add Ward-protected directories.")]

            response = "📋 Ward Favorites:\n" + "="*50 + "\n\n"

            for i, fav in enumerate(favorites, 1):
                status = "🛡️ Protected" if fav["ward_status"]["protected"] else "❌ Unprotected"
                exists = "✅" if fav["exists"] else "❌"

                response += f"{i}. {fav['path']} {exists}\n"
                response += f"   📝 Description: {fav['description'] or 'No description'}\n"
                response += f"   🛡️ Status: {status}\n"
                response += f"   📅 Added: {fav['added_date'][:10]}\n"
                response += f"   🔄 Access count: {fav['access_count']}\n"

                if fav["recent_comments"]:
                    response += "   💬 Recent comments:\n"
                    for comment in fav["recent_comments"]:
                        response += f"      • {comment['author']}: {comment['comment'][:50]}{'...' if len(comment['comment']) > 50 else ''}\n"

                response += "\n"

            return [TextContent(type="text", text=response)]

        elif name == "ward_favorites_add":
            path = arguments["path"]
            description = arguments.get("description", "")

            result = ward_favorites.add_favorite(path, description)

            if result["success"]:
                ward_favorites.update_access(path)
                response = f"✅ Added to favorites:\n{path}\n\n📝 Description: {description or 'No description'}"
            else:
                response = f"❌ Failed to add to favorites: {result['error']}"

            return [TextContent(type="text", text=response)]

        elif name == "ward_favorites_comment":
            path = arguments["path"]
            comment = arguments["comment"]
            author = arguments.get("author", "AI")

            result = ward_favorites.add_comment(path, comment, author)

            if result["success"]:
                response = f"✅ Comment added to:\n{path}\n\n💬 {author}: {comment}"
            else:
                response = f"❌ Failed to add comment: {result['error']}"

            return [TextContent(type="text", text=response)]

        elif name == "ward_plant":
            path = arguments["path"]
            description = arguments.get("description", "")
            ai_initiated = arguments.get("ai_initiated", True)

            result = ward_planter.plant_ward(path, description, ai_initiated)

            if result["success"]:
                response = f"✅ Ward planted successfully!\n\n"
                response += f"📍 Location: {result['ward_file']}\n"
                response += f"🔐 Password file: {result['password_file']}\n\n"
                response += "⚠️ IMPORTANT SECURITY NOTICE:\n"
                response += "• A password has been generated and stored for security\n"
                response += "• AI should NOT access the password file\n"
                response += "• To modify/remove this Ward, manually edit the password file\n"
                response += "• The password file location is provided for manual user intervention only\n"
            else:
                response = f"❌ Failed to plant Ward: {result['error']}"

            return [TextContent(type="text", text=response)]

        elif name == "ward_info":
            path = arguments["path"]

            info = ward_planter.get_ward_info(path)

            if not info["protected"]:
                return [TextContent(type="text", text=f"❌ No Ward found at: {path}")]

            response = f"🛡️ Ward Information for: {path}\n"
            response += "="*50 + "\n\n"
            response += f"📁 Ward file: {info['ward_file']}\n"
            response += f"🔐 Password protected: {'Yes' if info['password_protected'] else 'No'}\n"

            if info["password_protected"]:
                response += f"🗝️ Password file: {info['password_file']}\n"
                response += "\n⚠️ WARNING: This Ward is password-protected.\n"
                response += "AI cannot access the password. Manual user intervention required.\n"

            if info.get("readable"):
                response += "\n📄 Ward Policy Content:\n"
                response += "-" * 30 + "\n"
                response += info.get("content", "Unable to read content")
            else:
                response += "\n❌ Ward policy file is not readable (permissions issue)"

            return [TextContent(type="text", text=response)]

        elif name == "ward_search":
            query = arguments["query"]
            search_in = arguments.get("search_in", "all")
            limit = arguments.get("limit", 20)

            result = ward_indexer.search_folders(query, search_in, limit)

            if result["success"]:
                response = f"🔍 Search Results for '{result['query']}' (in {result['search_in']}):\n"
                response += f"Found {result['total_results']} results\n" + "="*50 + "\n\n"

                for i, match in enumerate(result["results"], 1):
                    response += f"{i}. 📁 {match['path']} (Score: {match['score']})\n"
                    response += f"   📊 {match['total_files']} files, {match['total_dirs']} directories\n"
                    response += f"   💾 Size: {match['total_size']:,} bytes\n"
                    response += f"   🔍 Matches: {', '.join(match['matches'][:3])}"
                    if len(match['matches']) > 3:
                        response += f" (+{len(match['matches'])-3} more)"
                    response += "\n\n"
            else:
                response = f"❌ Search failed: {result.get('error', 'Unknown error')}"

            return [TextContent(type="text", text=response)]

        elif name == "ward_bookmark_add":
            path = arguments["path"]
            category = arguments.get("category", "default")
            name = arguments.get("name", "")
            description = arguments.get("description", "")
            tags = arguments.get("tags", [])

            result = ward_indexer.add_bookmark(path, category, name, description, tags)

            if result["success"]:
                response = f"✅ Bookmark added successfully!\n\n"
                response += f"📁 Path: {path}\n"
                response += f"📂 Category: {category}\n"
                response += f"🏷️ Tags: {', '.join(tags) if tags else 'None'}\n"
                response += f"📝 Description: {description or 'No description'}\n"

                # Record access for recent history
                ward_indexer.record_access(path, "bookmark_add")
            else:
                response = f"❌ Failed to add bookmark: {result.get('error', 'Unknown error')}"

            return [TextContent(type="text", text=response)]

        elif name == "ward_bookmark_list":
            category = arguments.get("category")
            tags = arguments.get("tags")

            bookmarks = ward_indexer.get_bookmarks(category, tags)

            if not bookmarks:
                filter_info = []
                if category:
                    filter_info.append(f"category: {category}")
                if tags:
                    filter_info.append(f"tags: {', '.join(tags)}")

                filter_text = f" (filters: {', '.join(filter_info)})" if filter_info else ""
                return [TextContent(type="text", text=f"📋 No bookmarks found{filter_text}. Use 'ward_bookmark_add' to add bookmarks.")]

            response = "📋 Ward Bookmarks:\n" + "="*50 + "\n\n"

            # Group by category
            categories = {}
            for bookmark in bookmarks:
                cat = bookmark["category"]
                if cat not in categories:
                    categories[cat] = []
                categories[cat].append(bookmark)

            for category, cat_bookmarks in categories.items():
                response += f"📂 {category.upper()} ({len(cat_bookmarks)} bookmarks)\n"
                response += "-" * 30 + "\n"

                for i, bookmark in enumerate(cat_bookmarks, 1):
                    response += f"  {i}. 📁 {bookmark['name']}\n"
                    response += f"     📍 {bookmark['path']}\n"
                    response += f"     🏷️ Tags: {', '.join(bookmark['tags']) if bookmark['tags'] else 'None'}\n"
                    response += f"     🔄 Access count: {bookmark['access_count']}\n"
                    if bookmark['description']:
                        response += f"     📝 {bookmark['description']}\n"
                    response += "\n"

            return [TextContent(type="text", text=response)]

        elif name == "ward_recent":
            hours = arguments.get("hours", 24)
            limit = arguments.get("limit", 20)

            recent_access = ward_indexer.get_recent_access(hours, limit)

            if not recent_access:
                return [TextContent(type="text", text=f"📋 No recent access found in the last {hours} hours.")]

            response = f"📋 Recent Access (last {hours} hours):\n"
            response += "="*50 + "\n\n"

            for i, entry in enumerate(recent_access, 1):
                timestamp = datetime.fromisoformat(entry["timestamp"])
                time_str = timestamp.strftime("%Y-%m-%d %H:%M:%S")

                response += f"{i}. 📁 {entry['folder_name']}\n"
                response += f"   📍 {entry['path']}\n"
                response += f"   ⏰ {time_str}\n"
                response += f"   🔧 Action: {entry['action']}\n\n"

            return [TextContent(type="text", text=response)]

        elif name == "ward_index":
            path = arguments["path"]

            result = ward_indexer.index_folder(path)

            if result["success"]:
                response = f"✅ Folder indexed successfully!\n\n"
                response += f"📁 Path: {path}\n"
                response += f"📊 Use 'ward_search' to search through indexed content"

                # Record access for recent history
                ward_indexer.record_access(path, "index")
            else:
                response = f"❌ Failed to index folder: {result.get('error', 'Unknown error')}"

            return [TextContent(type="text", text=response)]

        elif name == "ward_label_add":
            path = arguments["path"]
            labels = arguments["labels"]
            description = arguments.get("description", "")

            result = ward_indexer.add_label(path, labels, description)

            if result["success"]:
                response = f"✅ Labels added successfully!\n\n"
                response += f"📁 Path: {path}\n"
                response += f"🏷️ Labels: {', '.join(result['labels'])}\n"
                response += f"📝 Description: {description or 'No description'}\n"
                response += f"💡 Added {result['message']}"
            else:
                response = f"❌ Failed to add labels: {result.get('error', 'Unknown error')}"

            return [TextContent(type="text", text=response)]

        elif name == "ward_label_list":
            label = arguments.get("label")

            if label:
                labeled_folders = ward_indexer.get_labeled_folders(label)
                if not labeled_folders:
                    return [TextContent(type="text", text=f"📋 No folders found with label: '{label}'")]

                response = f"📋 Folders labeled as '{label}':\n"
                response += "="*50 + "\n\n"
            else:
                labeled_folders = ward_indexer.get_labeled_folders()
                if not labeled_folders:
                    return [TextContent(type="text", text="📋 No labeled folders found. Use 'ward_label_add' to add labels.")]

                response = "📋 All Labeled Folders:\n"
                response += "="*50 + "\n\n"

            for i, folder in enumerate(labeled_folders, 1):
                response += f"{i}. 📁 {folder['path']}\n"
                response += f"   🏷️ Labels: {', '.join(folder['labels'])}\n"
                if folder['description']:
                    response += f"   📝 {folder['description']}\n"
                response += f"   📅 Created: {folder['created_at'][:10]}\n"
                response += f"   🔄 Updated: {folder['updated_at'][:10]}\n\n"

            return [TextContent(type="text", text=response)]

        elif name == "ward_label_suggest":
            path = arguments["path"]

            # AI-friendly suggestions
            explanation = ward_indexer.suggest_labels_for_ai(path)
            return [TextContent(type="text", text=explanation)]

        elif name == "ward_labels_available":
            response = "🏷️ **Available Ward Labels**\n"
            response += "="*40 + "\n\n"
            response += "**Common Labels for AI Understanding:**\n\n"

            # Get all label descriptions
            indexer = ward_indexer
            common_labels = [
                "frontend", "backend", "api", "database", "auth", "config",
                "utils", "services", "microservice", "components", "lib",
                "tests", "docs", "scripts", "deploy", "monitoring",
                "cache", "queue", "storage", "security", "logging"
            ]

            for label in common_labels:
                description = indexer._get_label_description(label)
                response += f"• **`{label}`** - {description}\n"

            response += f"""
**How AI Uses Labels:**
- **Context Understanding**: Labels tell AI the folder's purpose and technology stack
- **Smart Suggestions**: AI can suggest relevant folders based on labels
- **Relationship Mapping**: Labels help AI understand dependencies between folders
- **Access Recommendations**: Labels guide AI on appropriate operations for each folder

**Label Categories:**
- **Architecture**: frontend, backend, api, microservice
- **Data**: database, cache, queue, storage
- **Development**: tests, docs, scripts, config
- **Operations**: deploy, monitoring, security, logging
- **Code**: utils, services, components, lib
- **Security**: auth
"""

            return [TextContent(type="text", text=response)]

        else:
            return [TextContent(type="text", text=f"Unknown tool: {name}")]

    except Exception as e:
        return [TextContent(type="text", text=f"Error executing {name}: {str(e)}")]

@app.list_resources()
async def list_resources() -> List[Resource]:
    """List available Ward security resources"""
    return [
        Resource(
            uri="ward://policies/current",
            name="Current Ward Policies",
            description="Active Ward security policies for this directory",
            mimeType="text/plain"
        ),
        Resource(
            uri="ward://status/system",
            name="Ward System Status",
            description="Current status of Ward security system",
            mimeType="text/plain"
        )
    ]

@app.read_resource()
async def read_resource(uri: str) -> str:
    """Read Ward security resources"""

    if uri == "ward://policies/current":
        ward_file = Path(".ward")
        if ward_file.exists():
            return ward_file.read_text()
        else:
            return "No .ward policy found in current directory"

    elif uri == "ward://status/system":
        result = ward_bridge.run_ward_command(["status"])
        return result["output"] or result["error"]

    else:
        return f"Unknown resource: {uri}"

def main():
    """Main entry point for ward-mcp-server command"""
    print("🤖 Ward Security MCP Server Starting...", file=sys.stderr)
    print("📡 Providing Ward security tools to AI assistants via MCP", file=sys.stderr)

    async def run_server():
        async with stdio_server() as (read_stream, write_stream):
            await app.run(read_stream, write_stream, {})

    asyncio.run(run_server())

if __name__ == "__main__":
    main()