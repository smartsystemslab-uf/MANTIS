"""Post-Paper Extension: additional banking workloads (coding plan §11).

Covers the new dispute-filing/tracking capability -- a genuinely new
front-office business process, not a new prompt into an existing
workflow (see dispute_resolution_agent in
src/mantis/banking/front_office/__init__.py). Tests the repository layer
directly (against a real temp SQLite db, not a mock) and the tool
wrappers on top of it, plus that the new agent/tools are correctly
reflected in the domain-scoped inventory.
"""
import json
import tempfile
from pathlib import Path

import pytest

from mantis.banking.infra.repository import BankingRepository


@pytest.fixture
def repo(monkeypatch):
    with tempfile.TemporaryDirectory() as tmpdir:
        r = BankingRepository(db_path=Path(tmpdir) / "test_banking.db")
        r.initialize()
        # Tool wrappers import the module-level `repo` singleton directly,
        # so point it at this test's isolated db for the duration of the test.
        monkeypatch.setattr("mantis.banking.tools.dispute_tools.repo", r)
        yield r


def test_create_dispute_round_trips_through_real_sqlite(repo):
    created = repo.create_dispute("CUST-001", "TXN-1001", "Does not recognize the charge")
    assert created["status"] == "filed"
    assert created["dispute_id"].startswith("DSP-")

    fetched = repo.get_dispute(created["dispute_id"])
    assert fetched["customer_id"] == "CUST-001"
    assert fetched["transaction_id"] == "TXN-1001"
    assert fetched["status"] == "filed"


def test_get_dispute_returns_none_for_unknown_id(repo):
    assert repo.get_dispute("DSP-DOESNOTEXIST") is None


def test_file_dispute_tool_returns_valid_json_with_a_real_case_id(repo):
    from mantis.banking.tools.dispute_tools import file_dispute
    result = json.loads(file_dispute("CUST-001", "TXN-1001", "Does not recognize the charge"))
    assert result["status"] == "filed"
    assert result["dispute_id"].startswith("DSP-")


def test_get_dispute_status_tool_reports_not_found_for_unknown_id(repo):
    from mantis.banking.tools.dispute_tools import get_dispute_status
    result = json.loads(get_dispute_status("DSP-DOESNOTEXIST"))
    assert "error" in result


def test_get_dispute_status_tool_reflects_a_real_filed_dispute(repo):
    from mantis.banking.tools.dispute_tools import file_dispute, get_dispute_status
    filed = json.loads(file_dispute("CUST-001", "TXN-1001", "Does not recognize the charge"))
    status = json.loads(get_dispute_status(filed["dispute_id"]))
    assert status["status"] == "filed"
    assert status["transaction_id"] == "TXN-1001"


def test_dispute_resolution_agent_and_tools_appear_in_front_office_inventory():
    from mantis.runtime.adapter import NativeBankingAdapter
    inv = NativeBankingAdapter().inventory()
    assert "dispute_resolution_agent" in inv.domains["front_office"]["agents"]
    assert "file_dispute" in inv.domains["front_office"]["tools"]
    assert "get_dispute_status" in inv.domains["front_office"]["tools"]
    # And correctly excluded from the other two domains' scoped tool lists.
    assert "file_dispute" not in inv.domains["mid_office"]["tools"]
    assert "file_dispute" not in inv.domains["back_office"]["tools"]


def test_front_office_card_dispute_workflow_is_registered():
    from mantis.core.registry import scenario_registry, workflow_registry
    assert "front_office_card_dispute" in scenario_registry.all()
    assert workflow_registry.get("front_office_card_dispute") == "front_office"
