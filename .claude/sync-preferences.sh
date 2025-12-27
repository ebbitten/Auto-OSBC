#!/bin/bash
# Claude Code Preferences Sync Script for Linux/macOS
# This script manages syncing Claude preferences between machines via Git

# Determine Claude Code directory based on OS
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    CLAUDE_USER_DIR="$HOME/Library/Application Support/Claude Code/User"
    VSCODE_USER_DIR="$HOME/Library/Application Support/Code/User"
elif [[ "$OSTYPE" == "msys" || "$OSTYPE" == "cygwin" ]]; then
    # Windows (Git Bash/MSYS2/Cygwin)
    CLAUDE_USER_DIR="$HOME/AppData/Roaming/Claude Code/User"
    VSCODE_USER_DIR="$HOME/AppData/Roaming/Code/User"
else
    # Linux
    CLAUDE_USER_DIR="$HOME/.config/claude-code/User"
    VSCODE_USER_DIR="$HOME/.config/Code/User"
fi

PROJECT_PREFS_DIR="$(dirname "$0")/user-preferences"

# Check if Claude Code is installed (standalone or as VS Code extension)
check_claude_installation() {
    if [ -d "$ACTIVE_USER_DIR" ]; then
        ACTIVE_USER_DIR="$ACTIVE_USER_DIR"
        echo "Using Claude Code standalone installation"
    elif [ -d "$VSCODE_USER_DIR" ]; then
        ACTIVE_USER_DIR="$VSCODE_USER_DIR"
        echo "Using VS Code with Claude Code extension"
    else
        echo "ERROR: Neither Claude Code nor VS Code found"
        echo "Expected locations:"
        echo "  $ACTIVE_USER_DIR"
        echo "  $VSCODE_USER_DIR"
        echo "Please install Claude Code or VS Code with Claude Code extension."
        exit 1
    fi
}

show_help() {
    cat << EOF
Claude Preferences Sync Tool

Usage: $0 [command]

Commands:
  export  - Export current Claude preferences to git
  import  - Import preferences from git to Claude
  status  - Check sync status
  help    - Show this help

Examples:
  $0 export   (run on machine with current preferences)
  $0 import   (run on machine to receive preferences)
EOF
}

export_prefs() {
    echo "Exporting Claude Code preferences for cross-machine sync..."
    check_claude_installation

    # Create preferences directory if it doesn't exist
    mkdir -p "$PROJECT_PREFS_DIR"

    # Export core settings
    echo "Copying settings.json..."
    if [ -f "$ACTIVE_USER_DIR/settings.json" ]; then
        cp "$ACTIVE_USER_DIR/settings.json" "$PROJECT_PREFS_DIR/settings.json"
        echo "✓ settings.json exported"
    else
        echo "WARNING: settings.json not found or failed to copy"
    fi

    # Export keybindings
    echo "Copying keybindings.json..."
    if [ -f "$ACTIVE_USER_DIR/keybindings.json" ]; then
        cp "$ACTIVE_USER_DIR/keybindings.json" "$PROJECT_PREFS_DIR/keybindings.json"
        echo "✓ keybindings.json exported"
    else
        echo "WARNING: keybindings.json not found - using default keybindings"
        echo "{}" > "$PROJECT_PREFS_DIR/keybindings.json"
    fi

    # Export extensions list if it exists
    echo "Copying extensions.json..."
    if [ -f "$ACTIVE_USER_DIR/extensions.json" ]; then
        cp "$ACTIVE_USER_DIR/extensions.json" "$PROJECT_PREFS_DIR/extensions.json"
        echo "✓ extensions.json exported"
    else
        echo "WARNING: extensions.json not found - no extensions configured"
        echo "[]" > "$PROJECT_PREFS_DIR/extensions.json"
    fi

    # Document current setup
    echo "Documenting current setup..."
    cat > "$PROJECT_PREFS_DIR/setup-info.txt" << EOF
Claude Code Setup Information
Export Date: $(date)
Machine: $(hostname)
User: $(whoami)
OS: $(uname -s)
Claude User Directory: $ACTIVE_USER_DIR

Installed Extensions:
EOF

    # List installed extensions
    if [ -d "$ACTIVE_USER_DIR/extensions" ]; then
        ls -1 "$ACTIVE_USER_DIR/extensions" >> "$PROJECT_PREFS_DIR/setup-info.txt" 2>/dev/null || echo "No extensions found" >> "$PROJECT_PREFS_DIR/setup-info.txt"
    else
        echo "No extensions directory found" >> "$PROJECT_PREFS_DIR/setup-info.txt"
    fi

    echo ""
    echo "✓ Claude preferences exported to $PROJECT_PREFS_DIR"
    echo ""
    echo "Next steps:"
    echo "1. Review exported files to ensure they contain your preferences"
    echo "2. Commit these files to git:"
    echo "   git add .claude/user-preferences/"
    echo "   git commit -m 'Export Claude Code preferences for cross-machine sync'"
    echo "   git push origin multi-machine"
}

