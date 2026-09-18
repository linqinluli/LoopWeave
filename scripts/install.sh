#!/bin/bash
# LoopWeave Installation Script
# Usage: /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/anonymous/loopweave/main/scripts/install.sh)"

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
LOOPWEAVE_HOME="${LOOPWEAVE_HOME:-$HOME/.loopweave}"
LOOPWEAVE_BIN="$LOOPWEAVE_HOME/bin"
LOOPWEAVE_VENV="$LOOPWEAVE_HOME/venv"
PYTHON_VERSION="3.12"
LOOPWEAVE_PYPI_REQUIREMENT="${LOOPWEAVE_PYPI_REQUIREMENT:-loopweave[backend,persistence]>=0.1.8}"
LOOPWEAVE_GIT_REPO="https://github.com/anonymous/loopweave.git"
INSTALL_FROM_SOURCE=false
LOCAL_SOURCE_PATH=""
CLEAN_INSTALL=false

# Print functions
print_step() {
    echo -e "${BLUE}==>${NC} $1"
}

print_success() {
    echo -e "${GREEN}==>${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}Warning:${NC} $1"
}

print_error() {
    echo -e "${RED}Error:${NC} $1"
}

# Parse command line arguments
parse_args() {
    while [[ $# -gt 0 ]]; do
        case "$1" in
            --from-source)
                INSTALL_FROM_SOURCE=true
                shift
                ;;
            --local-source)
                LOCAL_SOURCE_PATH="$2"
                shift 2
                ;;
            --clean)
                CLEAN_INSTALL=true
                shift
                ;;
            --help|-h)
                echo "LoopWeave Installation Script"
                echo ""
                echo "Usage: install.sh [options]"
                echo ""
                echo "Options:"
                echo "  --from-source         Install from GitHub instead of PyPI"
                echo "  --local-source PATH   Install from local source directory (for development/CI)"
                echo "  --clean               Remove existing installation before installing"
                echo "  --help, -h            Show this help message"
                echo ""
                echo "The script installs LoopWeave with full backend support (GPU, persistence, flash-attn)."
                echo ""
                echo "Environment Variables:"
                echo "  LOOPWEAVE_HOME             Installation directory (default: ~/.loopweave)"
                echo "  LOOPWEAVE_PYPI_REQUIREMENT Override the default PyPI requirement"
                exit 0
                ;;
            *)
                print_error "Unknown option: $1"
                exit 1
                ;;
        esac
    done
}

# Detect OS and architecture
detect_platform() {
    OS="$(uname -s)"
    ARCH="$(uname -m)"

    case "$OS" in
        Linux)
            PLATFORM="linux"
            ;;
        Darwin)
            PLATFORM="macos"
            ;;
        *)
            print_error "Unsupported operating system: $OS"
            exit 1
            ;;
    esac

    case "$ARCH" in
        x86_64|amd64)
            ARCH="x86_64"
            ;;
        arm64|aarch64)
            ARCH="aarch64"
            ;;
        *)
            print_error "Unsupported architecture: $ARCH"
            exit 1
            ;;
    esac

    print_step "Detected platform: $PLATFORM ($ARCH)"
}

# Check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Install uv if not present
install_uv() {
  if command_exists uv; then
    print_step "uv is already installed"
    return
  fi

  print_step "Installing uv (Python package manager)..."

  # Primary: official installer (fast path)
  if ! curl -LsSf https://astral.sh/uv/install.sh | sh; then
    print_warning "uv install via curl failed. Falling back to pip install uv."
    print_warning "If you are in a restricted network, consider configuring a PyPI mirror."

    local PYTHON_BIN=""
    if command_exists python3; then
      PYTHON_BIN="python3"
    elif command_exists python; then
      PYTHON_BIN="python"
    else
      print_error "Python not found; cannot install uv. Please install python3 and re-run."
      exit 1
    fi

    "$PYTHON_BIN" -m pip install --user --upgrade uv
  fi

  # Source env files if present (for curl installer case)
  if [ -f "$HOME/.local/bin/env" ]; then
    source "$HOME/.local/bin/env"
  elif [ -f "$HOME/.cargo/env" ]; then
    source "$HOME/.cargo/env"
  fi

  # Ensure PATH contains common locations
  export PATH="$HOME/.local/bin:$HOME/.cargo/bin:$PATH"

  if ! command_exists uv; then
    print_error "Failed to install uv. Please install it manually and re-run."
    exit 1
  fi

  print_success "uv installed successfully"
}

