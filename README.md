# Ward Security System

<p align="center">
  <img src="assets/ward.png" alt="Ward Security System" width="200"/>
</p>


[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**Ward** is a lightweight permission management system that protects your terminal interactions with AI assistants and human collaborators. It prevents unauthorized actions while providing intelligent guidance for the next steps.

## 🤖 Why Ward is Essential

In today's AI-driven development environment, tools like **Claude**, **GitHub Copilot**, and **ChatGPT** have become indispensable partners in coding. However, these powerful AI assistants sometimes attempt actions that could:

- ❌ Delete important files by mistake
- ❌ Modify system configurations unintentionally
- ❌ Execute harmful commands with full system access
- ❌ Access sensitive data beyond project boundaries
- ❌ Make irreversible changes without human oversight

**Ward acts as a intelligent safety layer** that:
- ✅ **Protects** your system from AI overreach
- ✅ **Guides** AI assistants with clear constraints
- ✅ **Educates** both AI and humans about safe operations
- ✅ **Maintains** productivity while ensuring security

## 🚀 Key Features

### 🛡️ AI Safety & Security
- **Terminal Integration**: Seamlessly integrates with your existing shell
- **Command Filtering**: Whitelist/blacklist dangerous commands automatically
- **Directory Protection**: Restrict AI access to sensitive system directories
- **Real-time Monitoring**: Track and log all AI-initiated actions
- **Smart Suggestions**: Provide safe alternatives to blocked operations

### 🤝 AI-Human Collaboration
- **Permission Prompts**: AI assistants can ask for permission before actions
- **Contextual Guidance**: Intelligent hints about what operations are safe
- **Progress Tracking**: Monitor AI work progress with structured feedback
- **Safe Experimentation**: Allow AI to work within defined boundaries

### ⚡ Lightweight & Fast
- **Zero Configuration**: Works out of the box with sensible defaults
- **Minimal Overhead**: No noticeable impact on terminal performance
- **Simple Setup**: One-command installation and activation
- **Cross-platform**: Linux, macOS, and Windows support

## 🎯 Perfect Use Cases

### AI Assistant Integration
```bash
# Claude wants to modify files - Ward checks permissions
claude> "I'll help you refactor the authentication module"
ward> ✅ Command allowed: ls, cat, grep, sed in src/auth/
ward> 🎯 Suggestion: Use 'ward-cli handle add' to track this task

# Copilot attempts system-wide changes
copilot> "Let me update system configurations"
ward> ❌ BLOCKED: System directory access denied
ward> 💡 Hint: Use 'ward-cli check /etc' to see what's allowed
```

### Team Collaboration Safety
```bash
# New team member joins project
developer> "I'll clean up the project structure"
ward> ✅ Basic file operations allowed in current directory
ward> ⚠️  WARNING: rm commands require explicit permission
ward> 📝 Use 'ward-cli comment' to document destructive changes
```

### Learning & Development
```bash
# Learning environment for students
student> "I want to understand system internals"
ward> 📚 Safe exploration mode activated
ward> 🔒 Sensitive system areas protected
ward> 💡 Educational hints provided for each command
```

## 📦 Installation

### Using UV (Recommended)
```bash
# Install as a tool
uv tool install --from git+https://github.com/yamonco/ward.git ward

# Or run directly without installation
uvx --from git+https://github.com/yamonco/ward.git ward-cli status

# Initialize for AI interaction
ward-init ai-project
cd ai-project
```

### Direct Download
```bash
# Download and install
wget https://github.com/yamonco/ward/releases/latest/download/ward-bash.tar.gz
tar -xzf ward-bash.tar.gz
cd ward-bash
./setup-ward.sh
```

## 🏁 Quick Start with AI

### Step 1: Initialize AI-Safe Environment
```bash
# Create AI-ready project
mkdir ai-secure-project
cd ai-secure-project

# Set up AI-friendly policies
echo "@description: AI-Assisted Development Project
@whitelist: ls cat pwd echo grep sed awk git python npm node code vim
@blacklist: rm -rf / sudo su chmod chown docker kubectl
@allow_ai_handles: true
@ai_guidance: true
@max_ai_operations: 10" > .ward

# Verify AI safety setup
ward-cli status
```

### Step 2: Start AI Collaboration
```bash
# Activate AI-safe shell
ward-shell

# Now Claude/Copilot can work safely within these boundaries
# AI assistants will automatically be guided by Ward's policies
```

## 🤖 AI Assistant Integration Examples

### Claude + Ward Synergy
```bash
# Claude wants to help with code refactoring
claude> "I'll analyze and improve your codebase structure"
ward> ✅ AI assistance mode activated
ward> 📊 Current project: 15 files, 3 directories
ward> 🎯 Safe operations: read, analyze, suggest modifications
ward> ❌ Restricted: file deletion, system changes

# Claude gets intelligent guidance
ward> 💡 For refactoring, consider:
#   1. Read existing code with 'cat' and 'grep'
#   2. Create analysis file with suggestions
#   3. Use 'ward-cli handle add' to track changes
```

### GitHub Copilot + Ward Protection
```bash
# Copilot suggests system modifications
copilot> "Let me optimize your development environment"
ward> 🔍 Checking suggested commands...
ward> ⚠️  Potentially risky: 'npm install -g some-package'
ward> 🛡️ Protection: Requires manual confirmation
ward> 💡 Safer alternative: 'npm install --save-dev some-package'
```

### ChatGPT + Ward Boundaries
```bash
# ChatGPT explores your project
chatgpt> "I'll help you understand the codebase"
ward> 📚 Project Analysis Mode: ON
ward> ✅ Allowed: 'find', 'grep', 'cat', 'head', 'tail'
ward> 📊 Progress: 5/15 files analyzed
ward> 💡 Next suggestion: Check 'README.md' for project overview
```

## 🔧 Advanced Configuration

### AI-Specific Policy Examples
```bash
# AI Development Environment
echo "@description: AI-Optimized Development
@whitelist: ls cat pwd echo grep sed awk git python node npm yarn
@ai_whitelist: handle comment analyze suggest review
@ai_restrictions: no_file_deletion, no_system_access
@ai_guidance_level: detailed
@ai_operation_limit: 50" > .ward

# Learning Environment
echo "@description: Educational AI Sandbox
@whitelist: ls cat echo grep head tail wc find
@ai_mode: educational
@ai_explain_denials: true
@ai_suggest_alternatives: true
@ai_progress_hints: true" > .ward
```

### AI Permission Management
```bash
# Allow specific AI operations
ward-cli ai allow "file_modification" --scope "src/"

# Review AI activity
ward-cli ai audit --last 24h

# Set AI operation limits
ward-cli ai limit --operations 100 --timeframe "1 hour"
```

## 🛠️ Usage with AI Assistants

### Real-time AI Protection
```bash
# Ward automatically intercepts and guides AI commands
$ ai_assistant_suggests_delete_ward_config
ward> 🚫 BLOCKED: Attempting to modify Ward configuration
ward> 💡 AI Assistant: This action requires explicit permission
ward> 📋 To proceed: Use 'ward-cli ai override --confirm' with justification

# Ward provides safe alternatives
ward> ✅ Suggested safe alternative:
#   - Review configuration with 'ward-cli config show'
#   - Create backup with 'ward-cli export config-backup.json'
#   - Submit change request with 'ward-cli ai request-change'
```

### AI Task Tracking
```bash
# Track AI-assisted work
ward-cli ai track start "API refactoring" --model claude-3.5
ward-cli ai track add-file "modified auth.py" --ai-generated
ward-cli ai track add-comment "Improved error handling" --ai-explanation
ward-cli ai track complete --verified

# Generate AI work report
ward-cli ai report --format markdown --include-suggestions
```

## 📊 AI Integration Benefits

### Enhanced AI Safety
- **Prevents accidental data loss** from AI mistakes
- **Blocks unauthorized system access** attempts
- **Provides educational feedback** for AI learning
- **Maintains audit trail** of all AI operations

### Improved AI Productivity
- **Clear boundaries** help AI work more effectively
- **Intelligent suggestions** speed up development
- **Context-aware guidance** reduces trial and error
- **Safe experimentation** encourages innovation

### Team Collaboration
- **Consistent AI behavior** across team members
- **Shared AI policies** for project safety
- **Centralized AI activity** monitoring and review
- **Onboarding assistance** for new AI users

## 🎯 Real-World Success Stories

### Company A: AI Code Review Integration
> *"Ward saved us from potential disaster when our AI assistant attempted to delete our production database credentials. The smart protection and guidance features are now essential for our AI-powered development workflow."* - DevOps Lead

### Startup B: Educational AI Partnership
> *"We use Ward to teach our junior developers how to work with AI assistants safely. The real-time guidance and protection features have accelerated their learning while maintaining code security."* - CTO

### Team C: Multi-AI Environment
> *"With Claude, Copilot, and ChatGPT all working on our codebase, Ward provides the unified safety layer we need. The AI-specific policies and monitoring give us confidence in our AI-assisted development."* - Engineering Manager

## 🚀 Getting Started with AI

1. **Install Ward** in your development environment
2. **Create AI-safe project** policies
3. **Enable AI assistance mode** with `ward-shell`
4. **Start collaborating** with your AI assistants
5. **Monitor and refine** AI interactions over time

## 🤝 Contributing

We welcome contributions to enhance AI safety and collaboration! See our [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

1. Fork this repository
2. Create a feature branch for AI enhancements
3. Test thoroughly with various AI assistants
4. Submit your Pull Request with AI use cases

## 📄 License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## 🆘 Support

- [GitHub Discussions](https://github.com/yamonco/ward/discussions) - AI integration questions
- [Issue reporting](https://github.com/yamonco/ward/issues) - Bug reports and feature requests
- [AI safety discussions](security@yamonco.com) - AI security concerns

## 🏢 yamonco

Ward is developed and maintained by [yamonco](https://github.com/yamonco) with a focus on AI-human collaboration safety.

## ❤️ Sponsors

If Ward helps you work safely with AI assistants, please consider supporting us:

[![Sponsor yamonco](https://img.shields.io/github/sponsors/yamonco?style=for-the-badge&logo=github&logoColor=white)](https://github.com/sponsors/yamonco)

Your support helps us enhance AI safety features and maintain this essential tool for the AI-powered development community.

---

**🤖 Ward Security System - Your AI Assistant's Safety Co-pilot**