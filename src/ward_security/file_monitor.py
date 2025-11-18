#!/usr/bin/env python3
"""
File System Monitor for Ward Protection
Monitors file system operations and enforces protection rules
"""

import os
import time
import threading
from pathlib import Path
from typing import Dict, Set, Optional, Callable
from dataclasses import dataclass
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileSystemEvent

from .ward_config import WardConfigParser, FolderProtector

@dataclass
class FileOperation:
    """Represents a file system operation"""
    operation_type: str  # 'create', 'delete', 'modify', 'move'
    source_path: str
    destination_path: Optional[str] = None
    timestamp: float = 0
    user: Optional[str] = None

class WardFileEventHandler(FileSystemEventHandler):
    """File system event handler for Ward protection"""

    def __init__(self, base_path: str, protected_folders: List[str],
                 on_operation: Optional[Callable[[FileOperation], bool]] = None):
        self.base_path = Path(base_path).resolve()
        self.protector = FolderProtector(base_path, protected_folders)
        self.on_operation = on_operation
        self.blocked_operations: Set[str] = set()

    def should_monitor_event(self, event: FileSystemEvent) -> bool:
        """Check if event should be monitored"""
        # Skip monitoring of Ward's own files
        if event.is_directory:
            return False

        event_path = Path(event.src_path)

        # Skip hidden files and temporary files
        if event_path.name.startswith('.') or event_path.name.endswith('.tmp'):
            return False

        # Skip Ward configuration files
        if event_path.name == '.ward' or event_path.name.startswith('.ward_'):
            return False

        return True

    def on_created(self, event):
        """Handle file creation events"""
        if not self.should_monitor_event(event):
            return

        operation = FileOperation(
            operation_type='create',
            source_path=str(event.src_path),
            timestamp=time.time()
        )

        # Check if protected path
        if self.protector.is_protected_path(event.src_path):
            protection_info = self.protector.get_protection_info(event.src_path)

            if self.on_operation:
                allowed = self.on_operation(operation)
                if not allowed:
                    self._block_operation(event.src_path)
            else:
                self._block_operation(event.src_path)

    def on_deleted(self, event):
        """Handle file deletion events"""
        if not self.should_monitor_event(event):
            return

        operation = FileOperation(
            operation_type='delete',
            source_path=str(event.src_path),
            timestamp=time.time()
        )

        # Check if protected path
        if self.protector.is_protected_path(event.src_path):
            protection_info = self.protector.get_protection_info(event.src_path)

            if self.on_operation:
                allowed = self.on_operation(operation)
                if not allowed:
                    self._log_protection_event(operation, protection_info)

    def on_moved(self, event):
        """Handle file move events"""
        if not self.should_monitor_event(event):
            return

        operation = FileOperation(
            operation_type='move',
            source_path=str(event.src_path),
            destination_path=str(event.dest_path) if hasattr(event, 'dest_path') else None,
            timestamp=time.time()
        )

        # Check if source or destination is protected
        source_protected = self.protector.is_protected_path(event.src_path)
        dest_protected = event.dest_path and self.protector.is_protected_path(event.dest_path)

        if source_protected or dest_protected:
            if self.on_operation:
                allowed = self.on_operation(operation)
                if not allowed:
                    self._block_operation(event.src_path)

    def _block_operation(self, path: str):
        """Block a file system operation"""
        try:
            # For files, we can't easily block after the fact, but we can
            # track this for logging or future prevention
            self.blocked_operations.add(path)
            print(f"🚫 BLOCKED: File operation on protected path: {path}")
        except Exception:
            pass

    def _log_protection_event(self, operation: FileOperation, protection_info: Dict):
        """Log protection event"""
        try:
            print(f"🛡️ PROTECTION: {operation.operation_type.upper()} blocked")
            print(f"   Path: {operation.source_path}")
            print(f"   Reason: {protection_info.get('message', 'Unknown')}")
            print(f"   Protected folder: {protection_info.get('folder', 'Unknown')}")
        except Exception:
            pass

class WardFileMonitor:
    """Main file system monitor for Ward protection"""

    def __init__(self, base_path: str, protected_folders: List[str]):
        self.base_path = Path(base_path).resolve()
        self.protected_folders = protected_folders
        self.protector = FolderProtector(base_path, protected_folders)
        self.observer = Observer()
        self.handler = None
        self.monitoring = False
        self.operation_log: List[FileOperation] = []

    def start_monitoring(self, callback: Optional[Callable[[FileOperation], bool]] = None) -> bool:
        """Start file system monitoring"""
        if self.monitoring:
            return True

        try:
            # Create event handler
            self.handler = WardFileEventHandler(
                str(self.base_path),
                self.protected_folders,
                callback
            )

            # Start monitoring
            self.observer.schedule(self.handler, str(self.base_path), recursive=True)
            self.observer.start()
            self.monitoring = True

            return True
        except Exception as e:
            print(f"❌ Failed to start file monitoring: {e}")
            return False

    def stop_monitoring(self):
        """Stop file system monitoring"""
        if self.monitoring and self.observer:
            try:
                self.observer.stop()
                self.observer.join()
                self.monitoring = False
            except Exception:
                pass

    def is_protected_path(self, path: str) -> bool:
        """Check if a path is protected"""
        return self.protector.is_protected_path(path)

    def get_protection_info(self, path: str) -> Dict:
        """Get protection information for a path"""
        return self.protector.get_protection_info(path)

    def add_protected_folder(self, folder_name: str) -> bool:
        """Add a new folder to protection"""
        if folder_name not in self.protected_folders:
            self.protected_folders.append(folder_name)
            # Recreate protector with updated folders
            self.protector = FolderProtector(str(self.base_path), self.protected_folders)
            return True
        return False

    def remove_protected_folder(self, folder_name: str) -> bool:
        """Remove a folder from protection"""
        if folder_name in self.protected_folders:
            self.protected_folders.remove(folder_name)
            # Recreate protector with updated folders
            self.protector = FolderProtector(str(self.base_path), self.protected_folders)
            return True
        return False

    def get_protection_summary(self) -> Dict:
        """Get summary of current protection settings"""
        return self.protector.get_protection_summary()

# Standalone protection checker function
def check_file_protection(base_path: str, file_path: str, protected_folders: List[str]) -> Dict:
    """Check if a file operation should be blocked"""
    protector = FolderProtector(base_path, protected_folders)
    protection_info = protector.get_protection_info(file_path)

    return {
        "blocked": protection_info["protected"],
        "protection_info": protection_info,
        "recommendation": "This operation will be blocked by Ward protection" if protection_info["protected"] else "Operation allowed"
    }