# Create loopweave directory structure
create_directories() {
    print_step "Creating LoopWeave directory structure..."
    mkdir -p "$LOOPWEAVE_HOME"
    mkdir -p "$LOOPWEAVE_BIN"
    mkdir -p "$LOOPWEAVE_HOME/checkpoints"
    mkdir -p "$LOOPWEAVE_HOME/configs"
    mkdir -p "$LOOPWEAVE_HOME/scripts"
}

# Create Python virtual environment and install loopweave
install_loopweave() {
    print_step "Creating Python $PYTHON_VERSION virtual environment..."

    # Remove existing venv if present
    if [ -d "$LOOPWEAVE_VENV" ]; then
        rm -rf "$LOOPWEAVE_VENV"
    fi

    uv venv --python "$PYTHON_VERSION" "$LOOPWEAVE_VENV"

    print_step "Installing LoopWeave package..."

    # Determine package source
    if [ -n "$LOCAL_SOURCE_PATH" ]; then
        print_step "Installing from local source: $LOCAL_SOURCE_PATH"
        PACKAGE_SPEC="${LOCAL_SOURCE_PATH}[backend,persistence]"
    elif [ "$INSTALL_FROM_SOURCE" = true ]; then
        print_step "Installing from GitHub: $LOOPWEAVE_GIT_REPO"
        PACKAGE_SPEC="git+${LOOPWEAVE_GIT_REPO}#egg=loopweave[backend,persistence]"
    else
        print_step "Installing from PyPI: $LOOPWEAVE_PYPI_REQUIREMENT"
        PACKAGE_SPEC="$LOOPWEAVE_PYPI_REQUIREMENT"
    fi

    # Ensure the verl override file (pins verl to the #6551 commit) exists, then
    # install with it so registry/git resolves satisfy verl>=0.8,<0.9.
    setup_verl_override

    # PACKAGE_SPEC already includes the backend and persistence extras.
    uv pip install --python "$LOOPWEAVE_VENV/bin/python" --override "$VERL_OVERRIDE_FILE" "$PACKAGE_SPEC"

    print_success "LoopWeave installed successfully"
}

# Ensure the uv override file pinning verl to the #6551 commit exists at
# $VERL_OVERRIDE_FILE (prefer the bundled file, else download, else write it
# inline). See scripts/verl-git-override.txt for the rationale.
setup_verl_override() {
    mkdir -p "$(dirname "$VERL_OVERRIDE_FILE")"
    if [ -n "$LOCAL_SOURCE_PATH" ] && [ -f "$LOCAL_SOURCE_PATH/scripts/verl-git-override.txt" ]; then
        cp "$LOCAL_SOURCE_PATH/scripts/verl-git-override.txt" "$VERL_OVERRIDE_FILE"
        return
    fi

    local tmp_file="${VERL_OVERRIDE_FILE}.tmp"
    if curl -fsSL "$VERL_OVERRIDE_URL" -o "$tmp_file" 2>/dev/null; then
        mv "$tmp_file" "$VERL_OVERRIDE_FILE"
    else
        rm -f "$tmp_file"
        # Offline / pre-merge fallback. Keep in sync with pyproject [tool.uv]
        # override-dependencies and scripts/verl-git-override.txt.
        if [ ! -f "$VERL_OVERRIDE_FILE" ]; then
            printf '%s\n' "verl @ git+https://github.com/verl-project/verl.git@14574ecf52e310055e4d6e9f116bcb14d343d7e0" > "$VERL_OVERRIDE_FILE"
        fi
    fi
}

# URL for the flash-attn installation script
FLASH_ATTN_SCRIPT_URL="https://raw.githubusercontent.com/anonymous/loopweave/main/scripts/install_flash_attn.py"

# uv override file that pins verl to the #6551 commit (numpy>=2 + runtime fixes).
# scripts/verl-git-override.txt is the canonical decision record and removal
# procedure. Pass it via --override on every supported install path.
VERL_OVERRIDE_URL="https://raw.githubusercontent.com/anonymous/loopweave/main/scripts/verl-git-override.txt"
VERL_OVERRIDE_FILE="$LOOPWEAVE_HOME/scripts/verl-git-override.txt"

