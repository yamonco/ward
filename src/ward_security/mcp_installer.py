#!/usr/bin/env python3
"""
Ward MCP Installer - Easy installation of Ward MCP server for Claude Desktop

This module provides simple commands to install and configure Ward MCP server
for various AI assistants, especially Claude Desktop.
"""

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Dict, Any, Optional

try:
    import click
except ImportError:
    print("Error: click is required. Install with: pip install click")
    sys.exit(1)


class MCPInstaller:
    """Handles Ward MCP server installation and configuration"""

    def __init__(self):
        self.home_dir = Path.home()
        self.config_dir = self._get_config_dir()
        self.config_file = self.config_dir / "claude_desktop_config.json"

    def _get_config_dir(self, target: str = "claude-desktop") -> Path:
        """Get config directory based on platform and target"""
        system = sys.platform

        if target == "claude-desktop":
            if system == "darwin":  # macOS
                return self.home_dir / "Library" / "Application Support" / "Claude"
            elif system == "win32":  # Windows
                return self.home_dir / "AppData" / "Roaming" / "Claude"
            else:  # Linux and others
                return self.home_dir / ".config" / "Claude"

        elif target == "claude-code":
            # Claude Code uses VS Code's settings location
            if system == "darwin":  # macOS
                return self.home_dir / "Library" / "Application Support" / "Code" / "User"
            elif system == "win32":  # Windows
                return self.home_dir / "AppData" / "Roaming" / "Code" / "User"
            else:  # Linux and others
                return self.home_dir / ".config" / "Code" / "User"

        else:
            raise ValueError(f"Unknown target: {target}")

    def _get_ward_executable(self) -> Optional[Path]:
        """Find Ward MCP server executable"""
        # Try uvx installation first
        try:
            result = subprocess.run(
                ["uvx", "--help"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                # uvx is available, use it to run ward-mcp
                return None  # Will use uvx command directly
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass

        # Try local installation
        local_paths = [
            self.home_dir / ".local" / "bin" / "ward-mcp",
            Path.cwd() / "src" / "ward_security" / "mcp_server.py",
            self.home_dir / ".ward" / "mcp" / "mcp_server.py",
        ]

        for path in local_paths:
            if path.exists():
                return path

        return None

    def _create_config_backup(self, target: str = "claude-desktop") -> Optional[Path]:
        """Create backup of existing config"""
        config_file = self._get_config_file(target)
        if config_file.exists():
            backup_path = config_file.with_suffix(
                f".backup.{int(Path().absolute().stat().st_mtime)}"
            )
            shutil.copy2(config_file, backup_path)
            return backup_path
        return None

    def _get_config_file(self, target: str = "claude-desktop") -> Path:
        """Get config file path for target"""
        config_dir = self._get_config_dir(target)

        if target == "claude-desktop":
            return config_dir / "claude_desktop_config.json"
        elif target == "claude-code":
            return config_dir / "settings.json"
        else:
            raise ValueError(f"Unknown target: {target}")

    def _load_existing_config(self, target: str = "claude-desktop") -> Dict[str, Any]:
        """Load existing configuration"""
        config_file = self._get_config_file(target)

        if config_file.exists():
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                click.echo(f"Warning: Could not read existing config: {e}", err=True)
                return {}

        # Return default config structure
        if target == "claude-desktop":
            return {"mcpServers": {}}
        elif target == "claude-code":
            return {
                "mcp": {
                    "mcpServers": {},
                    "serverConnectors": {}
                }
            }
        else:
            return {}

    def _save_config(self, config: Dict[str, Any], target: str = "claude-desktop") -> bool:
        """Save configuration"""
        try:
            config_file = self._get_config_file(target)
            config_dir = config_file.parent

            # Create config directory if it doesn't exist
            config_dir.mkdir(parents=True, exist_ok=True)

            # Ensure appropriate keys exist
            if target == "claude-desktop":
                if "mcpServers" not in config:
                    config["mcpServers"] = {}
            elif target == "claude-code":
                if "mcp" not in config:
                    config["mcp"] = {}
                if "mcpServers" not in config["mcp"]:
                    config["mcp"]["mcpServers"] = {}
                if "serverConnectors" not in config["mcp"]:
                    config["mcp"]["serverConnectors"] = {}

            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)

            return True
        except (IOError, OSError) as e:
            click.echo(f"Error: Could not save config: {e}", err=True)
            return False

    def add_ward_mcp_server(self, target: str = "claude-desktop", use_uvx: bool = True) -> bool:
        """Add Ward MCP server to configuration"""
        target_name = "Claude Desktop" if target == "claude-desktop" else "Claude Code"

        # Create backup
        backup_path = self._create_config_backup(target)
        if backup_path:
            click.echo(f"✓ Backed up existing {target_name} config to: {backup_path}")

        # Load existing config
        config = self._load_existing_config(target)

        # Choose execution method based on installation type
        if use_uvx:
            # UVX method (temporary/on-demand)
            executable_command = ["uvx", "git+https://github.com/yamonco/ward.git", "ward-mcp-server"]
            click.echo("⚡ Using UVX method (temporary, on-demand)")
            click.echo("💡 Benefits: No installation required, always latest version")
        else:
            # UV method (permanent installation)
            executable_command = ["ward-mcp-server"]
            click.echo("🔧 Using UV method (permanent installation)")
            click.echo("💡 Benefits: Fast execution, persistent across sessions")

        # Add Ward server configuration
        ward_config = {
            "command": executable_command[0],
            "args": executable_command[1:] if len(executable_command) > 1 else [],
            "description": "Ward Security System - AI-powered terminal protection"
        }

        if target == "claude-desktop":
            config["mcpServers"]["ward-security"] = ward_config
        elif target == "claude-code":
            # VS Code uses nested structure, need to handle missing keys
            if "mcp" not in config:
                config["mcp"] = {}
            if "mcpServers" not in config["mcp"]:
                config["mcp"]["mcpServers"] = {}
            config["mcp"]["mcpServers"]["ward-security"] = ward_config

        # Save configuration
        config_file = self._get_config_file(target)
        if self._save_config(config, target):
            click.echo(f"✅ Ward MCP server added to {target_name}!")
            click.echo(f"📁 Configuration saved to: {config_file}")
            click.echo()

            if target == "claude-desktop":
                click.echo("🔄 Restart Claude Desktop to activate Ward integration")
            else:
                click.echo("🔄 Restart VS Code/Claude Code to activate Ward integration")
                click.echo("💡 Make sure the MCP extension is installed and enabled")

            click.echo()
            click.echo("🎯 Available Ward tools in Claude:")
            click.echo("  • ward_check - Check security policies")
            click.echo("  • ward_plant - Plant protection")
            click.echo("  • ward_favorites_* - Manage favorites")
            click.echo("  • ward_search - Search folders")
            click.echo("  • ward_bookmark_* - Manage bookmarks")
            click.echo("  • ward_label_* - AI labeling system")
            click.echo("  • And more...")
            return True

        return False

    def remove_ward_mcp_server(self, target: str = "claude-desktop") -> bool:
        """Remove Ward MCP server from configuration"""
        config_file = self._get_config_file(target)
        target_name = "Claude Desktop" if target == "claude-desktop" else "Claude Code"

        if not config_file.exists():
            click.echo(f"No {target_name} configuration found")
            return False

        # Create backup
        backup_path = self._create_config_backup(target)
        if backup_path:
            click.echo(f"✓ Backed up existing config to: {backup_path}")

        # Load and modify config
        config = self._load_existing_config(target)

        if target == "claude-desktop":
            key_path = "mcpServers"
        else:
            key_path = "mcp.mcpServers"

        # Navigate to the nested key
        keys = key_path.split(".")
        current = config
        for key in keys:
            if key not in current:
                current = {}
                break
            current = current[key]

        if "ward-security" in current:
            del current["ward-security"]

            # Rebuild nested structure
            keys = key_path.split(".")
            final_config = config
            for i, key in enumerate(keys):
                if i == len(keys) - 1:
                    final_config[key] = current
                else:
                    final_config = final_config.setdefault(key, {})

            if self._save_config(config, target):
                click.echo(f"✅ Ward MCP server removed from {target_name}")
                if target == "claude-desktop":
                    click.echo("🔄 Restart Claude Desktop to apply changes")
                else:
                    click.echo("🔄 Restart VS Code/Claude Code to apply changes")
                return True
            else:
                click.echo("❌ Failed to save configuration", err=True)
                return False
        else:
            click.echo(f"ℹ️ Ward MCP server not found in {target_name} configuration")
            return False

    def print_status_for_target(self, target: str):
        """Print status for specific target"""
        target_name = "Claude Desktop" if target == "claude-desktop" else "Claude Code"
        config_file = self._get_config_file(target)

        # Configuration status
        if config_file.exists():
            click.echo("✅ Configuration found")
            click.echo(f"   📍 {config_file}")
            config = self._load_existing_config(target)

            if target == "claude-desktop":
                ward_configured = "ward-security" in config.get("mcpServers", {})
            else:
                # Check nested structure for Claude Code
                mcp_config = config.get("mcp", {})
                mcp_servers = mcp_config.get("mcpServers", {})
                ward_configured = "ward-security" in mcp_servers

            if ward_configured:
                click.echo("✅ Ward MCP server is configured")
            else:
                click.echo("❌ Ward MCP server not configured")
        else:
            click.echo("❌ Configuration not found")
            click.echo(f"   Expected at: {config_file}")

        # Show recommendations if not configured
        if not config_file.exists() or not self._is_configured(target):
            click.echo()
            click.echo(f"💡 Add Ward to {target_name}:")
            click.echo(f"   ward-mcp add --target {target}")

    def _is_configured(self, target: str) -> bool:
        """Check if Ward is configured for target"""
        config = self._load_existing_config(target)

        if target == "claude-desktop":
            return "ward-security" in config.get("mcpServers", {})
        elif target == "claude-code":
            # Check nested structure
            mcp_config = config.get("mcp", {})
            mcp_servers = mcp_config.get("mcpServers", {})
            return "ward-security" in mcp_servers
        return False

    def check_installation(self) -> Dict[str, Any]:
        """Check Ward MCP installation status"""
        status = {
            "claude_config_exists": self.config_file.exists(),
            "ward_in_config": False,
            "ward_executable_found": False,
            "uvx_available": False,
            "ward_version": None
        }

        # Check uvx availability
        try:
            subprocess.run(["uvx", "--help"], capture_output=True, timeout=5)
            status["uvx_available"] = True
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass

        # Check Ward executable
        ward_executable = self._get_ward_executable()
        status["ward_executable_found"] = ward_executable is not None

        # Check configuration
        if status["claude_config_exists"]:
            config = self._load_existing_config()
            status["ward_in_config"] = "ward-security" in config.get("mcpServers", {})

        # Get Ward version if available
        try:
            result = subprocess.run(
                ["uvx", "ward-security", "--version"] if status["uvx_available"] else ["ward", "--version"],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                status["ward_version"] = result.stdout.strip()
        except Exception:
            pass

        return status

    def print_status(self):
        """Print detailed installation status"""
        status = self.check_installation()

        click.echo("🔍 Ward MCP Installation Status")
        click.echo("=" * 40)

        # Claude Desktop config
        if status["claude_config_exists"]:
            click.echo("✅ Claude Desktop configuration found")
            click.echo(f"   📍 {self.config_file}")
            if status["ward_in_config"]:
                click.echo("✅ Ward MCP server is configured")
            else:
                click.echo("❌ Ward MCP server not configured")
        else:
            click.echo("❌ Claude Desktop configuration not found")
            click.echo(f"   Expected at: {self.config_file}")

        # UVX availability
        if status["uvx_available"]:
            click.echo("✅ UVX package runner available")
        else:
            click.echo("❌ UVX not found (install with: pip install uv)")

        # Ward installation
        if status["ward_executable_found"]:
            click.echo("✅ Ward executable found")
        else:
            click.echo("❌ Ward executable not found")

        # Version info
        if status["ward_version"]:
            click.echo(f"📦 Ward version: {status['ward_version']}")

        # Recommendations
        click.echo()
        click.echo("💡 Recommendations:")

        if not status["uvx_available"]:
            click.echo("   • Install UVX: pip install uv")

        if not status["ward_in_config"]:
            click.echo("   • Add Ward to Claude: ward-mcp add")

        if status["ward_in_config"] and status["claude_config_exists"]:
            click.echo("   • Restart Claude Desktop to activate")


@click.group()
@click.version_option(version="2.0.0", prog_name="ward-mcp")
def cli():
    """Ward MCP Installer - Easy Claude Desktop integration"""
    pass


@cli.command()
@click.option('--target', type=click.Choice(['claude-desktop', 'claude-code']),
              default='claude-desktop', help='Target application for MCP integration')
@click.option('--method', type=click.Choice(['uvx', 'uv']),
              default='uvx', help='Installation method: uvx (temporary) or uv (permanent)')
def add(target, method):
    """Add Ward MCP server to Claude Desktop or Claude Code"""
    installer = MCPInstaller()
    target_name = "Claude Desktop" if target == "claude-desktop" else "Claude Code"
    use_uvx = (method == 'uvx')

    click.echo(f"🚀 Adding Ward MCP server to {target_name} using {method.upper()} method...")

    if installer.add_ward_mcp_server(target=target, use_uvx=use_uvx):
        click.echo()
        click.echo("🎉 Installation completed successfully!")
    else:
        click.echo()
        click.echo("❌ Installation failed", err=True)
        sys.exit(1)


@cli.command()
@click.option('--target', type=click.Choice(['claude-desktop', 'claude-code']),
              default='claude-desktop', help='Target application for MCP integration')
def remove(target):
    """Remove Ward MCP server from Claude Desktop or Claude Code"""
    installer = MCPInstaller()
    target_name = "Claude Desktop" if target == "claude-desktop" else "Claude Code"

    click.echo(f"🗑️  Removing Ward MCP server from {target_name}...")

    if installer.remove_ward_mcp_server(target=target):
        click.echo()
        click.echo("🎉 Removal completed successfully!")
    else:
        click.echo()
        click.echo("❌ Removal failed", err=True)
        sys.exit(1)


@cli.command()
@click.option('--target', type=click.Choice(['claude-desktop', 'claude-code', 'all']),
              default='all', help='Check specific target or all')
def status(target):
    """Check Ward MCP installation status"""
    installer = MCPInstaller()

    if target == 'all':
        # Check both Claude Desktop and Claude Code
        click.echo("🔍 Ward MCP Installation Status")
        click.echo("=" * 40)

        for t in ['claude-desktop', 'claude-code']:
            click.echo(f"\n📱 {t.replace('-', ' ').title()}:")
            installer.print_status_for_target(t)
    else:
        installer.print_status_for_target(target)


@cli.command()
@click.option('--target', type=click.Choice(['claude-desktop', 'claude-code', 'all']),
              default='all', help='Target for MCP integration')
def install(target):
    """Complete Ward installation with MCP support"""
    click.echo("🛡️  Ward Security System - Complete Installation")
    click.echo("=" * 50)

    # Install Ward with MCP support using UVX
    try:
        click.echo("📦 Installing Ward with MCP support...")
        subprocess.run([
            "pip", "install", "git+https://github.com/yamonco/ward.git"
        ], check=True)

        click.echo("✅ Ward installed successfully!")
        click.echo()

        installer = MCPInstaller()

        # Add to specified targets
        if target == 'all':
            targets = ['claude-desktop', 'claude-code']
        else:
            targets = [target]

        for t in targets:
            target_name = "Claude Desktop" if t == "claude-desktop" else "Claude Code"
            click.echo(f"🔧 Adding Ward MCP server to {target_name}...")

            if installer.add_ward_mcp_server(use_uvx=True, target=t):
                click.echo(f"✅ Added to {target_name}")
            else:
                click.echo(f"⚠️  Failed to add to {target_name}", err=True)

        click.echo()
        click.echo("🎉 Installation completed!")
        click.echo()
        click.echo("🔄 Next steps:")

        if 'claude-desktop' in targets:
            click.echo("1. Restart Claude Desktop")

        if 'claude-code' in targets:
            click.echo("2. Restart VS Code/Claude Code")
            click.echo("3. Ensure MCP extension is enabled in VS Code")

        click.echo("4. Start using Ward tools in Claude conversations")
        click.echo("5. Try: 'ward_check my-project-directory'")

    except subprocess.CalledProcessError as e:
        click.echo(f"❌ Installation failed: {e}", err=True)
        sys.exit(1)


@cli.command()
def info():
    """Show Ward MCP server information"""
    click.echo("🤖 Ward MCP Server Information")
    click.echo("=" * 40)

    click.echo("📋 Available Tools:")
    tools = [
        "ward_check - Check security policies for paths",
        "ward_plant - Plant Ward protection with password",
        "ward_favorites_list - List favorite directories",
        "ward_favorites_add - Add directory to favorites",
        "ward_favorites_comment - Add comments to favorites",
        "ward_search - Search through indexed folders",
        "ward_bookmark_add - Add folder to bookmarks",
        "ward_bookmark_list - List bookmarks",
        "ward_recent - Show recent access",
        "ward_index - Index folder for search",
        "ward_label_add - Add AI-friendly labels",
        "ward_label_list - List labeled folders",
        "ward_label_suggest - Get AI label suggestions",
        "ward_labels_available - Show all available labels"
    ]

    for tool in tools:
        click.echo(f"  • {tool}")

    click.echo()
    click.echo("🔗 Integration:")
    click.echo("  • Claude Desktop - Automatic configuration")
    click.echo("  • Claude Code - VS Code integration with MCP extension")
    click.echo("  • Other AI assistants - stdio MCP protocol")

    click.echo()
    click.echo("📦 Installation:")
    click.echo("  • Quick install: ward-mcp install")
    click.echo("  • Add to Claude Desktop: ward-mcp add --target claude-desktop")
    click.echo("  • Add to Claude Code: ward-mcp add --target claude-code")
    click.echo("  • Check status: ward-mcp status --target all")

    click.echo()
    click.echo("🔧 Claude Code Setup:")
    click.echo("  1. Install MCP extension in VS Code")
    click.echo("  2. Run: ward-mcp add --target claude-code")
    click.echo("  3. Restart VS Code")
    click.echo("  4. Enable MCP extension in settings")


def main():
    """Main entry point for ward-mcp command"""
    cli()


if __name__ == "__main__":
    main()