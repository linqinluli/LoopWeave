"""Constants for LoopWeave runtime: environment variable names, default paths, and ports."""

from __future__ import annotations

import os
from pathlib import Path


# ---------------------------------------------------------------------------
# Environment variable names
# ---------------------------------------------------------------------------

ENV_LOOPWEAVE_ADDRESS = "LOOPWEAVE_ADDRESS"
"""Service address, e.g. http://127.0.0.1:10610"""

ENV_LOOPWEAVE_API_KEY = "LOOPWEAVE_API_KEY"  # pragma: allowlist secret
"""API authentication key"""

ENV_LOOPWEAVE_CONFIG = "LOOPWEAVE_CONFIG"
"""Path to config file"""

ENV_LOOPWEAVE_MODEL_PATH = "LOOPWEAVE_MODEL_PATH"
"""Model path for auto-generating minimal config"""

ENV_LOOPWEAVE_HOME = "LOOPWEAVE_HOME"
"""LoopWeave home directory, defaults to ~/.loopweave"""

ENV_LOOPWEAVE_HOST = "LOOPWEAVE_HOST"
"""Server bind address"""

ENV_LOOPWEAVE_PORT = "LOOPWEAVE_PORT"
"""Server bind port"""

ENV_LOOPWEAVE_ENABLE_AUTO_CONNECT = "LOOPWEAVE_ENABLE_AUTO_CONNECT"
"""Whether to enable auto-connect, defaults to "1" (enabled)"""

# ---------------------------------------------------------------------------
# Defaults
# ---------------------------------------------------------------------------

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 10610

# ---------------------------------------------------------------------------
# Derived paths (resolved at import time, but functions allow override)
# ---------------------------------------------------------------------------


def get_loopweave_home() -> Path:
    """Return the LOOPWEAVE_HOME directory, defaulting to ~/.loopweave."""
    return Path(os.environ.get(ENV_LOOPWEAVE_HOME, Path.home() / ".loopweave"))


def get_address_file() -> Path:
    """Return the path to the server address file."""
    return get_loopweave_home() / "loopweave_current_server"


def get_default_config_path() -> Path:
    """Return the default config file path."""
    return get_loopweave_home() / "configs" / "loopweave_config.yaml"


def get_default_checkpoint_dir() -> Path:
    """Return the default checkpoint directory."""
    return get_loopweave_home() / "checkpoints"


def get_credentials_file() -> Path:
    """Return the path to the auto-generated credentials file."""
    return get_loopweave_home() / "credentials"


# ---------------------------------------------------------------------------
# Health check endpoint
# ---------------------------------------------------------------------------

HEALTHZ_PATH = "/api/v1/healthz"
"""Health check endpoint path used for service discovery."""

HEALTHZ_TIMEOUT = 2.0
"""Timeout in seconds for a single health check request."""

STARTUP_TIMEOUT = 120.0
"""Maximum seconds to wait for an embedded service to become healthy."""

STARTUP_POLL_INTERVAL = 0.5
"""Seconds between health check polls during startup."""
