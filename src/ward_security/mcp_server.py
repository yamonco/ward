#!/usr/bin/env python3
"""
Ward Security MCP Server
Provides Ward security features through Model Context Protocol (MCP)

This server enables AI assistants like Claude, Copilot, and ChatGPT
to interact with Ward security policies through standardized MCP interface.
"""

import asyncio
import json
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    from mcp.server import Server
    from mcp.server.stdio import stdio_server
    from mcp.types import Tool, Resource, TextContent, ImageContent
except ImportError:
    print("Error: MCP dependencies not installed. Please run: pip install mcp")
    sys.exit(1)

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
        else "No .ward policy found in current directory"

    elif uri == "ward://status/system":
        result = ward_bridge.run_ward_command(["status"])
        return result["output"] or result["error"]

    else:
        return f"Unknown resource: {uri}"

async def main():
    """Main MCP server entry point"""
    print("🤖 Ward Security MCP Server Starting...", file=sys.stderr)
    print("📡 Providing Ward security tools to AI assistants via MCP", file=sys.stderr)

    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream)

if __name__ == "__main__":
    asyncio.run(main())