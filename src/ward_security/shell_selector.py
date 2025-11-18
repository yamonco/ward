#!/usr/bin/env python3
"""
Interactive Shell Selector
Provides user-friendly shell selection interface
"""

import sys
import select
from typing import List, Tuple, Optional

class ShellSelector:
    """Interactive shell selection interface"""

    def __init__(self):
        self.selected_index = 0

    def display_shell_menu(self, available_shells: List[Tuple[str, bool, str]],
                          detected_shell: str) -> Optional[str]:
        """Display interactive shell selection menu"""
        print()
        print("🐚 Shell Selection for Ward Configuration")
        print("=" * 50)
        print(f"Detected current shell: {detected_shell}")
        print()
        print("Select your shell for Ward integration:")
        print()

        # Display menu items
        for idx, (shell_name, is_available, description) in enumerate(available_shells):
            status = "✅" if is_available else "❌"
            current = " (CURRENT)" if shell_name == detected_shell else ""

            marker = "👉" if idx == self.selected_index else "  "
            print(f"{marker} [{idx+1}] {status} {shell_name.upper()}{current}")
            print(f"      {description}")
            print()

        print("Controls:")
        print("  ↑/↓ or k/j - Navigate")
        print("  Enter/Space - Select")
        print("  q/Escape - Cancel")
        print()
        print("Select a shell [1-{}] or press Enter for detected shell ({}): ".format(
            len(available_shells), detected_shell), end="", flush=True)

        return self._get_user_selection(available_shells, detected_shell)

    def _get_user_selection(self, available_shells: List[Tuple[str, bool, str]],
                           detected_shell: str) -> Optional[str]:
        """Get user selection from input"""
        try:
            # Try to get a single character without waiting for Enter
            if select.select([sys.stdin], [], [], 0.1)[0]:
                char = sys.stdin.read(1)
                if char in ['\n', '\r']:
                    # Enter - use detected shell if available
                    for shell_name, is_available, _ in available_shells:
                        if shell_name == detected_shell and is_available:
                            return shell_name
                    return None
                elif char.lower() == 'q':
                    return None
                elif char in ['\x1b']:  # Escape
                    return None
                elif char.isdigit():
                    # Direct number selection
                    try:
                        idx = int(char) - 1
                        if 0 <= idx < len(available_shells):
                            shell_name, is_available, _ = available_shells[idx]
                            return shell_name if is_available else None
                    except (ValueError, IndexError):
                        pass

            # Fallback: read full line
            line = sys.stdin.readline().strip()
            if not line:
                # Empty line - use detected shell
                for shell_name, is_available, _ in available_shells:
                    if shell_name == detected_shell and is_available:
                        return shell_name
                return None

            # Parse number input
            try:
                idx = int(line) - 1
                if 0 <= idx < len(available_shells):
                    shell_name, is_available, _ = available_shells[idx]
                    return shell_name if is_available else None
            except (ValueError, IndexError):
                pass

        except (IOError, OSError):
            # Fallback to simple input
            try:
                response = input().strip()
                if not response:
                    for shell_name, is_available, _ in available_shells:
                        if shell_name == detected_shell and is_available:
                            return shell_name
                    return None

                idx = int(response) - 1
                if 0 <= idx < len(available_shells):
                    shell_name, is_available, _ = available_shells[idx]
                    return shell_name if is_available else None
            except (ValueError, IndexError, KeyboardInterrupt):
                return None

        return None

    def simple_selection(self, available_shells: List[Tuple[str, bool, str]],
                        detected_shell: str) -> Optional[str]:
        """Simple selection for non-interactive environments"""
        print()
        print("🐚 Available Shells for Ward Configuration")
        print("=" * 45)

        # First, show the detected shell if available
        for shell_name, is_available, description in available_shells:
            if shell_name == detected_shell and is_available:
                print(f"✅ Recommended: {shell_name.upper()} (detected)")
                print(f"   {description}")

                response = input(f"Use {shell_name}? [Y/n]: ").strip().lower()
                if not response or response in ['y', 'yes']:
                    return shell_name
                break

        # Show all available shells
        print()
        print("Available shells:")
        available_list = []
        for idx, (shell_name, is_available, description) in enumerate(available_shells, 1):
            if is_available and shell_name != detected_shell:
                available_list.append((shell_name, description))
                print(f"[{len(available_list)}] {shell_name.upper()}")
                print(f"    {description}")

        if not available_list:
            print("❌ No additional shells available")
            return None

        print()
        try:
            choice = input(f"Select shell [1-{len(available_list)}] or Enter to skip: ").strip()
            if not choice:
                return None

            idx = int(choice) - 1
            if 0 <= idx < len(available_list):
                return available_list[idx][0]
        except (ValueError, IndexError, KeyboardInterrupt):
            return None

        return None