# Install flash-attn from precompiled wheels (avoids lengthy compilation)
# Also stores the script locally for later use by install-backend command
install_flash_attn() {
    print_step "Installing flash-attn from precompiled wheels..."

    local script_path="$LOOPWEAVE_HOME/scripts/install_flash_attn.py"

    # Copy or download the flash-attn install script to local storage
    if [ -n "$LOCAL_SOURCE_PATH" ] && [ -f "$LOCAL_SOURCE_PATH/scripts/install_flash_attn.py" ]; then
        print_step "Using local flash-attn install script"
        cp "$LOCAL_SOURCE_PATH/scripts/install_flash_attn.py" "$script_path"
    else
        # Download the script from GitHub and store locally
        if ! curl -fsSL "$FLASH_ATTN_SCRIPT_URL" -o "$script_path"; then
            print_warning "Could not download flash-attn install script, skipping"
            return
        fi
    fi

    # Run the script and check exit code
    if "$LOOPWEAVE_VENV/bin/python" "$script_path"; then
        print_success "flash-attn installation complete"
    else
        print_warning "flash-attn installation failed. This is optional, so installation will continue."
    fi
}

# Create the loopweave wrapper script
# Note: The wrapper is intentionally embedded in this install script (heredoc) rather than
# being a separate file. This ensures the wrapper is always in sync with the install script
# version and simplifies distribution. When updating the wrapper, edit the heredoc below.
# The wrapper provides CLI commands (launch, version, upgrade, etc.) that delegate to the
# Python module while handling configuration defaults and environment setup.
create_wrapper() {
    print_step "Creating loopweave command wrapper..."

    cat > "$LOOPWEAVE_BIN/loopweave" << 'WRAPPER_EOF'
#!/bin/bash
# LoopWeave CLI Wrapper
# This script provides a convenient interface to the LoopWeave server
# Generated by install.sh - edit the heredoc in install.sh to modify

set -e

LOOPWEAVE_HOME="${LOOPWEAVE_HOME:-$HOME/.loopweave}"
LOOPWEAVE_VENV="$LOOPWEAVE_HOME/venv"
LOOPWEAVE_PYTHON="$LOOPWEAVE_VENV/bin/python"
LOOPWEAVE_PYPI_REQUIREMENT="${LOOPWEAVE_PYPI_REQUIREMENT:-loopweave[backend,persistence]>=0.1.8}"
VERL_OVERRIDE_URL="${LOOPWEAVE_VERL_OVERRIDE_URL:-https://raw.githubusercontent.com/anonymous/loopweave/main/scripts/verl-git-override.txt}"
VERL_OVERRIDE_FILE="$LOOPWEAVE_HOME/scripts/verl-git-override.txt"

# Verify installation
if [ ! -f "$LOOPWEAVE_PYTHON" ]; then
    echo "Error: LoopWeave installation not found at $LOOPWEAVE_HOME"
    echo "Please reinstall LoopWeave using:"
    echo '  /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/anonymous/loopweave/main/scripts/install.sh)"'
    exit 1
fi

# Atomically refresh the release-channel override before upgrades. Keep the
# remote file at this stable URL after the workaround is removed (it can become
# comment-only), so old wrappers stop applying the pin instead of retaining it.
refresh_verl_override() {
    mkdir -p "$(dirname "$VERL_OVERRIDE_FILE")"
    local tmp_file="${VERL_OVERRIDE_FILE}.tmp"
    if curl -fsSL "$VERL_OVERRIDE_URL" -o "$tmp_file" 2>/dev/null; then
        mv "$tmp_file" "$VERL_OVERRIDE_FILE"
        return
    fi

    rm -f "$tmp_file"
    if [ -f "$VERL_OVERRIDE_FILE" ]; then
        echo "Warning: could not refresh the Verl override; using the existing file."
        return
    fi

    echo "Error: Verl override is unavailable. Re-run the LoopWeave installer."
    return 1
}

# Handle commands
case "${1:-}" in
    launch)
        shift
        # Pass all arguments directly to the CLI (single source of truth)
        exec "$LOOPWEAVE_PYTHON" -m loopweave launch "$@"
        ;;

    version|--version|-v)
        "$LOOPWEAVE_PYTHON" -c "import loopweave; print(f'LoopWeave version: {loopweave.__version__}')" 2>/dev/null || \
        "$LOOPWEAVE_PYTHON" -c "from importlib.metadata import version; print(f'LoopWeave version: {version(\"loopweave\")}')"
        ;;

    upgrade)
        shift
        # Parse upgrade options
        UPGRADE_FROM_SOURCE=false
        UPGRADE_LOCAL_SOURCE=""
        while [[ $# -gt 0 ]]; do
            case "$1" in
                --from-source)
                    UPGRADE_FROM_SOURCE=true
                    shift
                    ;;
                --local-source)
                    UPGRADE_LOCAL_SOURCE="$2"
                    shift 2
                    ;;
                *)
                    echo "Unknown option: $1"
                    echo "Usage: loopweave upgrade [--from-source | --local-source PATH]"
                    exit 1
                    ;;
            esac
        done

        echo "Upgrading LoopWeave..."
        # verl is pinned to the #6551 commit via a uv override file placed at
        # install time (scripts/verl-git-override.txt). Use --override (not a
        # direct requirement): the commit reports 0.9.0.dev0, which a normal
        # requirement can't satisfy against verl>=0.8,<0.9. Once verl publishes
        # a release containing #6551, keep the remote file but make it
        # comment-only so existing wrappers refresh away the temporary pin.
        LOCAL_VERL_OVERRIDE="$UPGRADE_LOCAL_SOURCE/scripts/verl-git-override.txt"
        if [ -n "$UPGRADE_LOCAL_SOURCE" ] && [ -f "$LOCAL_VERL_OVERRIDE" ]; then
            cp "$LOCAL_VERL_OVERRIDE" "$VERL_OVERRIDE_FILE"
        else
            refresh_verl_override
        fi
        if [ -n "$UPGRADE_LOCAL_SOURCE" ]; then
            echo "Upgrading from local source: $UPGRADE_LOCAL_SOURCE"
            uv pip install --python "$LOOPWEAVE_PYTHON" --upgrade --override "$VERL_OVERRIDE_FILE" "${UPGRADE_LOCAL_SOURCE}[backend,persistence]"
        elif [ "$UPGRADE_FROM_SOURCE" = true ]; then
            # Repo is overridable (default: upstream main) so CI / advanced users
            # can exercise the real VCS clone+build+resolve path against a
            # specific checkout, e.g. LOOPWEAVE_GIT_URL="file://$GITHUB_WORKSPACE@$GITHUB_SHA".
            LOOPWEAVE_GIT_URL="${LOOPWEAVE_GIT_URL:-https://github.com/anonymous/loopweave.git}"
            echo "Upgrading from Git: git+${LOOPWEAVE_GIT_URL}"
            uv pip install --python "$LOOPWEAVE_PYTHON" --upgrade --override "$VERL_OVERRIDE_FILE" "git+${LOOPWEAVE_GIT_URL}#egg=loopweave[backend,persistence]"
        else
            uv pip install --python "$LOOPWEAVE_PYTHON" --upgrade --override "$VERL_OVERRIDE_FILE" "$LOOPWEAVE_PYPI_REQUIREMENT"
        fi

        # Also update flash-attn
        echo ""
        echo "Updating flash-attn..."
        FLASH_SCRIPT_PATH="$LOOPWEAVE_HOME/scripts/install_flash_attn.py"
        if [ -n "$UPGRADE_LOCAL_SOURCE" ] && [ -f "$UPGRADE_LOCAL_SOURCE/scripts/install_flash_attn.py" ]; then
            cp "$UPGRADE_LOCAL_SOURCE/scripts/install_flash_attn.py" "$FLASH_SCRIPT_PATH"
        elif [ ! -f "$FLASH_SCRIPT_PATH" ]; then
            FLASH_SCRIPT_URL="https://raw.githubusercontent.com/anonymous/loopweave/main/scripts/install_flash_attn.py"
            mkdir -p "$LOOPWEAVE_HOME/scripts"
            curl -fsSL "$FLASH_SCRIPT_URL" -o "$FLASH_SCRIPT_PATH" 2>/dev/null || true
        fi
        if [ -f "$FLASH_SCRIPT_PATH" ]; then
            "$LOOPWEAVE_PYTHON" "$FLASH_SCRIPT_PATH" || echo "Warning: flash-attn update failed (optional)"
        fi

        echo ""
        echo "LoopWeave upgraded successfully!"
        ;;

    uninstall)
        echo "Uninstalling LoopWeave..."
        read -p "This will remove $LOOPWEAVE_HOME. Are you sure? [y/N] " -n 1 -r
        echo
        if [[ "$REPLY" =~ ^[Yy]$ ]]; then
            rm -rf "$LOOPWEAVE_HOME"
            echo "LoopWeave uninstalled. Please remove $LOOPWEAVE_HOME/bin from your PATH."
        else
            echo "Uninstall cancelled."
        fi
        ;;

    help|--help|-h)
        echo "LoopWeave - Tenant-unified Fine-Tuning Server"
        echo ""
        echo "Usage: loopweave <command> [options]"
        echo ""
        echo "Commands:"
        echo "  launch            Start the LoopWeave server"
        echo "  version           Show LoopWeave version"
        echo "  upgrade           Upgrade LoopWeave to the latest version"
        echo "                    Options: --from-source, --local-source PATH"
        echo "  uninstall         Remove LoopWeave installation"
        echo "  help              Show this help message"
        echo ""
        echo "Launch options: Run 'loopweave launch --help' for all available options."
        echo ""
        echo "Environment Variables:"
        echo "  LOOPWEAVE_HOME            Installation directory (default: ~/.loopweave)"
        echo "  LOOPWEAVE_CONFIG          Default config file path"
        echo "  LOOPWEAVE_HOST            Default host for launch command"
        echo "  LOOPWEAVE_PORT            Default port for launch command"
        echo "  LOOPWEAVE_CHECKPOINT_DIR  Default checkpoint directory"
        echo "  LOOPWEAVE_LOG_LEVEL       Default log level"
        echo "  LOOPWEAVE_PYPI_REQUIREMENT Override the PyPI package requirement"
        echo "  LOOPWEAVE_VERL_OVERRIDE_URL Override the release-channel Verl override URL"
        echo ""
        echo "Examples:"
        echo "  loopweave launch --config loopweave_config.yaml"
        echo "  loopweave launch --port 10610 --config /path/to/loopweave_config.yaml"
        echo "  loopweave launch  # uses default config at ~/.loopweave/configs/loopweave_config.yaml"
        echo "  loopweave upgrade"
        echo ""
        echo "Documentation: https://github.com/anonymous/loopweave"
        ;;

    "")
        # No command provided, show help
        "$0" help
        ;;

    *)
        # Pass through to the loopweave module for any other commands
        exec "$LOOPWEAVE_PYTHON" -m loopweave "$@"
        ;;
