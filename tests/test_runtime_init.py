"""Tests for loopweave.runtime init/shutdown/is_initialized flow."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

import loopweave


@pytest.fixture(autouse=True)
def reset_runtime():
    """Ensure runtime state is clean before and after each test."""
    loopweave.shutdown()
    yield
    loopweave.shutdown()


class TestInit:
    @patch("loopweave.runtime.discover", return_value="http://localhost:10610")
    @patch("loopweave.runtime.tinker.ServiceClient")
    def test_init_connected_mode(self, mock_client_cls, mock_discover):
        mock_client_cls.return_value = MagicMock()
        loopweave.init()
        assert loopweave.is_initialized()
        # Should be in connected mode
        from loopweave.runtime import _mode

        assert _mode == "connected"

    @patch("loopweave.runtime.discover", return_value="http://localhost:10610")
    @patch("loopweave.runtime.tinker.ServiceClient")
    def test_init_idempotent(self, mock_client_cls, mock_discover):
        mock_client_cls.return_value = MagicMock()
        loopweave.init()
        loopweave.init()  # should not raise
        assert loopweave.is_initialized()

    @patch("loopweave.runtime.discover", return_value="http://localhost:10610")
    @patch("loopweave.runtime.tinker.ServiceClient")
    def test_init_raises_on_reinit_when_flag_false(self, mock_client_cls, mock_discover):
        mock_client_cls.return_value = MagicMock()
        loopweave.init()
        with pytest.raises(RuntimeError, match="already initialized"):
            loopweave.init(ignore_reinit_error=False)

    @patch("loopweave.runtime.discover", return_value=None)
    def test_init_raises_when_no_service_and_no_config(self, mock_discover, tmp_path, monkeypatch):
        monkeypatch.setenv("LOOPWEAVE_HOME", str(tmp_path))
        monkeypatch.delenv("LOOPWEAVE_CONFIG", raising=False)
        monkeypatch.delenv("LOOPWEAVE_MODEL_PATH", raising=False)
        with pytest.raises(RuntimeError, match="Cannot start LoopWeave"):
            loopweave.init()


class TestShutdown:
    @patch("loopweave.runtime.discover", return_value="http://localhost:10610")
    @patch("loopweave.runtime.tinker.ServiceClient")
    def test_shutdown_resets_state(self, mock_client_cls, mock_discover):
        mock_client_cls.return_value = MagicMock()
        loopweave.init()
        assert loopweave.is_initialized()
        loopweave.shutdown()
        assert not loopweave.is_initialized()

    def test_shutdown_when_not_initialized(self):
        # Should not raise
        loopweave.shutdown()


class TestGetServiceClient:
    @patch("loopweave.runtime.discover", return_value="http://localhost:10610")
    @patch("loopweave.runtime.tinker.ServiceClient")
    def test_returns_client_after_init(self, mock_client_cls, mock_discover):
        mock_instance = MagicMock()
        mock_client_cls.return_value = mock_instance
        loopweave.init()
        client = loopweave.get_service_client()
        assert client is mock_instance

    @patch("loopweave.runtime.discover", return_value="http://localhost:10610")
    @patch("loopweave.runtime.tinker.ServiceClient")
    def test_auto_init_on_get_service_client(self, mock_client_cls, mock_discover):
        mock_client_cls.return_value = MagicMock()
        # Should auto-init
        client = loopweave.get_service_client()
        assert loopweave.is_initialized()
        assert client is not None

    def test_raises_when_auto_connect_disabled(self, monkeypatch):
        monkeypatch.setenv("LOOPWEAVE_ENABLE_AUTO_CONNECT", "0")
        with pytest.raises(RuntimeError, match="auto-connect is disabled"):
            loopweave.get_service_client()


class TestIsInitialized:
    def test_false_initially(self):
        assert not loopweave.is_initialized()

    @patch("loopweave.runtime.discover", return_value="http://localhost:10610")
    @patch("loopweave.runtime.tinker.ServiceClient")
    def test_true_after_init(self, mock_client_cls, mock_discover):
        mock_client_cls.return_value = MagicMock()
        loopweave.init()
        assert loopweave.is_initialized()
