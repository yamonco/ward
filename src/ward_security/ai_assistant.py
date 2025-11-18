#!/usr/bin/env python3
"""
AI Assistant Configuration Manager for Ward Security System
Inspired by OpenCode's agent selection structure
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from enum import Enum


class AssistantType(Enum):
    """AI Assistant types"""
    CLAUDE = "claude"
    CHATGPT = "chatgpt"
    GEMINI = "gemini"
    CUSTOM = "custom"
    NONE = "none"


@dataclass
class AIAssistant:
    """AI Assistant configuration"""
    name: str
    type: AssistantType
    model: str
    api_key: Optional[str] = None
    api_endpoint: Optional[str] = None
    system_prompt: Optional[str] = None
    temperature: float = 0.7
    max_tokens: int = 2000
    enabled: bool = True

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        data = asdict(self)
        data['type'] = self.type.value
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AIAssistant':
        """Create from dictionary"""
        data = data.copy()
        if 'type' in data:
            data['type'] = AssistantType(data['type'])
        return cls(**data)


class AIAssistantManager:
    """Manages AI assistant configurations for Ward"""

    def __init__(self):
        self.config_dir = Path.home() / ".ward"
        self.config_file = self.config_dir / "ai_assistants.json"
        self.active_assistant_file = self.config_dir / "active_assistant.json"
        self._ensure_config_dir()
        self._load_default_assistants()

    def _ensure_config_dir(self):
        """Ensure config directory exists"""
        self.config_dir.mkdir(exist_ok=True)

    def _load_default_assistants(self):
        """Load default AI assistant configurations"""
        if not self.config_file.exists():
            default_assistants = {
                "assistants": [
                    {
                        "name": "Claude Sonnet",
                        "type": "claude",
                        "model": "claude-3-sonnet-20241022",
                        "system_prompt": "You are a Ward Security System assistant. Help users manage file protection, security policies, and AI assistant integration. Be helpful, clear, and security-focused.",
                        "temperature": 0.3,
                        "max_tokens": 1500,
                        "enabled": True
                    },
                    {
                        "name": "ChatGPT-4",
                        "type": "chatgpt",
                        "model": "gpt-4",
                        "system_prompt": "You are a Ward Security System assistant specializing in file system protection and security policy management.",
                        "temperature": 0.5,
                        "max_tokens": 1500,
                        "enabled": True
                    },
                    {
                        "name": "Gemini Pro",
                        "type": "gemini",
                        "model": "gemini-pro",
                        "system_prompt": "You are a Ward Security System assistant focused on protecting files and managing security policies.",
                        "temperature": 0.4,
                        "max_tokens": 1500,
                        "enabled": True
                    },
                    {
                        "name": "None (Local Processing)",
                        "type": "none",
                        "model": "local",
                        "system_prompt": "Local command processing without AI assistance.",
                        "temperature": 0.0,
                        "max_tokens": 0,
                        "enabled": True
                    }
                ]
            }
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(default_assistants, f, indent=2, ensure_ascii=False)

    def get_assistants(self) -> List[AIAssistant]:
        """Get all configured assistants"""
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            assistants = []
            for assistant_data in data.get('assistants', []):
                assistants.append(AIAssistant.from_dict(assistant_data))

            return assistants
        except (FileNotFoundError, json.JSONDecodeError):
            return []

    def get_active_assistant(self) -> Optional[AIAssistant]:
        """Get currently active assistant"""
        try:
            with open(self.active_assistant_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            assistant_name = data.get('active_assistant')
            if not assistant_name:
                return None

            assistants = self.get_assistants()
            for assistant in assistants:
                if assistant.name == assistant_name:
                    return assistant

            return None
        except (FileNotFoundError, json.JSONDecodeError):
            return None

    def set_active_assistant(self, assistant_name: str) -> bool:
        """Set active assistant"""
        assistants = self.get_assistants()
        for assistant in assistants:
            if assistant.name == assistant_name and assistant.enabled:
                with open(self.active_assistant_file, 'w', encoding='utf-8') as f:
                    json.dump({'active_assistant': assistant_name}, f, indent=2)
                return True

        return False

    def add_assistant(self, assistant: AIAssistant) -> bool:
        """Add new assistant"""
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            data = {'assistants': []}

        # Check if assistant already exists
        for i, existing in enumerate(data.get('assistants', [])):
            if existing.get('name') == assistant.name:
                data['assistants'][i] = assistant.to_dict()
                break
        else:
            data.setdefault('assistants', []).append(assistant.to_dict())

        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        return True

    def process_command_with_ai(self, user_input: str) -> Dict[str, Any]:
        """Process natural language command using active AI assistant"""
        assistant = self.get_active_assistant()

        if not assistant or assistant.type == AssistantType.NONE:
            # Fallback to local processing
            return self._local_command_processing(user_input)

        # Here you would integrate with the actual AI service
        # For now, we'll simulate the response
        return self._simulate_ai_response(assistant, user_input)

    def _local_command_processing(self, user_input: str) -> Dict[str, Any]:
        """Local command processing without AI"""
        user_input_lower = user_input.lower()

        # Simple keyword matching
        if any(keyword in user_input_lower for keyword in ['잠가', '잠금', 'lock', '잠그']):
            return {
                "action": "lock",
                "message": user_input,
                "path": ".",
                "confidence": 0.8,
                "assistant": "local"
            }
        elif any(keyword in user_input_lower for keyword in ['풀어', '해제', 'unlock', '열어', '잠금해제']):
            return {
                "action": "unlock",
                "message": user_input,
                "path": ".",
                "confidence": 0.8,
                "assistant": "local"
            }
        elif any(keyword in user_input_lower for keyword in ['보호', '설치', '만들어', 'plant', 'seed']):
            return {
                "action": "plant",
                "description": user_input,
                "path": ".",
                "confidence": 0.7,
                "assistant": "local"
            }
        elif any(keyword in user_input_lower for keyword in ['코멘트', 'comment', '메모', '남겨']):
            return {
                "action": "add_comment",
                "comment": user_input,
                "path": ".",
                "confidence": 0.8,
                "assistant": "local"
            }
        elif any(keyword in user_input_lower for keyword in ['상태', 'status', '확인', '보여']):
            return {
                "action": "status",
                "path": ".",
                "confidence": 0.9,
                "assistant": "local"
            }
        else:
            return {
                "action": "unknown",
                "message": "이해하지 못했습니다",
                "confidence": 0.1,
                "assistant": "local"
            }

    def _simulate_ai_response(self, assistant: AIAssistant, user_input: str) -> Dict[str, Any]:
        """Simulate AI response (replace with actual AI integration)"""
        # This is where you would integrate with Claude, ChatGPT, etc.
        # For now, we'll use enhanced local processing

        user_input_lower = user_input.lower()

        # Enhanced processing with context
        if "민감한" in user_input_lower and ("수정" in user_input_lower or "변경" in user_input_lower):
            return {
                "action": "lock",
                "message": "이 폴더는 민감한 데이터가 포함되어 있어 수정할 수 없습니다",
                "path": ".",
                "confidence": 0.95,
                "assistant": assistant.name,
                "reasoning": "사용자가 '민감한 폴더'와 '수정 안되게'를 언급하여 잠금 조치가 필요하다고 판단"
            }
        elif "보호해줘" in user_input_lower or "지켜줘" in user_input_lower:
            return {
                "action": "plant",
                "description": "사용자 요청으로 보호 설정",
                "path": ".",
                "confidence": 0.9,
                "assistant": assistant.name,
                "reasoning": "보호 요청 명령어를 감지하여 Ward 설치 필요"
            }

        # Fallback to local processing with AI branding
        result = self._local_command_processing(user_input)
        result["assistant"] = assistant.name

        return result

    def get_assistant_menu(self) -> str:
        """Get formatted assistant selection menu"""
        assistants = self.get_assistants()
        active = self.get_active_assistant()
        active_name = active.name if active else "None"

        menu = "🤖 **AI Assistant Selection:**\n"
        menu += "=" * 30 + "\n"

        for i, assistant in enumerate(assistants, 1):
            if not assistant.enabled:
                continue

            status = "✅" if assistant.name == active_name else "⚪"
            menu += f"{i}. {status} {assistant.name} ({assistant.type.value})\n"
            if assistant.name == active_name:
                menu += f"   📝 Model: {assistant.model}\n"
                menu += f"   🌡️  Temperature: {assistant.temperature}\n"

        menu += f"\n현재 활성화: {active_name}\n"
        return menu