esac
WRAPPER_EOF

    chmod +x "$LOOPWEAVE_BIN/loopweave"
    print_success "Wrapper script created at $LOOPWEAVE_BIN/loopweave"
}

# Create example configuration
create_example_config() {
    if [ ! -f "$LOOPWEAVE_HOME/configs/loopweave_config.yaml.example" ]; then
        print_step "Creating example configuration..."
        cat > "$LOOPWEAVE_HOME/configs/loopweave_config.yaml.example" << 'CONFIG_EOF'
# LoopWeave Server Configuration Example
# Copy this file to loopweave_config.yaml and customize for your setup

model_owner: local

supported_models:
  - model_name: Qwen/Qwen3-8B
    model_path: Qwen/Qwen3-8B  # HuggingFace model ID or local path
    max_model_len: 32768
    tensor_parallel_size: 1
    temperature: 0.7
    top_p: 1.0
    top_k: -1

  # Add more models as needed:
  # - model_name: meta-llama/Llama-2-7b-hf
  #   model_path: /path/to/local/model
  #   max_model_len: 4096
  #   tensor_parallel_size: 1

# API Key authentication
# Format: api_key: user_identifier
authorized_users:
  my-api-key: default
  # Add more API keys as needed:
  # another-key: another-user

# Optional: Persistence configuration
# persistence:
#   mode: DISABLE  # Options: DISABLE, REDIS, FILE
#   redis_url: "redis://localhost:6379/0"
#   namespace: "persistence-loopweave-server"
CONFIG_EOF
    fi
}

