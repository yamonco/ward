#!/usr/bin/env python3
"""
Ward Configuration Parser and Manager
Handles .ward file parsing, including protected_folders functionality
"""

import os
import json
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime

@dataclass
class WardConfig:
    """Ward configuration data structure"""
    description: str = ""
    created: Optional[str] = None
    ai_initiated: bool = False
    password_protected: bool = False
    whitelist: List[str] = None
    blacklist: List[str] = None
    ai_guidance: bool = True
    protected_folders: List[str] = None
    shell: Optional[str] = None
    theme: Optional[str] = None
    allow_comments: bool = False
    max_comments: int = 5
    comment_prompt: str = ""
    ai_notes: str = ""

    def __post_init__(self):
        if self.whitelist is None:
            self.whitelist = []
        if self.blacklist is None:
            self.blacklist = []
        if self.protected_folders is None:
            self.protected_folders = []

class WardConfigParser:
    """Parser for .ward configuration files"""

    def __init__(self):
        pass

    def parse_file(self, ward_file_path: str) -> Optional[WardConfig]:
        """Parse .ward file and return WardConfig object"""
        try:
            with open(ward_file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            return self.parse_content(content)
        except (IOError, OSError, UnicodeDecodeError):
            return None

    def parse_content(self, content: str) -> WardConfig:
        """Parse .ward file content and return WardConfig object"""
        config = WardConfig()

        for line in content.split('\n'):
            line = line.strip()
            if not line or line.startswith('#'):
                continue

            if line.startswith('@description:'):
                config.description = line[13:].strip()
            elif line.startswith('@created:'):
                config.created = line[9:].strip()
            elif line.startswith('@ai_initiated:'):
                config.ai_initiated = line[14:].strip().lower() in ['true', 'yes', '1']
            elif line.startswith('@password_protected:'):
                config.password_protected = line[19:].strip().lower() in ['true', 'yes', '1']
            elif line.startswith('@whitelist:'):
                config.whitelist = [item.strip() for item in line[11:].split()]
            elif line.startswith('@blacklist:'):
                config.blacklist = [item.strip() for item in line[11:].split()]
            elif line.startswith('@ai_guidance:'):
                config.ai_guidance = line[13:].strip().lower() in ['true', 'yes', '1']
            elif line.startswith('@protected_folders:'):
                # Parse array format: services,mappers,repositories
                folders_str = line[19:].strip()
                if folders_str:
                    config.protected_folders = [item.strip() for item in folders_str.split(',')]
            elif line.startswith('@shell:'):
                config.shell = line[7:].strip()
            elif line.startswith('@theme:'):
                config.theme = line[7:].strip()
            elif line.startswith('@allow_comments:'):
                config.allow_comments = line[16:].strip().lower() in ['true', 'yes', '1']
            elif line.startswith('@max_comments:'):
                try:
                    config.max_comments = int(line[14:].strip())
                except ValueError:
                    config.max_comments = 5
            elif line.startswith('@comment_prompt:'):
                config.comment_prompt = line[15:].strip()
            elif line.startswith('@ai_notes:'):
                config.ai_notes = line[10:].strip()

        return config

    def generate_content(self, config: WardConfig) -> str:
        """Generate .ward file content from WardConfig object"""
        lines = []

        if config.description:
            lines.append(f"@description: {config.description}")
        if config.created:
            lines.append(f"@created: {config.created}")
        else:
            lines.append(f"@created: {datetime.now().isoformat()}")

        lines.append(f"@ai_initiated: {config.ai_initiated}")
        lines.append(f"@password_protected: {config.password_protected}")
        lines.append("")

        # Security policy
        if config.whitelist:
            lines.append(f"@whitelist: {' '.join(config.whitelist)}")
        if config.blacklist:
            lines.append(f"@blacklist: {' '.join(config.blacklist)}")

        lines.append(f"@ai_guidance: {config.ai_guidance}")
        lines.append("")

        # Protected folders (new feature)
        if config.protected_folders:
            lines.append(f"@protected_folders: {','.join(config.protected_folders)}")
            lines.append("")

        # Shell configuration
        if config.shell:
            lines.append(f"@shell: {config.shell}")
        if config.theme:
            lines.append(f"@theme: {config.theme}")

        # Comments configuration
        lines.append(f"@allow_comments: {config.allow_comments}")
        lines.append(f"@max_comments: {config.max_comments}")
        if config.comment_prompt:
            lines.append(f"@comment_prompt: {config.comment_prompt}")

        # AI notes
        if config.ai_notes:
            lines.append("")
            lines.append(f"# AI Operations Guidance")
            lines.append(f"@ai_notes: {config.ai_notes}")

        return '\n'.join(lines)

class FolderProtector:
    """Monitors and protects specified folders within a Ward-protected directory"""

    def __init__(self, base_path: str, protected_folders: List[str]):
        self.base_path = Path(base_path).resolve()
        self.protected_folders = protected_folders
        self.protected_paths = [
            (self.base_path / folder).resolve()
            for folder in protected_folders
        ]

    def is_protected_path(self, file_path: str) -> bool:
        """Check if a path is within any protected folder"""
        target_path = Path(file_path).resolve()

        # Check if target is exactly one of the protected paths
        if target_path in self.protected_paths:
            return True

        # Check if target is within any protected path
        for protected_path in self.protected_paths:
            try:
                if target_path.is_relative_to(protected_path):
                    return True
            except ValueError:
                # Path is on different drive (Windows) or not relative
                continue

        return False

    def get_protection_info(self, file_path: str) -> Dict[str, Any]:
        """Get protection information for a path"""
        target_path = Path(file_path).resolve()

        for folder_name, protected_path in zip(self.protected_folders, self.protected_paths):
            try:
                if target_path == protected_path:
                    return {
                        "protected": True,
                        "folder": folder_name,
                        "type": "direct_match",
                        "message": f"Direct match with protected folder: {folder_name}"
                    }
                elif target_path.is_relative_to(protected_path):
                    relative_path = target_path.relative_to(protected_path)
                    return {
                        "protected": True,
                        "folder": folder_name,
                        "type": "subfolder",
                        "relative_path": str(relative_path),
                        "message": f"Path is within protected folder: {folder_name}/{relative_path}"
                    }
            except ValueError:
                continue

        return {
            "protected": False,
            "message": "Path is not within any protected folder"
        }

    def get_all_protected_paths(self) -> List[str]:
        """Get list of all protected folder paths"""
        return [str(path) for path in self.protected_paths]

    def get_protection_summary(self) -> Dict[str, Any]:
        """Get summary of protection configuration"""
        return {
            "base_path": str(self.base_path),
            "protected_folders": self.protected_folders,
            "protected_paths": self.get_all_protected_paths(),
            "total_protected": len(self.protected_folders)
        }