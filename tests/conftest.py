import pytest
import os


@pytest.fixture(autouse=True)
def set_env_var(monkeypatch):
    """
    Overrides key environment variables to avoid accidentally using real
    credentials.
    """
    monkeypatch.setenv("APTIBLE_TOKEN", "foobar")
    monkeypatch.setenv("APTIBLE_API_ROOT_URL", "https://localhost:3000")
    monkeypatch.setenv("APTIBLE_AUTH_ROOT_URL", "https://localhost:3001")

    assert os.getenv("APTIBLE_TOKEN") == "foobar"
    assert os.getenv("APTIBLE_API_ROOT_URL") == "https://localhost:3000"
    assert os.getenv("APTIBLE_AUTH_ROOT_URL") == "https://localhost:3001"