# Update shell configuration to add loopweave to PATH
update_shell_config() {
    print_step "Configuring shell PATH..."

    SHELL_NAME="$(basename "$SHELL")"
    SHELL_CONFIG=""

    case "$SHELL_NAME" in
        bash)
            if [ -f "$HOME/.bash_profile" ]; then
                SHELL_CONFIG="$HOME/.bash_profile"
            else
                SHELL_CONFIG="$HOME/.bashrc"
            fi
            ;;
        zsh)
            SHELL_CONFIG="$HOME/.zshrc"
            ;;
        fish)
            SHELL_CONFIG="$HOME/.config/fish/config.fish"
            ;;
        *)
            print_warning "Unknown shell: $SHELL_NAME. Please add $LOOPWEAVE_BIN to your PATH manually."
            return
            ;;
    esac

    # Check if PATH is already configured
    if [ -n "$SHELL_CONFIG" ] && [ -f "$SHELL_CONFIG" ]; then
        if grep -q "LOOPWEAVE_HOME" "$SHELL_CONFIG" 2>/dev/null; then
            print_step "PATH already configured in $SHELL_CONFIG"
            return
        fi
    fi

    # Add to shell config
    # Use $HOME literal so the config remains portable
    if [ -n "$SHELL_CONFIG" ]; then
        if [ "$SHELL_NAME" = "fish" ]; then
            mkdir -p "$(dirname "$SHELL_CONFIG")"
            echo "" >> "$SHELL_CONFIG"
            echo "# LoopWeave" >> "$SHELL_CONFIG"
            echo 'set -gx LOOPWEAVE_HOME $HOME/.loopweave' >> "$SHELL_CONFIG"
            echo 'fish_add_path $LOOPWEAVE_HOME/bin' >> "$SHELL_CONFIG"
        else
            echo "" >> "$SHELL_CONFIG"
            echo "# LoopWeave" >> "$SHELL_CONFIG"
            echo 'export LOOPWEAVE_HOME="$HOME/.loopweave"' >> "$SHELL_CONFIG"
            echo 'export PATH="$LOOPWEAVE_HOME/bin:$PATH"' >> "$SHELL_CONFIG"
        fi
        print_success "Added LoopWeave to PATH in $SHELL_CONFIG"
    fi
}

