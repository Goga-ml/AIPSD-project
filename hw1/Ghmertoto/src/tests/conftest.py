import sys
from pathlib import Path

# src/ modules import each other by bare name (they also run as scripts), so put src/ on the path.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pytest  # noqa: E402


@pytest.fixture(autouse=True)
def no_retry_wait(monkeypatch):
    """Retry tests should not sleep for real."""
    import classifier
    monkeypatch.setattr(classifier, "RETRY_DELAY_S", 0)
