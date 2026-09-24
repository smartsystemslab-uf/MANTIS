"""A live run with no model key must say so up front, not fail deep in the runtime."""
import asyncio

import pytest

from mantis.cli.main import run_experiment


@pytest.fixture
def no_env_file(monkeypatch):
    import dotenv
    monkeypatch.setattr(dotenv, "load_dotenv", lambda *a, **k: False)


def _run(monkeypatch, **env):
    for k in ("MANTIS_MOCK_LLM", "UF_NAVIGATOR_API_KEY", "UF_NAVIGATOR_BASE_URL"):
        monkeypatch.delenv(k, raising=False)
    for k, v in env.items():
        monkeypatch.setenv(k, v)
    return asyncio.run(run_experiment("configs/campaigns/1_attack_tour/route_confusion.yaml"))


def test_live_run_without_a_key_exits_with_a_clear_message(monkeypatch, capsys, no_env_file):
    with pytest.raises(SystemExit) as exc:
        _run(monkeypatch)
    assert exc.value.code == 1
    err = capsys.readouterr().err
    assert "UF_NAVIGATOR_API_KEY" in err and "MANTIS_MOCK_LLM=1" in err


def test_a_custom_endpoint_is_not_blocked_by_the_preflight(monkeypatch, capsys, no_env_file):
    """A local OpenAI-compatible endpoint may need no key; the preflight must not stop it."""
    try:
        _run(monkeypatch, UF_NAVIGATOR_BASE_URL="http://127.0.0.1:1")
    except SystemExit:
        pass
    assert "No model key" not in capsys.readouterr().err
