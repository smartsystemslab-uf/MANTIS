import sys
from pathlib import Path

# tests/ has no __init__.py, so pytest's rootdir insertion adds tests/
# itself to sys.path, not its parent -- `import mcp_server` then only
# resolves by accident, under `python -m pytest` (which also inserts CWD).
# The plain `pytest` entry point CI actually runs does not get that
# accident (see citi_banking_backend/tests/conftest.py's identical fix).
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