import_prefs() {
    echo "Importing Claude Code preferences from git..."
    check_claude_installation

    # Check if preferences directory exists
    if [ ! -d "$PROJECT_PREFS_DIR" ]; then
        echo "ERROR: No preferences found at $PROJECT_PREFS_DIR"
        echo "Run 'git pull origin multi-machine' first to sync preferences."
        exit 1
    fi

    # Create backup directory
    BACKUP_DIR="$ACTIVE_USER_DIR/backup-$(date +%Y%m%d-%H%M%S)"
    echo "Creating backup at $BACKUP_DIR..."
    mkdir -p "$BACKUP_DIR"
    
    # Backup existing files
    [ -f "$ACTIVE_USER_DIR/settings.json" ] && cp "$ACTIVE_USER_DIR/settings.json" "$BACKUP_DIR/"
    [ -f "$ACTIVE_USER_DIR/keybindings.json" ] && cp "$ACTIVE_USER_DIR/keybindings.json" "$BACKUP_DIR/"
    [ -f "$ACTIVE_USER_DIR/extensions.json" ] && cp "$ACTIVE_USER_DIR/extensions.json" "$BACKUP_DIR/"

    # Import settings
    echo "Importing settings.json..."
    if [ -f "$PROJECT_PREFS_DIR/settings.json" ]; then
        cp "$PROJECT_PREFS_DIR/settings.json" "$ACTIVE_USER_DIR/settings.json"
        echo "✓ settings.json imported"
    else
        echo "WARNING: settings.json not found in preferences"
    fi

    # Import keybindings
    echo "Importing keybindings.json..."
    if [ -f "$PROJECT_PREFS_DIR/keybindings.json" ]; then
        cp "$PROJECT_PREFS_DIR/keybindings.json" "$ACTIVE_USER_DIR/keybindings.json"
        echo "✓ keybindings.json imported"
    else
        echo "WARNING: keybindings.json not found in preferences"
    fi

    # Import extensions list
    echo "Importing extensions.json..."
    if [ -f "$PROJECT_PREFS_DIR/extensions.json" ]; then
        cp "$PROJECT_PREFS_DIR/extensions.json" "$ACTIVE_USER_DIR/extensions.json"
        echo "✓ extensions.json imported"
    else
        echo "WARNING: extensions.json not found in preferences"
    fi

    echo ""
    echo "✓ Claude preferences imported successfully"
    echo ""
    echo "IMPORTANT: Restart Claude Code completely to apply all settings"
    echo "           Close all Claude Code windows and restart the application"
}

check_status() {
    echo "Claude Preferences Sync Status"
    echo "=============================="
    echo ""

    # Check if project preferences exist
    if [ -d "$PROJECT_PREFS_DIR" ]; then
        echo "✓ Project preferences directory found"
        if [ -f "$PROJECT_PREFS_DIR/setup-info.txt" ]; then
            echo ""
            echo "Last export information:"
            cat "$PROJECT_PREFS_DIR/setup-info.txt"
        fi
    else
        echo "✗ No project preferences found"
        echo "  Run '$0 export' to export current preferences"
    fi

    echo ""
    # Check Claude installation and set ACTIVE_USER_DIR
    if [ -d "$CLAUDE_USER_DIR" ]; then
        ACTIVE_USER_DIR="$CLAUDE_USER_DIR"
        echo "✓ Claude Code standalone installation found at $ACTIVE_USER_DIR"
    elif [ -d "$VSCODE_USER_DIR" ]; then
        ACTIVE_USER_DIR="$VSCODE_USER_DIR"
        echo "✓ VS Code with Claude Code extension found at $ACTIVE_USER_DIR"
    else
        echo "✗ Neither Claude Code nor VS Code found"
        echo "  Expected: $CLAUDE_USER_DIR or $VSCODE_USER_DIR"
        ACTIVE_USER_DIR=""
    fi

    # Check for current preferences
    echo ""
    echo "Current preferences:"
    if [ -n "$ACTIVE_USER_DIR" ]; then
        [ -f "$ACTIVE_USER_DIR/settings.json" ] && echo "✓ settings.json" || echo "✗ settings.json"
        [ -f "$ACTIVE_USER_DIR/keybindings.json" ] && echo "✓ keybindings.json" || echo "✗ keybindings.json (using defaults)"
        [ -f "$ACTIVE_USER_DIR/extensions.json" ] && echo "✓ extensions.json" || echo "✗ extensions.json (no extensions)"
    else
        echo "✗ Cannot check - no installation found"
    fi
}

# Parse command line arguments
case "$1" in
    export)
        export_prefs
        ;;
    import)
        import_prefs
        ;;
    status)
        check_status
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        show_help
        ;;
esac