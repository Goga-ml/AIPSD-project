import socket
import sys
import threading
import time
from pathlib import Path

import pytest
import uvicorn

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import app as app_module  # noqa: E402


@pytest.fixture(autouse=True)
def mock_provider_env(monkeypatch):
    """Tests never touch a real provider, even if a .env says gemini."""
    monkeypatch.setenv("LLM_PROVIDER", "mock")
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)


@pytest.fixture
def use_provider(monkeypatch):
    """Swap in a fake provider: use_provider(async_gen_fn)."""

    def install(provider):
        monkeypatch.setattr(app_module, "get_provider", lambda: (provider, "fake-model"))

    return install


@pytest.fixture(scope="session")
def live_server():
    """A real uvicorn server on a free port, so streaming goes over a real socket."""
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        port = s.getsockname()[1]
    server = uvicorn.Server(uvicorn.Config(app_module.app, host="127.0.0.1", port=port, log_level="warning"))
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()
    deadline = time.monotonic() + 10
    while not server.started:
        if time.monotonic() > deadline:
            raise RuntimeError("uvicorn didn't start")
        time.sleep(0.02)
    yield f"http://127.0.0.1:{port}"
    server.should_exit = True
    thread.join(timeout=5)
