#!/usr/bin/env python3
"""
Ward Folder Indexing System
Provides search, bookmark, and recent access functionality for Ward-protected folders
"""

import json
import os
import re
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import fnmatch

class WardIndexer:
    """Advanced folder indexing system for Ward"""

    def __init__(self):
        self.index_file = Path.home() / ".ward" / "folder_index.json"
        self.bookmarks_file = Path.home() / ".ward" / "bookmarks.json"
        self.recent_file = Path.home() / ".ward" / "recent_access.json"

        # Ensure directories exist
        self.index_file.parent.mkdir(parents=True, exist_ok=True)

        # Load existing data
        self.index_data = self._load_index()
        self.bookmarks_data = self._load_bookmarks()
        self.recent_data = self._load_recent()

    def _load_index(self) -> Dict[str, Any]:
        """Load folder index data"""
        if self.index_file.exists():
            try:
                with open(self.index_file, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                pass
        return {"folders": {}, "last_updated": None}

    def _save_index(self) -> bool:
        """Save folder index data"""
        try:
            self.index_data["last_updated"] = datetime.now().isoformat()
            with open(self.index_file, 'w') as f:
                json.dump(self.index_data, f, indent=2)
            return True
        except IOError:
            return False

    def _load_bookmarks(self) -> Dict[str, Any]:
        """Load bookmarks data"""
        if self.bookmarks_file.exists():
            try:
                with open(self.bookmarks_file, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                pass
        return {"categories": {}, "bookmarks": {}}

    def _save_bookmarks(self) -> bool:
        """Save bookmarks data"""
        try:
            with open(self.bookmarks_file, 'w') as f:
                json.dump(self.bookmarks_data, f, indent=2)
            return True
        except IOError:
            return False

    def _load_recent(self) -> Dict[str, Any]:
        """Load recent access data"""
        if self.recent_file.exists():
            try:
                with open(self.recent_file, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                pass
        return {"access_log": []}

    def _save_recent(self) -> bool:
        """Save recent access data"""
        try:
            # Keep only last 1000 entries
            if len(self.recent_data["access_log"]) > 1000:
                self.recent_data["access_log"] = self.recent_data["access_log"][-1000:]

            with open(self.recent_file, 'w') as f:
                json.dump(self.recent_data, f, indent=2)
            return True
        except IOError:
            return False

    def _is_ward_folder(self, path: Path) -> bool:
        """Check if directory has Ward protection"""
        ward_file = path / ".ward"
        return ward_file.exists() and ward_file.is_file()

    def _scan_folder_content(self, path: Path) -> Dict[str, Any]:
        """Scan folder content for indexing"""
        content_info = {
            "files": [],
            "directories": [],
            "file_types": {},
            "total_size": 0,
            "last_modified": None
        }

        try:
            last_modified = 0
            for item in path.iterdir():
                if item.name.startswith('.'):
                    continue

                if item.is_file():
                    file_info = {
                        "name": item.name,
                        "size": item.stat().st_size,
                        "modified": datetime.fromtimestamp(item.stat().st_mtime).isoformat(),
                        "extension": item.suffix.lower()
                    }
                    content_info["files"].append(file_info)
                    content_info["total_size"] += file_info["size"]

                    # Track file types
                    ext = item.suffix.lower()
                    content_info["file_types"][ext] = content_info["file_types"].get(ext, 0) + 1

                    mod_time = item.stat().st_mtime
                    if mod_time > last_modified:
                        last_modified = mod_time

                elif item.is_dir():
                    dir_info = {
                        "name": item.name,
                        "modified": datetime.fromtimestamp(item.stat().st_mtime).isoformat()
                    }
                    content_info["directories"].append(dir_info)

                    mod_time = item.stat().st_mtime
                    if mod_time > last_modified:
                        last_modified = mod_time

            if last_modified > 0:
                content_info["last_modified"] = datetime.fromtimestamp(last_modified).isoformat()

        except (PermissionError, OSError):
            pass

        return content_info

    def index_folder(self, path: str) -> Dict[str, Any]:
        """Index a Ward-protected folder"""
        path = str(Path(path).resolve())

        if not self._is_ward_folder(Path(path)):
            return {"success": False, "error": "Directory is not Ward-protected"}

        folder_content = self._scan_folder_content(Path(path))

        self.index_data["folders"][path] = {
            "indexed_at": datetime.now().isoformat(),
            "content": folder_content
        }

        if self._save_index():
            return {"success": True, "message": "Folder indexed successfully"}
        else:
            return {"success": False, "error": "Failed to save index"}

    def search_folders(self, query: str, search_in: str = "all", limit: int = 20) -> Dict[str, Any]:
        """Search through indexed Ward folders"""
        results = []
        query_lower = query.lower()

        for folder_path, folder_data in self.index_data["folders"].items():
            score = 0
            match_info = {
                "path": folder_path,
                "indexed_at": folder_data["indexed_at"],
                "matches": []
            }

            folder_name = Path(folder_path).name.lower()
            content = folder_data["content"]

            # Search in folder name
            if search_in in ["all", "name"]:
                if query_lower in folder_name:
                    score += 10
                    match_info["matches"].append(f"Folder name: {Path(folder_path).name}")

            # Search in file names
            if search_in in ["all", "files"]:
                for file_info in content["files"]:
                    if query_lower in file_info["name"].lower():
                        score += 5
                        match_info["matches"].append(f"File: {file_info['name']}")

            # Search in file extensions
            if search_in in ["all", "types"]:
                if query_lower.startswith('.'):
                    query_ext = query_lower
                else:
                    query_ext = f".{query_lower}"

                if query_ext in content["file_types"]:
                    score += 3
                    match_info["matches"].append(f"File type: {query_ext} ({content['file_types'][query_ext]} files)")

            # Search in directory names
            if search_in in ["all", "directories"]:
                for dir_info in content["directories"]:
                    if query_lower in dir_info["name"].lower():
                        score += 4
                        match_info["matches"].append(f"Directory: {dir_info['name']}")

            if score > 0:
                match_info["score"] = score
                match_info["total_files"] = len(content["files"])
                match_info["total_dirs"] = len(content["directories"])
                match_info["total_size"] = content["total_size"]
                results.append(match_info)

        # Sort by score (descending)
        results.sort(key=lambda x: x["score"], reverse=True)

        # Limit results
        results = results[:limit]

        return {
            "success": True,
            "query": query,
            "search_in": search_in,
            "total_results": len(results),
            "results": results
        }

    def add_bookmark(self, path: str, category: str = "default", name: str = None, description: str = "", tags: List[str] = None) -> Dict[str, Any]:
        """Add a folder to bookmarks with categorization"""
        path = str(Path(path).resolve())

        if not self._is_ward_folder(Path(path)):
            return {"success": False, "error": "Directory is not Ward-protected"}

        bookmark_name = name or Path(path).name
        bookmark_data = {
            "path": path,
            "name": bookmark_name,
            "description": description,
            "category": category,
            "tags": tags or [],
            "created_at": datetime.now().isoformat(),
            "access_count": 0
        }

        # Add to bookmarks
        bookmark_id = f"{category}_{bookmark_name}".replace(" ", "_").lower()
        self.bookmarks_data["bookmarks"][bookmark_id] = bookmark_data

        # Add to category
        if category not in self.bookmarks_data["categories"]:
            self.bookmarks_data["categories"][category] = []
        if bookmark_id not in self.bookmarks_data["categories"][category]:
            self.bookmarks_data["categories"][category].append(bookmark_id)

        if self._save_bookmarks():
            return {"success": True, "message": "Bookmark added", "id": bookmark_id}
        else:
            return {"success": False, "error": "Failed to save bookmark"}

    def get_bookmarks(self, category: str = None, tags: List[str] = None) -> List[Dict[str, Any]]:
        """Get bookmarks with optional filtering"""
        bookmarks = []

        for bookmark_id, bookmark_data in self.bookmarks_data["bookmarks"].items():
            # Filter by category
            if category and bookmark_data["category"] != category:
                continue

            # Filter by tags
            if tags:
                bookmark_tags = set(bookmark_data["tags"])
                required_tags = set(tags)
                if not required_tags.issubset(bookmark_tags):
                    continue

            bookmarks.append({
                "id": bookmark_id,
                **bookmark_data
            })

        # Sort by creation date (newest first)
        bookmarks.sort(key=lambda x: x["created_at"], reverse=True)
        return bookmarks

    def get_categories(self) -> List[str]:
        """Get all bookmark categories"""
        return list(self.bookmarks_data["categories"].keys())

    def record_access(self, path: str, action: str = "access") -> None:
        """Record folder access for recent history"""
        path = str(Path(path).resolve())

        access_entry = {
            "path": path,
            "action": action,
            "timestamp": datetime.now().isoformat(),
            "folder_name": Path(path).name
        }

        # Add to access log
        self.recent_data["access_log"].append(access_entry)

        # Update access count in bookmarks if exists
        for bookmark_id, bookmark_data in self.bookmarks_data["bookmarks"].items():
            if bookmark_data["path"] == path:
                bookmark_data["access_count"] += 1
                break

        self._save_recent()
        self._save_bookmarks()

    def get_recent_access(self, hours: int = 24, limit: int = 20) -> List[Dict[str, Any]]:
        """Get recent access history"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        recent_entries = []

        for entry in reversed(self.recent_data["access_log"]):  # Start from newest
            entry_time = datetime.fromisoformat(entry["timestamp"])

            if entry_time < cutoff_time:
                break  # Too old, stop processing

            # Check if folder still has Ward
            if self._is_ward_folder(Path(entry["path"])):
                recent_entries.append(entry)

            if len(recent_entries) >= limit:
                break

        return recent_entries

    def get_folder_stats(self, path: str) -> Dict[str, Any]:
        """Get statistics for a specific folder"""
        path = str(Path(path).resolve())

        if not self._is_ward_folder(Path(path)):
            return {"error": "Directory is not Ward-protected"}

        # Check if indexed
        if path not in self.index_data["folders"]:
            # Auto-index if not found
            self.index_folder(path)

        if path in self.index_data["folders"]:
            content = self.index_data["folders"][path]["content"]
            return {
                "path": path,
                "total_files": len(content["files"]),
                "total_directories": len(content["directories"]),
                "total_size": content["total_size"],
                "file_types": content["file_types"],
                "last_modified": content["last_modified"],
                "indexed_at": self.index_data["folders"][path]["indexed_at"]
            }
        else:
            return {"error": "Failed to index folder"}

    def add_label(self, path: str, labels: List[str], description: str = "") -> Dict[str, Any]:
        """Add labels to a Ward-protected folder"""
        path = str(Path(path).resolve())

        if not self._is_ward_folder(Path(path)):
            return {"success": False, "error": "Directory is not Ward-protected"}

        if "labels" not in self.index_data:
            self.index_data["labels"] = {}

        # Initialize folder labels if not exists
        if path not in self.index_data["labels"]:
            self.index_data["labels"][path] = {
                "labels": [],
                "description": "",
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
                "ai_suggested": False
            }

        # Add new labels (avoid duplicates)
        existing_labels = set(self.index_data["labels"][path]["labels"])
        new_labels = [label for label in labels if label not in existing_labels]
        self.index_data["labels"][path]["labels"].extend(new_labels)

        if description:
            self.index_data["labels"][path]["description"] = description

        self.index_data["labels"][path]["updated_at"] = datetime.now().isoformat()

        if self._save_index():
            return {
                "success": True,
                "message": f"Added {len(new_labels)} new labels",
                "labels": self.index_data["labels"][path]["labels"]
            }
        else:
            return {"success": False, "error": "Failed to save labels"}

    def get_labeled_folders(self, label: str = None) -> List[Dict[str, Any]]:
        """Get folders with specific label or all labeled folders"""
        if "labels" not in self.index_data:
            return []

        labeled_folders = []
        for path, label_data in self.index_data["labels"].items():
            if label:
                if label in label_data["labels"]:
                    labeled_folders.append({
                        "path": path,
                        "labels": label_data["labels"],
                        "description": label_data.get("description", ""),
                        "created_at": label_data["created_at"],
                        "updated_at": label_data["updated_at"]
                    })
            else:
                labeled_folders.append({
                    "path": path,
                    "labels": label_data["labels"],
                    "description": label_data.get("description", ""),
                    "created_at": label_data["created_at"],
                    "updated_at": label_data["updated_at"]
                })

        return labeled_folders

    def get_label_suggestions(self, folder_path: str = None) -> Dict[str, Any]:
        """AI-friendly label suggestions based on folder content and naming"""
        suggestions = {
            "common_labels": [
                "frontend", "backend", "api", "database", "auth", "config",
                "utils", "services", "microservice", "components", "lib",
                "tests", "docs", "scripts", "deploy", "monitoring",
                "cache", "queue", "storage", "security", "logging"
            ],
            "semantic_patterns": {
                "frontend": ["react", "vue", "angular", "svelte", "ui", "css", "scss"],
                "backend": ["api", "server", "routes", "controllers", "services"],
                "database": ["models", "schema", "migration", "seeds", "queries"],
                "auth": ["jwt", "oauth", "login", "register", "session", "passport"],
                "config": ["env", "settings", "constants", "webpack", "babel"],
                "utils": ["helper", "common", "shared", "core", "base"],
                "tests": ["spec", "test", "mock", "fixture", "coverage"]
            }
        }

        if folder_path and folder_path in self.index_data["folders"]:
            content = self.index_data["folders"][folder_path]["content"]
            folder_name = Path(folder_path).name.lower()

            # Analyze folder content for suggestions
            file_names = [f["name"].lower() for f in content["files"]]
            file_extensions = [f["extension"] for f in content["files"]]

            suggested_labels = []

            # Pattern-based suggestions
            for label, patterns in suggestions["semantic_patterns"].items():
                if any(pattern in folder_name for pattern in patterns):
                    suggested_labels.append(label)
                elif any(any(pattern in fname for pattern in patterns) for fname in file_names):
                    suggested_labels.append(label)

            # File type based suggestions
            if ".js" in file_extensions or ".ts" in file_extensions:
                if "package.json" in file_names:
                    suggested_labels.append("nodejs")
                if any("react" in fname or "vue" in fname or "angular" in fname for fname in file_names):
                    suggested_labels.append("frontend")

            if ".py" in file_extensions:
                suggested_labels.append("python")
                if "requirements.txt" in file_names or "setup.py" in file_names:
                    suggested_labels.append("python-project")

            if ".go" in file_extensions:
                suggested_labels.append("golang")
            if ".rs" in file_extensions:
                suggested_labels.append("rust")

            # Remove duplicates and prioritize
            suggestions["ai_suggested"] = list(dict.fromkeys(suggested_labels))[:10]

        return suggestions

    def suggest_labels_for_ai(self, folder_path: str) -> str:
        """AI-friendly explanation of label suggestions"""
        suggestions = self.get_label_suggestions(folder_path)
        folder_name = Path(folder_path).name

        explanation = f"""
🏷️ **AI Label Suggestions for '{folder_name}'**

**Recommended Labels (AI-detected patterns):**
"""

        if "ai_suggested" in suggestions:
            for label in suggestions["ai_suggested"]:
                explanation += f"• `{label}` - Automatically detected based on folder content\n"

        explanation += f"""
**Common Labels You Can Use:**
"""

        common_labels = suggestions["common_labels"]
        for i, label in enumerate(common_labels, 1):
            if i <= 10:  # Show first 10
                explanation += f"• `{label}` - {self._get_label_description(label)}\n"

        explanation += f"""
**How to Add Labels:**
Use: `ward_label_add --path '{folder_path}' --labels "label1,label2" --description "Purpose"`

**Labels help AI understand:**
- Folder purpose and context
- Technology stack being used
- Relationship to other folders
- Recommended access patterns
"""

        return explanation

    def _get_label_description(self, label: str) -> str:
        """Get human-readable description for a label"""
        descriptions = {
            "frontend": "User interface and client-side code",
            "backend": "Server-side logic and APIs",
            "api": "REST/GraphQL API endpoints",
            "database": "Data persistence and models",
            "auth": "Authentication and authorization",
            "config": "Configuration and settings",
            "utils": "Utility functions and helpers",
            "services": "Business logic services",
            "microservice": "Independent deployable service",
            "components": "Reusable UI components",
            "lib": "Shared libraries and dependencies",
            "tests": "Unit and integration tests",
            "docs": "Documentation and guides",
            "scripts": "Build and automation scripts",
            "deploy": "Deployment configurations",
            "monitoring": "Logging and monitoring tools",
            "cache": "Caching and performance",
            "queue": "Message queues and jobs",
            "storage": "File and blob storage",
            "security": "Security policies and tools",
            "logging": "Application logging"
        }
        return descriptions.get(label, "Custom label for categorization")

    def cleanup_old_data(self, days: int = 30) -> None:
        """Clean up old index data and access logs"""
        cutoff_date = datetime.now() - timedelta(days=days)
        cutoff_iso = cutoff_date.isoformat()

        # Clean recent access log
        self.recent_data["access_log"] = [
            entry for entry in self.recent_data["access_log"]
            if entry["timestamp"] > cutoff_iso
        ]

        self._save_recent()

# Export for use in MCP server
__all__ = ['WardIndexer']