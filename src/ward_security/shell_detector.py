#!/usr/bin/env python3
"""
Shell Detection and Configuration Module
Detects user's shell environment and generates appropriate configurations
"""

import os
import json
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict

@dataclass
class ShellProfile:
    """Shell configuration profile"""
    name: str
    config_files: List[str]
    prompt_var: str
    activation_commands: List[str]
    theme_detection: List[str]
    fallback_script: str

@dataclass
class ShellConfiguration:
    """Shell configuration data"""
    detected_shell: str
    selected_shell: str
    shell_theme: str
    prompt_variables: Dict[str, str]
    activation_method: str

class ShellDetector:
    """Detects and configures shell environments"""

    def __init__(self):
        self.shell_profiles = self._initialize_shell_profiles()
        self.config_dir = Path.home() / ".ward"
        self.config_file = self.config_dir / "config.json"

    def _initialize_shell_profiles(self) -> Dict[str, ShellProfile]:
        """Initialize supported shell profiles"""
        return {
            "bash": ShellProfile(
                name="bash",
                config_files=["~/.bashrc", "~/.bash_profile", "~/.profile"],
                prompt_var="PS1",
                activation_commands=[
                    "export WARD_ORIGINAL_PS1=\"$PS1\"",
                    "export PS1=\"🛡️ $PS1\""
                ],
                theme_detection=["PS1=", "\\[\\033", "\\e["],
                fallback_script="ward-activate.sh"
            ),
            "zsh": ShellProfile(
                name="zsh",
                config_files=["~/.zshrc", "~/.zprofile", "~/.zshenv"],
                prompt_var="PROMPT",
                activation_commands=[
                    "autoload -U colors && colors",
                    "export WARD_ORIGINAL_PROMPT=\"$PROMPT\"",
                    "export PROMPT=\"%{{$fg_bold[cyan]%}}🛡️ %{{$reset_color%}}$PROMPT\""
                ],
                theme_detection=["ZSH_THEME=", "agnoster", "powerlevel10k", "$PROMPT"],
                fallback_script="ward-activate.sh"
            ),
            "fish": ShellProfile(
                name="fish",
                config_files=["~/.config/fish/config.fish", "~/.config/fish/functions/fish_prompt.fish"],
                prompt_var="fish_prompt",
                activation_commands=[
                    "function fish_prompt",
                    "    echo -n \"🛡️ \"",
                    "    (eval (status function-or-substitution --status-line))",
                    "end"
                ],
                theme_detection=["fish_prompt", "starship", "tide"],
                fallback_script="ward-activate.fish"
            ),
            "ksh": ShellProfile(
                name="ksh",
                config_files=["~/.kshrc", "~/.profile"],
                prompt_var="PS1",
                activation_commands=[
                    "export WARD_ORIGINAL_PS1=\"$PS1\"",
                    "export PS1=\"🛡️ $PS1\""
                ],
                theme_detection=["PS1="],
                fallback_script="ward-activate.sh"
            ),
            "csh": ShellProfile(
                name="csh",
                config_files=["~/.cshrc", "~/.login", "~/.tcshrc"],
                prompt_var="prompt",
                activation_commands=[
                    "setenv WARD_ORIGINAL_PROMPT \"$prompt\"",
                    "set prompt = \"🛡️ $prompt\""
                ],
                theme_detection=["set prompt"],
                fallback_script="ward-activate.csh"
            ),
            "tcsh": ShellProfile(
                name="tcsh",
                config_files=["~/.tcshrc", "~/.cshrc", "~/.login"],
                prompt_var="prompt",
                activation_commands=[
                    "setenv WARD_ORIGINAL_PROMPT \"$prompt\"",
                    "set prompt = \"🛡️ $prompt\""
                ],
                theme_detection=["set prompt"],
                fallback_script="ward-activate.csh"
            )
        }

    def detect_current_shell(self) -> str:
        """Detect current shell from environment"""
        # Primary: $SHELL environment variable
        shell_env = os.environ.get("SHELL", "")
        if shell_env:
            shell_name = Path(shell_env).name
            if shell_name in self.shell_profiles:
                return shell_name
            # Remove version numbers and suffixes
            shell_base = shell_name.split()[0].replace("-shell", "")
            if shell_base in self.shell_profiles:
                return shell_base

        # Fallback: process name
        try:
            import psutil
            process = psutil.Process()
            parent = process.parent()
            if parent:
                parent_name = Path(parent.name()).name
                if parent_name in self.shell_profiles:
                    return parent_name
        except (ImportError, psutil.NoSuchProcess):
            pass

        # Default to bash as fallback
        return "bash"

    def validate_shell_availability(self, shell_name: str) -> bool:
        """Check if shell is available on the system"""
        try:
            result = subprocess.run(
                [shell_name, "--version"],
                capture_output=True,
                timeout=5
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False

    def detect_theme(self, shell_name: str) -> str:
        """Detect shell theme or framework"""
        profile = self.shell_profiles.get(shell_name)
        if not profile:
            return "unknown"

        # Check common theme locations and patterns
        if shell_name == "zsh":
            # Oh My Zsh
            zsh_dir = Path.home() / ".oh-my-zsh"
            if zsh_dir.exists():
                zshrc = Path.home() / ".zshrc"
                if zsh_dir.exists():
                    try:
                        with open(zshrc, 'r') as f:
                            content = f.read()
                            if "ZSH_THEME=" in content:
                                import re
                                match = re.search(r'ZSH_THEME="([^"]+)"', content)
                                if match:
                                    return f"oh-my-zsh-{match.group(1)}"
                            if "agnoster" in content.lower():
                                return "oh-my-zsh-agnoster"
                            if "powerlevel10k" in content.lower():
                                return "oh-my-zsh-powerlevel10k"
                    except (IOError, OSError):
                        pass
                return "oh-my-zsh"

            # Powerlevel10k standalone
            if (Path.home() / ".p10k.zsh").exists():
                return "powerlevel10k"

            # Starship
            if (Path.home() / ".config" / "starship.toml").exists():
                return "starship"

        elif shell_name == "bash":
            # Starship for bash
            if (Path.home() / ".config" / "starship.toml").exists():
                return "starship"

        return "default"

    def get_available_shells(self) -> List[Tuple[str, bool, str]]:
        """Get list of available shells with their status"""
        available = []
        for shell_name, profile in self.shell_profiles.items():
            is_available = self.validate_shell_availability(shell_name)
            description = f"{profile.name.title()} shell"
            if shell_name == self.detect_current_shell():
                description += " (current)"
            available.append((shell_name, is_available, description))

        return available

    def create_shell_config(self, selected_shell: str) -> ShellConfiguration:
        """Create shell configuration"""
        detected_shell = self.detect_current_shell()
        shell_theme = self.detect_theme(selected_shell)
        profile = self.shell_profiles.get(selected_shell)

        return ShellConfiguration(
            detected_shell=detected_shell,
            selected_shell=selected_shell,
            shell_theme=shell_theme,
            prompt_variables={
                "shell": selected_shell,
                "prompt_var": profile.prompt_var if profile else "PROMPT",
                "config_files": profile.config_files if profile else []
            },
            activation_method="standalone_script" if selected_shell != detected_shell else "rc_file"
        )

    def save_configuration(self, config: ShellConfiguration) -> bool:
        """Save shell configuration to file"""
        try:
            self.config_dir.mkdir(exist_ok=True)

            # Load existing config if it exists
            existing_config = {}
            if self.config_file.exists():
                try:
                    with open(self.config_file, 'r') as f:
                        existing_config = json.load(f)
                except (json.JSONDecodeError, IOError):
                    existing_config = {}

            # Update with shell configuration
            existing_config["shell"] = asdict(config)

            with open(self.config_file, 'w') as f:
                json.dump(existing_config, f, indent=2, ensure_ascii=False)

            return True
        except (IOError, OSError):
            return False

    def load_configuration(self) -> Optional[ShellConfiguration]:
        """Load shell configuration from file"""
        try:
            if not self.config_file.exists():
                return None

            with open(self.config_file, 'r') as f:
                config_data = json.load(f)
                shell_data = config_data.get("shell")

            if shell_data:
                return ShellConfiguration(**shell_data)

            return None
        except (json.JSONDecodeError, IOError, TypeError):
            return None