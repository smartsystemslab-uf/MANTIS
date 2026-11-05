import os
import sys
import tempfile
from pathlib import Path

import pytest

# tests/ has no __init__.py, so pytest's rootdir insertion adds tests/ itself
# to sys.path, not its parent -- `from app import ...` then only resolves by
# accident, under `python -m pytest` (which also inserts CWD). The plain
# `pytest` entry point CI actually runs does not get that accident, and
# fails every top-level `from app import ...` in this test package. Insert
# the real package root explicitly so both invocations behave identically.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

_TEST_DIR = Path(tempfile.mkdtemp(prefix="citi-p3-backend-tests-"))
os.environ["DATABASE_URL"] = f"sqlite:///{_TEST_DIR / 'backend.db'}"


@pytest.fixture(scope="session")
def client():
    from fastapi.testclient import TestClient

    from app.main import app

    with TestClient(app) as test_client:
        yield test_client

