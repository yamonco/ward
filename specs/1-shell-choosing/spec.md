# 1-shell-choosing

## Description
The Ward initialization process should automatically detect and allow users to select their preferred shell environment (bash, zsh, fish, etc.) when running `ward init`. This selection should configure Ward's prompt integration and activation scripts to work seamlessly with the user's chosen shell, ensuring the emoji prefix displays correctly across different shell environments.

## User Scenarios & Testing

### Scenario 1: Automatic Shell Detection
**User Story**: As a developer, when I run `ward init` for the first time, Ward should automatically detect my current shell and offer it as the default choice.

**Acceptance Criteria**:
- Ward detects the current shell from `$SHELL` environment variable
- Detected shell is presented as the recommended option
- User can accept the detected shell with a single keypress
- Detection works for bash, zsh, fish, and common shell variants

### Scenario 2: Manual Shell Selection
**User Story**: As a developer using multiple shells, I want to choose a specific shell for Ward integration even if it's different from my current shell.

**Acceptance Criteria**:
- Interactive menu shows all supported shells with visual indicators
- User can navigate options with arrow keys or number selection
- Selected shell is saved in Ward configuration
- Configuration persists across reboots and shell sessions

### Scenario 3: Shell Configuration Generation
**User Story**: As a developer, after selecting my shell, Ward should generate appropriate configuration files that work with my shell's prompt system.

**Acceptance Criteria**:
- Generates shell-specific activation scripts (bash: .bashrc modifications, zsh: .zshrc integration, fish: config.fish setup)
- Creates appropriate prompt integration for each shell type
- Handles Oh My Zsh, Powerlevel10k, and custom themes
- Preserves existing prompt customization while adding Ward prefix

### Scenario 4: Shell Switching and Reconfiguration
**User Story**: As a developer, I want to change my shell configuration later if I switch to a different shell or theme.

**Acceptance Criteria**:
- `ward config shell` command allows shell reconfiguration
- Properly cleans up previous shell configurations
- Maintains Ward functionality during shell transition
- Validates new shell compatibility before applying changes

## Functional Requirements

### FR1: Shell Detection and Selection
1. Detect current shell from `$SHELL` environment variable
2. Present interactive selection menu with detected shell as default
3. Support shell types: bash, zsh, fish, ksh, csh, tcsh
4. Validate shell availability on user's system
5. Save user's shell preference in Ward configuration

### FR2: Shell-Specific Configuration Generation
1. Generate appropriate activation scripts for each shell type:
   - Bash: Modify PS1 in .bashrc or create standalone script
   - Zsh: Handle PROMPT variable, Oh My Zsh themes, and agnoster/powerlevel10k
   - Fish: Create fish functions and modify fish_prompt
2. Create shell-compatible deactivation mechanisms
3. Handle shell-specific color and formatting syntax
4. Preserve existing prompt customization and themes

### FR3: Theme Integration
1. Detect popular shell themes and frameworks:
   - Oh My Zsh with custom themes
   - Powerlevel10k
   - Starship
   - Custom prompt configurations
2. Integrate Ward prefix without breaking existing themes
3. Provide fallback mechanisms for unknown themes
4. Support both left and right prompt modifications (zsh RPROMPT)

### FR4: Configuration Management
1. Store shell preference in `~/.ward/config.json`
2. Track original prompt configuration for restoration
3. Validate configuration changes before applying
4. Provide configuration reset functionality
5. Handle configuration conflicts gracefully

## Success Criteria

### Quantitative Metrics
- 95% of users successfully configure Ward on first attempt without manual intervention
- Support for 6+ shell types including bash, zsh, fish, ksh, csh, tcsh
- Compatibility with 10+ popular shell themes and frameworks
- Configuration setup time under 30 seconds
- Zero regression in existing Ward functionality

### Qualitative Metrics
- Users report seamless integration with their existing shell setup
- Ward emoji prefix displays correctly across all supported shells
- No need for users to manually edit shell configuration files
- Clean configuration management with proper cleanup and restoration
- Intuitive selection process with clear visual feedback

## Key Entities

### ShellConfiguration
- detected_shell: string (from $SHELL)
- selected_shell: string (user's choice)
- shell_theme: string (detected theme/framework)
- prompt_variables: object (shell-specific prompt variables)
- activation_method: string (rc_file, standalone_script, function)

### ShellProfile
- name: string (bash, zsh, fish, etc.)
- config_files: array (paths to shell configuration files)
- prompt_var: string (PS1, PROMPT, fish_prompt, etc.)
- activation_commands: array (shell-specific activation syntax)
- theme_detection: array (patterns to detect popular themes)

### ThemeIntegration
- theme_name: string (agnoster, powerlevel10k, starship, etc.)
- integration_method: string (prefix, segment, custom)
- compatibility_matrix: object (shell → integration_status)

## Assumptions

### Technical Assumptions
- Users have write permissions to their home directory and shell configuration files
- Shell environments follow standard configuration patterns (.bashrc, .zshrc, config.fish)
- Users are familiar with basic shell concepts and can identify their preferred shell
- Standard Unix/Linux file permissions apply to configuration files

### User Behavior Assumptions
- Users prefer automatic detection with manual override capability
- Users want minimal disruption to existing shell customization
- Users value clean, automatic configuration over manual setup
- Users may switch between shells and need reconfiguration capability

### Environment Assumptions
- Common shells (bash, zsh, fish) are available on target systems
- Shell themes follow predictable installation patterns
- Environment variables reliably indicate current shell context
- Terminal emulators support Unicode emoji display
