#!/usr/bin/env python3
"""
Ward Favorites Management System
Provides bookmark/favorites functionality for Ward-protected directories
"""

import json
import os
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any
import hashlib
import secrets

class WardFavorites:
    """Manages Ward favorites with metadata and comments"""

    def __init__(self):
        self.favorites_file = Path.home() / ".ward" / "favorites.json"
        self.favorites_file.parent.mkdir(parents=True, exist_ok=True)
        self.favorites = self._load_favorites()

    def _load_favorites(self) -> Dict[str, Any]:
        """Load favorites from file"""
        if self.favorites_file.exists():
            try:
                with open(self.favorites_file, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                return {"favorites": {}, "metadata": {}}
        return {"favorites": {}, "metadata": {"created": datetime.now().isoformat()}}

    def _save_favorites(self) -> bool:
        """Save favorites to file"""
        try:
            self.favorites["metadata"]["last_updated"] = datetime.now().isoformat()
            with open(self.favorites_file, 'w') as f:
                json.dump(self.favorites, f, indent=2)
            return True
        except IOError:
            return False

    def _get_ward_status(self, path: str) -> Dict[str, Any]:
        """Get Ward protection status for a path"""
        ward_file = Path(path) / ".ward"
        if not ward_file.exists():
            return {"protected": False, "policy": None}

        try:
            with open(ward_file, 'r') as f:
                content = f.read()
                return {
                    "protected": True,
                    "policy": content.strip(),
                    "readable": True
                }
        except (IOError, PermissionError):
            return {"protected": True, "policy": None, "readable": False}

    def add_favorite(self, path: str, description: str = "") -> Dict[str, Any]:
        """Add a directory to favorites"""
        path = str(Path(path).resolve())

        if not Path(path).exists():
            return {"success": False, "error": "Path does not exist"}

        # Check if Ward is present in the directory
        ward_status = self._get_ward_status(path)
        if not ward_status["protected"]:
            return {"success": False, "error": "Directory is not Ward-protected"}

        # Add to favorites
        self.favorites["favorites"][path] = {
            "description": description,
            "added_date": datetime.now().isoformat(),
            "last_accessed": datetime.now().isoformat(),
            "comments": [],
            "ward_status": ward_status,
            "access_count": 0
        }

        if self._save_favorites():
            return {"success": True, "message": "Added to favorites"}
        else:
            return {"success": False, "error": "Failed to save favorites"}

    def get_favorites(self) -> List[Dict[str, Any]]:
        """Get all favorites with metadata"""
        favorites_list = []

        for path, data in self.favorites["favorites"].items():
            # Refresh ward status
            ward_status = self._get_ward_status(path)

            # Get recent comments (last 3)
            recent_comments = sorted(
                data["comments"],
                key=lambda x: x.get("timestamp", ""),
                reverse=True
            )[:3]

            favorites_list.append({
                "path": path,
                "description": data.get("description", ""),
                "added_date": data.get("added_date", ""),
                "last_accessed": data.get("last_accessed", ""),
                "access_count": data.get("access_count", 0),
                "ward_status": ward_status,
                "recent_comments": recent_comments,
                "exists": Path(path).exists()
            })

        # Sort by last accessed
        favorites_list.sort(
            key=lambda x: x["last_accessed"],
            reverse=True
        )

        return favorites_list

    def add_comment(self, path: str, comment: str, author: str = "AI") -> Dict[str, Any]:
        """Add a comment to a favorited directory"""
        path = str(Path(path).resolve())

        if path not in self.favorites["favorites"]:
            return {"success": False, "error": "Path not in favorites"}

        comment_data = {
            "comment": comment,
            "author": author,
            "timestamp": datetime.now().isoformat()
        }

        self.favorites["favorites"][path]["comments"].append(comment_data)

        if self._save_favorites():
            return {"success": True, "message": "Comment added"}
        else:
            return {"success": False, "error": "Failed to save comment"}

    def update_access(self, path: str) -> None:
        """Update access information for a favorite"""
        path = str(Path(path).resolve())

        if path in self.favorites["favorites"]:
            self.favorites["favorites"][path]["last_accessed"] = datetime.now().isoformat()
            self.favorites["favorites"][path]["access_count"] += 1
            self._save_favorites()


class WardPlanter:
    """Manages Ward planting with AI permission system"""

    def __init__(self):
        self.passwords_file = Path.home() / ".ward" / "ward_passwords.json"
        self.passwords_file.parent.mkdir(parents=True, exist_ok=True)
        self.passwords = self._load_passwords()

    def _load_passwords(self) -> Dict[str, str]:
        """Load Ward passwords"""
        if self.passwords_file.exists():
            try:
                with open(self.passwords_file, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                return {}
        return {}

    def _save_passwords(self) -> bool:
        """Save Ward passwords"""
        try:
            with open(self.passwords_file, 'w') as f:
                json.dump(self.passwords, f, indent=2)
            # Set restrictive permissions
            os.chmod(self.passwords_file, 0o600)
            return True
        except IOError:
            return False

    def generate_password(self) -> str:
        """Generate a random password for Ward"""
        return secrets.token_urlsafe(16)

    def plant_ward(self, path: str, description: str = "", ai_initiated: bool = False) -> Dict[str, Any]:
        """Plant a Ward in a directory with permission management"""
        path = Path(path).resolve()

        if not path.exists():
            return {"success": False, "error": "Path does not exist"}

        if not path.is_dir():
            return {"success": False, "error": "Path is not a directory"}

        # Check if Ward already exists
        existing_ward = path / ".ward"
        if existing_ward.exists():
            return {"success": False, "error": "Ward already exists in this directory"}

        # Generate password for security
        password = self.generate_password()
        self.passwords[str(path)] = password

        if not self._save_passwords():
            return {"success": False, "error": "Failed to save password"}

        # Create basic Ward configuration
        ward_config = f"""@description: {description or "Ward Security Policy"}
@created: {datetime.now().isoformat()}
@ai_initiated: {ai_initiated}
@password_protected: true

# Basic security policy
@whitelist: ls cat pwd echo grep
@blacklist: rm -rf sudo su chmod chown
@ai_guidance: true

# AI Operations Guidance
@ai_notes: This Ward is password-protected. To modify or remove, manually edit the password file at {self.passwords_file}
"""

        try:
            # Create .ward file
            with open(existing_ward, 'w') as f:
                f.write(ward_config)

            # Set restrictive permissions
            os.chmod(existing_ward, 0o600)

            return {
                "success": True,
                "message": "Ward planted successfully",
                "password_file": str(self.passwords_file),
                "ward_file": str(existing_ward),
                "warning": "Password file created. AI should NOT access the password. Manual user intervention required for removal."
            }

        except IOError as e:
            # Clean up password on failure
            if str(path) in self.passwords:
                del self.passwords[str(path)]
                self._save_passwords()
            return {"success": False, "error": f"Failed to create Ward: {str(e)}"}

    def get_ward_info(self, path: str) -> Dict[str, Any]:
        """Get Ward information including password protection status"""
        path = Path(path).resolve()
        ward_file = path / ".ward"

        if not ward_file.exists():
            return {"protected": False}

        has_password = str(path) in self.passwords

        try:
            with open(ward_file, 'r') as f:
                content = f.read()

            return {
                "protected": True,
                "password_protected": has_password,
                "password_file": str(self.passwords_file) if has_password else None,
                "ward_file": str(ward_file),
                "content": content
            }
        except (IOError, PermissionError):
            return {
                "protected": True,
                "password_protected": has_password,
                "password_file": str(self.passwords_file) if has_password else None,
                "ward_file": str(ward_file),
                "readable": False
            }


# Export for use in MCP server
__all__ = ['WardFavorites', 'WardPlanter']