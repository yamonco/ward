#!/usr/bin/env python3
"""
Ward Security CLI Interface
Python wrapper for the Ward Security System
"""

import os
import sys
import subprocess
import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any
import re

# Import favorites functionality
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from favorites import WardFavorites, WardPlanter
from indexer import WardIndexer
from ai_assistant import AIAssistantManager, AssistantType

class WardCLI:
    """Ward Security Command Line Interface"""

    def __init__(self):
        self.ward_root = Path(__file__).parent.parent.parent
        self.ward_cli_path = self.ward_root / ".ward" / "ward.sh"
        self.ward_home = Path.home() / ".ward"
        self.mcp_server_path = self.ward_home / "mcp" / "mcp_server.py"
        self.favorites = WardFavorites()
        self.planter = WardPlanter()
        self.ai_manager = AIAssistantManager()
        self.ward_shell_mode = False  # Track if we're in Ward Shell mode
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

    def handle_interactive_mode(self) -> int:
        """Handle interactive mode with conversational interface"""
        print("🛡️ Ward Security System - Interactive Mode")
        print("=" * 50)
        print("👋 안녕하세요! Ward 도우미입니다. 무엇을 도와드릴까요?")
        print("📝 자연어로 말씀하시거나, 메뉴 번호를 선택하세요.")
        print("🚪 '종료', 'exit', 'quit' 또는 'q'를 입력하면 나갈 수 있습니다.")
        print()

        while True:
            current_dir = Path.cwd()
            ward_status = "🛡️ 활성화" if (current_dir / ".ward").exists() else "⚪ 비활성화"

            print(f"📍 현재 위치: {current_dir} ({ward_status})")
            print()
            print("🎯 **선택지:**")
            print("1. 🌱 현재 위치 보호하기 (Ward 설치)")
            print("2. 🔒 폴더 잠그기")
            print("3. 🔓 폴더 잠금 해제")
            print("4. 📝 코멘트 추가")
            print("5. ℹ️ 현재 상태 확인")
            print("6. 🔄 다른 위치로 이동")
            print("7. ❓ 도움말")
            print("0. 🚪 종료")
            print()

            try:
                user_input = input("💬 입력: ").strip()

                # 종료 명령 확인
                if user_input.lower() in ['종료', 'exit', 'quit', 'q', '0']:
                    print("👋 안녕히 가세요!")
                    break

                # 메뉴 번호 처리
                if user_input.isdigit():
                    choice = int(user_input)
                    if choice == 1:
                        self._interactive_plant_ward()
                    elif choice == 2:
                        self._interactive_lock_directory()
                    elif choice == 3:
                        self._interactive_unlock_directory()
                    elif choice == 4:
                        self._interactive_add_comment()
                    elif choice == 5:
                        self._interactive_check_status()
                    elif choice == 6:
                        self._interactive_change_directory()
                    elif choice == 7:
                        self._interactive_show_help()
                    else:
                        print("❌ 잘못된 번호입니다. 다시 선택해주세요.")
                    continue

                # 자연어 처리
                self._process_natural_language(user_input)

            except KeyboardInterrupt:
                print("\n👋 안녕히 가세요!")
                break
            except EOFError:
                print("\n👋 안녕히 가세요!")
                break

        return 0

    def _interactive_plant_ward(self):
        """대화형으로 Ward 설치"""
        print("\n🌱 **현재 위치 보호하기**")
        print("=" * 30)

        description = input("📝 설명 (없으면 엔터): ").strip()
        if not description:
            description = "이 폴더는 건드리면 안된다"

        print(f"📍 위치: {Path.cwd()}")
        print(f"📝 설명: {description}")

        confirm = input("✅ 이대로 설치할까요? (y/n): ").strip().lower()
        if confirm in ['y', 'yes', '예', '네']:
            result = self.plant_ward_cli(".", description)
            if result == 0:
                print("✅ 성공적으로 설치되었습니다!")
                self.ward_info_cli(".")
            else:
                print("❌ 설치에 실패했습니다.")
        else:
            print("❌ 취소되었습니다.")

    def _interactive_lock_directory(self):
        """대화형으로 디렉토리 잠그기"""
        print("\n🔒 **폴더 잠그기**")
        print("=" * 30)

        path = input(f"📍 경로 (현재: {Path.cwd()}): ").strip()
        if not path:
            path = "."

        message = input("📝 잠금 메시지: ").strip()
        if not message:
            message = "이곳은 잠겨있습니다"

        print(f"📍 위치: {path}")
        print(f"📝 메시지: {message}")

        confirm = input("🔒 이대로 잠글까요? (y/n): ").strip().lower()
        if confirm in ['y', 'yes', '예', '네']:
            result = self.plant_ward_cli(path, f"🔒 LOCKED: {message}")
            if result == 0:
                print("✅ 성공적으로 잠겼습니다!")
                self.ward_info_cli(path)
            else:
                print("❌ 잠그기에 실패했습니다.")
        else:
            print("❌ 취소되었습니다.")

    def _interactive_unlock_directory(self):
        """대화형으로 디렉토리 잠금 해제"""
        print("\n🔓 **폴더 잠금 해제**")
        print("=" * 30)

        path = input(f"📍 경로 (현재: {Path.cwd()}): ").strip()
        if not path:
            path = "."

        message = input("📝 허용 메시지: ").strip()
        if not message:
            message = "이곳은 이제 안전합니다"

        print(f"📍 위치: {path}")
        print(f"📝 메시지: {message}")

        confirm = input("🔓 이대로 잠금 해제할까요? (y/n): ").strip().lower()
        if confirm in ['y', 'yes', '예', '네']:
            result = self.plant_ward_cli(path, f"🔓 UNLOCKED: {message}")
            if result == 0:
                print("✅ 성공적으로 잠금 해제되었습니다!")
                self.ward_info_cli(path)
            else:
                print("❌ 잠금 해제에 실패했습니다.")
        else:
            print("❌ 취소되었습니다.")

    def _interactive_add_comment(self):
        """대화형으로 코멘트 추가"""
        print("\n📝 **코멘트 추가**")
        print("=" * 30)

        comment = input("💬 코멘트 내용: ").strip()
        if not comment:
            print("❌ 코멘트 내용을 입력해주세요.")
            return

        print(f"📍 위치: {Path.cwd()}")
        print(f"💬 코멘트: {comment}")

        confirm = input("✅ 이대로 추가할까요? (y/n): ").strip().lower()
        if confirm in ['y', 'yes', '예', '네']:
            comment_file = Path.cwd() / ".ward_comment.txt"
            try:
                with open(comment_file, 'w', encoding='utf-8') as f:
                    f.write(f"💬 Comment: {comment}\n")
                    f.write(f"📅 Added: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                    f.write(f"👤 By: Interactive User\n")
                print("✅ 코멘트가 추가되었습니다!")
                print(f"📍 위치: {comment_file}")
            except Exception as e:
                print(f"❌ 코멘트 추가 실패: {e}")
        else:
            print("❌ 취소되었습니다.")

    def _interactive_check_status(self):
        """대화형으로 상태 확인"""
        print("\nℹ️ **현재 상태 확인**")
        print("=" * 30)
        self.ward_info_cli(".")

    def _interactive_change_directory(self):
        """대화형으로 디렉토리 변경"""
        print("\n🔄 **디렉토리 변경**")
        print("=" * 30)

        new_path = input(f"📍 새 경로 (현재: {Path.cwd()}): ").strip()
        if new_path:
            try:
                os.chdir(new_path)
                print(f"✅ {Path.cwd()}로 이동했습니다.")
            except Exception as e:
                print(f"❌ 이동 실패: {e}")

    def _interactive_show_help(self):
        """대화형 도움말 표시"""
        print("\n❓ **도움말**")
        print("=" * 30)
        print("🎯 **자연어 명령어 예시:**")
        print("• '여기 잠가줘' - 현재 위치 잠그기")
        print("• '보호해줘' - Ward 설치")
        print("• '코멘트 남겨줘' - 코멘트 추가")
        print("• '상태 확인' - 현재 상태 보기")
        print("• '이동해줘' - 디렉토리 변경")
        print()
        print("🚪 **종료 명령어:**")
        print("• '종료', 'exit', 'quit', 'q', '0'")
        print()
        print("💡 **팁:**")
        print("• 항상 현재 위치를 보여줍니다")
        print("• 자연어로 편하게 대화하세요")
        print("• 확인 절차가 있어 안전합니다")

    def _process_natural_language(self, user_input: str):
        """AI assistant 기반 자연어 처리"""
        # AI 어시스턴트로 명령어 처리
        result = self.process_natural_command(user_input)

        if result.get("assistant") != "local" and "reasoning" in result:
            # AI 어시스턴트의 결과
            print(f"🤖 {result['assistant']} 분석:")
            if "reasoning" in result:
                print(f"💡 사유: {result['reasoning']}")
            print()

        # 결과에 따른 액션 실행
        action = result.get("action", "unknown")
        confidence = result.get("confidence", 0.0)

        if confidence < 0.5:
            print(f"⚠️  낮은 신뢰도 ({confidence:.2f}): 명령어를 명확하게 해주세요")
            return

        if action == "lock":
            message = result.get("message", user_input)
            path = result.get("path", ".")
            print(f"🔒 '{path}'를 잠급니다...")
            plant_result = self.plant_ward_cli(path, f"🔒 LOCKED: {message}")
            if plant_result == 0:
                print("✅ 성공적으로 잠겼습니다!")
                self.ward_info_cli(path)
            else:
                print("❌ 잠그기 실패")

        elif action == "unlock":
            message = result.get("message", user_input)
            path = result.get("path", ".")
            print(f"🔓 '{path}'의 잠금을 해제합니다...")
            plant_result = self.plant_ward_cli(path, f"🔓 UNLOCKED: {message}")
            if plant_result == 0:
                print("✅ 성공적으로 잠금 해제되었습니다!")
                self.ward_info_cli(path)
            else:
                print("❌ 잠금 해제 실패")

        elif action == "plant":
            description = result.get("description", user_input)
            path = result.get("path", ".")
            print(f"🌱 '{path}'에 보호를 설치합니다...")
            plant_result = self.plant_ward_cli(path, description)
            if plant_result == 0:
                print("✅ 성공적으로 보호 설정되었습니다!")
                self.ward_info_cli(path)
            else:
                print("❌ 보호 설정 실패")

        elif action == "add_comment":
            comment = result.get("comment", user_input)
            path = result.get("path", ".")
            print(f"💬 '{path}'에 코멘트를 추가합니다...")
            comment_file = Path(path) / ".ward_comment.txt"
            try:
                with open(comment_file, 'w', encoding='utf-8') as f:
                    f.write(f"💬 Comment: {comment}\n")
                    f.write(f"📅 Added: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                    f.write(f"👤 By: Interactive User\n")
                print("✅ 코멘트가 추가되었습니다!")
                print(f"📍 위치: {comment_file}")
            except Exception as e:
                print(f"❌ 코멘트 추가 실패: {e}")

        elif action == "status":
            path = result.get("path", ".")
            print(f"ℹ️ '{path}' 상태 확인:")
            self.ward_info_cli(path)

        elif action == "unknown":
            print("❌ 이해하지 못했습니다. 다른 방식으로 말씀해주세요.")
            print(f"💡 팁: '{user_input}' - 더 명확한 명령어를 사용해보세요")
            print("🤖 현재 AI 어시스턴트:", result.get("assistant", "local"))
        else:
            print(f"⚠️  알 수 없는 액션: {action}")

        # 신뢰도 표시
        if confidence >= 0.8:
            print(f"✅ 신뢰도: {confidence:.2f} (높음)")
        elif confidence >= 0.5:
            print(f"⚠️  신뢰도: {confidence:.2f} (중간)")
        else:
            print(f"❌ 신뢰도: {confidence:.2f} (낮음)")

    def handle_ai_command(self, args) -> int:
        """Handle AI assistant commands"""
        if args.ai_action == "list":
            print(self.ai_manager.get_assistant_menu())
            return 0
        elif args.ai_action == "select":
            success = self.ai_manager.set_active_assistant(args.assistant_name)
            if success:
                print(f"✅ AI assistant '{args.assistant_name}' selected successfully!")
                active = self.ai_manager.get_active_assistant()
                if active:
                    print(f"🤖 Model: {active.model}")
                    print(f"🌡️  Temperature: {active.temperature}")
            else:
                print(f"❌ Failed to select assistant '{args.assistant_name}'")
                print("💡 Use 'ward ai list' to see available assistants")
                return 1
        elif args.ai_action is None:
            # No subcommand provided - show current status
            active = self.ai_manager.get_active_assistant()
            if active:
                print(f"🤖 Current AI Assistant: {active.name}")
                print(f"📝 Model: {active.model}")
                print(f"🌡️  Temperature: {active.temperature}")
            else:
                print("⚪ No AI assistant selected")
                print("💡 Use 'ward ai list' to see available assistants")
                print("💡 Use 'ward ai select <name>' to select an assistant")
        else:
            print(f"Unknown AI command: {args.ai_action}")
            return 1

        return 0

    def handle_activate_command(self) -> int:
        """Activate Ward Shell mode (AI-assisted)"""
        print("🛡️ Activating Ward Shell Mode...")
        print("🤖 AI Assistant integration enabled")
        print("📋 All commands will be processed through AI assistant")

        # Check if AI assistant is configured
        active_assistant = self.ai_manager.get_active_assistant()
        if not active_assistant or active_assistant.type == AssistantType.NONE:
            print("⚠️  No AI assistant configured!")
            print("💡 Configure an AI assistant first:")
            print("   ward ai list           # Show available assistants")
            print("   ward ai select <name>  # Select an assistant")
            print()
            print("🔄 Continuing with local processing...")

        self.ward_shell_mode = True

        # Save original PS1 if not already saved
        original_ps1 = os.environ.get("WARD_ORIGINAL_PS1")
        if not original_ps1:
            original_ps1 = os.environ.get("PS1", "")
            os.environ["WARD_ORIGINAL_PS1"] = original_ps1

        # Create Ward Shell enhanced prompt
        current_ps1 = os.environ.get("PS1", "")
        ward_prefix = "🛡️⚡️ "  # Shield + lightning for AI mode

        # Check if Ward prefix already exists
        if ward_prefix not in current_ps1:
            new_ps1 = f"{ward_prefix}{current_ps1}"
            os.environ["PS1"] = new_ps1

            # Create Ward Shell activation script
            activation_script = Path.home() / ".ward-shell-activate.sh"
            with open(activation_script, 'w') as f:
                f.write(f"""#!/bin/bash
# Ward Shell Activation (AI Assistant Mode)
export WARD_SHELL_MODE=true
export WARD_ORIGINAL_PS1="${{WARD_ORIGINAL_PS1:-$PS1}}"
export PS1="{new_ps1}"
echo "🛡️⚡️ Ward Shell activated (AI Assistant Mode)"
echo "💡 All commands processed through AI assistant"
echo "🔧 Use 'ward deactivate' to return to normal terminal"
""")
            activation_script.chmod(0o755)

            print("✅ Ward Shell activated!")
            print(f"📌 Original prompt saved")
            print(f"🤖 AI Assistant: {active_assistant.name if active_assistant else 'Local Processing'}")
            print("💡 Your prompt now shows 🛡️⚡️ to indicate Ward Shell mode")
            print("🔧 All natural language commands are AI-assisted")
            print()
            print("To return to normal terminal:")
            print("   ward deactivate")
            print()
            print("⚠️  Note: For permanent prompt changes, run:")
            print(f"   source {activation_script}")
            return 0
        else:
            print("✅ Ward Shell is already active!")
            return 1

    def handle_deactivate_command(self) -> int:
        """Deactivate Ward Shell mode (return to normal terminal)"""
        print("🔓 Deactivating Ward Shell Mode...")
        print("💻 Returning to normal terminal mode")

        self.ward_shell_mode = False

        try:
            # Restore original PS1
            original_ps1 = os.environ.get("WARD_ORIGINAL_PS1")
            if original_ps1:
                os.environ["PS1"] = original_ps1
                print("✅ Original prompt restored!")
                print("💻 Normal terminal mode activated")
            else:
                print("⚠️  No original prompt found - keeping current prompt")

            # Remove activation script if it exists
            activation_script = Path.home() / ".ward-shell-activate.sh"
            if activation_script.exists():
                activation_script.unlink()
                print("🗑️  Ward Shell activation script removed")

            # Clear shell mode environment variable
            if "WARD_SHELL_MODE" in os.environ:
                del os.environ["WARD_SHELL_MODE"]

            print("🔓 Ward Shell deactivated")
            print("💻 Natural language commands now use local processing")
            print("🤖 AI assistants still available via MCP")
            return 0

        except Exception as e:
            print(f"❌ Error deactivating Ward Shell: {e}")
            return 1

    def handle_process_command(self, args) -> int:
        """Handle natural language command processing with JSON output"""
        result = self.process_natural_command(args.command)

        # Output as JSON for programmatic use
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return 0

    def process_natural_command(self, user_input: str) -> Dict[str, Any]:
        """Process natural language command based on current mode"""
        if self.ward_shell_mode:
            # Ward Shell mode - use AI assistant
            return self.ai_manager.process_command_with_ai(user_input)
        else:
            # Normal terminal mode - use local processing with JSON output
            result = self.ai_manager._local_command_processing(user_input)
            # Add mode information
            result["mode"] = "terminal"
            result["processing"] = "local"
            return result

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

        # Protected folders command
        protect_parser = subparsers.add_parser("protect", help="Add protected folders to Ward")
        protect_parser.add_argument("folders", nargs="+", help="List of folder names to protect within the Ward directory")
        protect_parser.add_argument("--path", default=".", help="Base path (defaults to current directory)")

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

        # AI Assistant commands
        ai_parser = subparsers.add_parser("ai", help="Manage AI assistants")
        ai_subparsers = ai_parser.add_subparsers(dest="ai_action")

        ai_list_parser = ai_subparsers.add_parser("list", help="List available AI assistants")
        ai_select_parser = ai_subparsers.add_parser("select", help="Select AI assistant")
        ai_select_parser.add_argument("assistant_name", help="Name of assistant to select")

        # Environment activation (new mode system)
        activate_parser = subparsers.add_parser("activate", help="Activate Ward Shell mode (AI-assisted)")
        deactivate_parser = subparsers.add_parser("deactivate", help="Deactivate Ward Shell mode (normal terminal)")

        # Natural language processing
        process_parser = subparsers.add_parser("process", help="Process natural language command (JSON output)")
        process_parser.add_argument("command", help="Natural language command to process")

        # Interactive mode
        subparsers.add_parser("interactive", help="Start interactive Ward management mode")

        # Help and version
        subparsers.add_parser("help", help="Show this help message")

        args = parser.parse_args()

        # Handle commands
        if args.command == "mcp-server":
            return self.run_mcp_server()
        elif args.command == "ai":
            return self.handle_ai_command(args)
        elif args.command == "activate":
            return self.handle_activate_command()
        elif args.command == "deactivate":
            return self.handle_deactivate_command()
        elif args.command == "process":
            return self.handle_process_command(args)
        elif args.command == "interactive":
            return self.handle_interactive_mode()
        elif args.command is None:
            # Default to interactive mode when no command provided
            return self.handle_interactive_mode()
        elif args.command == "status":
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
        elif args.command == "protect":
            return self.handle_protect_command(args)
        elif args.command == "search":
            return self.handle_search_command(args)
        elif args.command == "bookmark":
            return self.handle_bookmark_command(args)
        elif args.command == "recent":
            return self.handle_recent_command(args)
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
        from .ward_config import WardConfigParser, FolderProtector

        target_path = Path(path).resolve()
        ward_file = target_path / ".ward"

        if not ward_file.exists():
            print(f"❌ No Ward found at: {path}")
            return 1

        # Parse Ward configuration
        parser = WardConfigParser()
        config = parser.parse_file(str(ward_file))

        if not config:
            print(f"❌ Failed to parse Ward configuration: {ward_file}")
            return 1

        print(f"🛡️ Ward Information for: {path}")
        print("=" * 50)
        print()
        print(f"📁 Ward file: {ward_file}")
        print(f"🔐 Password protected: {'Yes' if config.password_protected else 'No'}")
        print(f"🤖 AI initiated: {'Yes' if config.ai_initiated else 'No'}")

        if config.created:
            print(f"📅 Created: {config.created}")

        if config.shell:
            print(f"🐚 Shell: {config.shell}")
        if config.theme:
            print(f"🎨 Theme: {config.theme}")

        # Security policy
        print(f"\n🔒 Security Policy:")
        print(f"   Whitelist: {len(config.whitelist)} commands")
        print(f"   Blacklist: {len(config.blacklist)} commands")
        print(f"   AI guidance: {'Enabled' if config.ai_guidance else 'Disabled'}")

        # Protected folders (new feature)
        if config.protected_folders:
            print(f"\n🛡️ Protected Folders ({len(config.protected_folders)}):")
            protector = FolderProtector(str(target_path), config.protected_folders)

            for folder in config.protected_folders:
                folder_path = target_path / folder
                status = "✅" if folder_path.exists() else "⚠️ "
                print(f"   {status} {folder}")

            print(f"\n📋 Protection Summary:")
            summary = protector.get_protection_summary()
            print(f"   Base path: {summary['base_path']}")
            print(f"   Total protected: {summary['total_protected']}")
        else:
            print(f"\n🛡️ Protected Folders: None configured")
            print("💡 Use 'ward protect <folder1> <folder2> ...' to add protected folders")

        # Comments configuration
        if config.allow_comments:
            print(f"\n💬 Comments: Enabled (max: {config.max_comments})")
            if config.comment_prompt:
                print(f"   Prompt: {config.comment_prompt}")
        else:
            print(f"\n💬 Comments: Disabled")

        if config.password_protected:
            print(f"\n🗝️ Password file: ~/.ward/ward_passwords.json")
            print("⚠️ WARNING: This Ward is password-protected.")
            print("Manual user intervention required for removal.")

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

    def handle_protect_command(self, args) -> int:
        """Handle protect command - add protected folders to Ward"""
        from .ward_config import WardConfigParser, FolderProtector

        base_path = Path(args.path).resolve()
        folders_to_protect = args.folders

        # Check if Ward exists in the base path
        ward_file = base_path / ".ward"
        if not ward_file.exists():
            print(f"❌ No Ward found in: {base_path}")
            print("💡 Initialize Ward first: ward init")
            return 1

        # Validate that folders exist
        missing_folders = []
        for folder in folders_to_protect:
            folder_path = base_path / folder
            if not folder_path.exists():
                missing_folders.append(folder)
            elif not folder_path.is_dir():
                missing_folders.append(f"{folder} (not a directory)")

        if missing_folders:
            print("❌ The following folders don't exist:")
            for folder in missing_folders:
                print(f"   - {folder}")
            print()
            print("💡 Available folders in this directory:")
            try:
                for item in base_path.iterdir():
                    if item.is_dir() and not item.name.startswith('.'):
                        print(f"   - {item.name}")
            except Exception:
                pass
            return 1

        # Parse existing Ward configuration
        parser = WardConfigParser()
        config = parser.parse_file(str(ward_file))
        if not config:
            print(f"❌ Failed to parse Ward configuration: {ward_file}")
            return 1

        # Update protected_folders
        existing_folders = set(config.protected_folders) if config.protected_folders else set()
        new_folders = set(folders_to_protect)

        # Check for duplicates
        duplicates = existing_folders.intersection(new_folders)
        if duplicates:
            print("⚠️  The following folders are already protected:")
            for folder in duplicates:
                print(f"   - {folder}")

        # Add new folders
        added_folders = new_folders - existing_folders
        if not added_folders:
            print("ℹ️  No new folders to protect")
            return 0

        config.protected_folders = list(existing_folders.union(new_folders))

        # Write updated configuration
        try:
            updated_content = parser.generate_content(config)
            with open(ward_file, 'w', encoding='utf-8') as f:
                f.write(updated_content)

            print(f"✅ Protected folders added successfully!")
            print(f"📍 Base directory: {base_path}")
            print(f"🔒 New protected folders:")
            for folder in added_folders:
                print(f"   - {folder}")

            print(f"\n📋 Current protected folders ({len(config.protected_folders)}):")
            for folder in config.protected_folders:
                print(f"   - {folder}")

            # Test folder protection
            protector = FolderProtector(str(base_path), config.protected_folders)
            print(f"\n🛡️  Protection Summary:")
            summary = protector.get_protection_summary()
            print(f"   Total protected folders: {summary['total_protected']}")

            return 0

        except Exception as e:
            print(f"❌ Failed to update Ward configuration: {e}", file=sys.stderr)
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
        """Handle init command with shell selection and legacy installation warnings"""
        path = args.path or "."

        # Import shell detection modules
        from .shell_detector import ShellDetector
        from .shell_selector import ShellSelector

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

        # Initialize shell detection
        shell_detector = ShellDetector()
        shell_selector = ShellSelector()

        # Detect current shell
        detected_shell = shell_detector.detect_current_shell()
        print(f"🔍 Detected shell: {detected_shell}")

        # Get available shells
        available_shells = shell_detector.get_available_shells()

        # Shell selection
        selected_shell = None
        interactive = getattr(args, 'interactive', True)

        if interactive and sys.stdout.isatty():
            selected_shell = shell_selector.display_shell_menu(available_shells, detected_shell)
        else:
            selected_shell = shell_selector.simple_selection(available_shells, detected_shell)

        if not selected_shell:
            print("❌ Shell selection cancelled or invalid")
            return 1

        print(f"✅ Selected shell: {selected_shell}")

        # Create shell configuration
        shell_config = shell_detector.create_shell_config(selected_shell)
        theme = shell_config.shell_theme

        print(f"🎨 Detected theme: {theme}")

        # Save shell configuration
        if shell_detector.save_configuration(shell_config):
            print("✅ Shell configuration saved")
        else:
            print("⚠️  Warning: Could not save shell configuration")

        # Create basic .ward file content with shell information
        description = getattr(args, 'description', 'AI-Assisted Development Project')
        ward_content = f"""# Ward Security Configuration
@description: {description}
@shell: {selected_shell}
@theme: {theme}
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

        # Provide shell-specific activation instructions
        print("🚀 Ward is ready to use!")
        print()
        print("🔧 Activation Commands:")
        if selected_shell == "zsh":
            print("   source ~/.ward-activate.sh    # Activate Ward in ZSH")
            print("   ward activate                  # CLI activation (if available)")
        elif selected_shell == "bash":
            print("   source ~/.ward-activate.sh    # Activate Ward in Bash")
            print("   ward activate                  # CLI activation (if available)")
        elif selected_shell == "fish":
            print("   source ~/.ward-activate.fish  # Activate Ward in Fish")
            print("   ward activate                  # CLI activation (if available)")
        else:
            print("   source ~/.ward-activate.sh    # Activate Ward")
            print("   ward activate                  # CLI activation (if available)")

        print()
        print("💡 Tip: Use UV-installed Ward for best experience:")
        print("   export PATH=\"$HOME/.local/share/uv/tools/ward-security/bin:$PATH\"")
        print()
        print("⚙️  To change shell configuration later:")
        print("   ward config shell                 # Reconfigure shell settings")
        return 0

def main() -> int:
    """Main entry point for the CLI"""
    cli = WardCLI()
    return cli.main()

if __name__ == "__main__":
    sys.exit(main())