# Print completion message
print_completion() {
    echo ""
    echo -e "${GREEN}============================================${NC}"
    echo -e "${GREEN}  LoopWeave installation complete!${NC}"
    echo -e "${GREEN}============================================${NC}"
    echo ""
    echo "Installation directory: $LOOPWEAVE_HOME"
    echo ""
    echo "To get started:"
    echo ""
    echo "  1. Restart your terminal or run:"
    echo "     source ~/.$(basename "$SHELL")rc"
    echo ""
    echo "  2. Create a server configuration file:"
    echo "     cp $LOOPWEAVE_HOME/configs/loopweave_config.yaml.example $LOOPWEAVE_HOME/configs/loopweave_config.yaml"
    echo "     # Edit the file to configure your models and API keys"
    echo ""
    echo "  3. Launch the LoopWeave server:"
    echo "     loopweave launch"
    echo ""
    echo "For more information:"
    echo "  loopweave help"
    echo "  https://github.com/anonymous/loopweave"
    echo ""
}

# Main installation flow
main() {
    parse_args "$@"

    echo ""
    echo -e "${BLUE}============================================${NC}"
    echo -e "${BLUE}  LoopWeave Installer${NC}"
    echo -e "${BLUE}  Tenant-unified Fine-Tuning Server${NC}"
    echo -e "${BLUE}============================================${NC}"
    echo ""

    print_step "Installing with full backend support (GPU, persistence, flash-attn)"

    if [ -n "$LOCAL_SOURCE_PATH" ]; then
        print_step "Installing from local source: $LOCAL_SOURCE_PATH"
    elif [ "$INSTALL_FROM_SOURCE" = true ]; then
        print_step "Installing from GitHub (source)"
    else
        print_step "Installing from PyPI"
    fi

    # Clean existing installation if requested
    if [ "$CLEAN_INSTALL" = true ] && [ -d "$LOOPWEAVE_HOME" ]; then
        print_step "Cleaning existing installation at $LOOPWEAVE_HOME..."
        rm -rf "$LOOPWEAVE_HOME"
        print_success "Existing installation removed"
    fi

    detect_platform
    install_uv
    create_directories
    install_loopweave
    install_flash_attn
    create_wrapper
    create_example_config
    update_shell_config
    print_completion
}

# Run main
main "$@"
