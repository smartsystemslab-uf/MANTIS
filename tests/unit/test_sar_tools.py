"""Post-Paper Extension: additional banking workloads (coding plan §11).

Covers the new back-office SAR/exception-escalation capability -- a
genuinely new back-office business process, not a new prompt into the
existing EOD workflow (see sar_escalation_agent in
src/mantis/banking/back_office/__init__.py). Mirrors
test_dispute_tools.py's shape: repository layer against a real temp
SQLite db, the tool wrappers on top of it, and domain-scoped inventory
registration.
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
        monkeypatch.setattr("mantis.banking.tools.sar_tools.repo", r)
        yield r


def test_get_exception_returns_none_for_unknown_id(repo):
    assert repo.get_exception("EX-DOESNOTEXIST") is None


def test_create_sar_round_trips_through_real_sqlite(repo):
    exceptions = repo._all("SELECT exception_id FROM exceptions")
    exception_id = exceptions[0]["exception_id"]

    created = repo.create_sar(exception_id, "Unexplained repeated round-number mismatch", filed_by="sar_escalation_agent")
    assert created["status"] == "filed"
    assert created["sar_id"].startswith("SAR-")

    fetched = repo.get_sar(created["sar_id"])
    assert fetched["exception_id"] == exception_id
    assert fetched["status"] == "filed"


def test_get_sar_returns_none_for_unknown_id(repo):
    assert repo.get_sar("SAR-DOESNOTEXIST") is None


def test_get_exception_case_tool_reflects_the_seeded_exception(repo):
    from mantis.banking.tools.sar_tools import get_exception_case
    result = json.loads(get_exception_case("EX-SEEDED01"))
    assert result["exception_id"] == "EX-SEEDED01"
    assert result["status"] == "open"


def test_get_exception_case_tool_reports_not_found_for_unknown_id(repo):
    from mantis.banking.tools.sar_tools import get_exception_case
    result = json.loads(get_exception_case("EX-DOESNOTEXIST"))
    assert "error" in result


def test_file_sar_report_tool_returns_valid_json_with_a_real_case_id(repo):
    from mantis.banking.tools.sar_tools import file_sar_report
    result = json.loads(file_sar_report("EX-SEEDED01", "Unexplained repeated round-number mismatch"))
    assert result["status"] == "filed"
    assert result["sar_id"].startswith("SAR-")


def test_get_sar_status_tool_reflects_a_real_filed_sar(repo):
    from mantis.banking.tools.sar_tools import file_sar_report, get_sar_status
    filed = json.loads(file_sar_report("EX-SEEDED01", "Unexplained repeated round-number mismatch"))
    status = json.loads(get_sar_status(filed["sar_id"]))
    assert status["status"] == "filed"
    assert status["exception_id"] == "EX-SEEDED01"


def test_sar_escalation_agent_and_tools_appear_in_back_office_inventory():
    from mantis.runtime.adapter import NativeBankingAdapter
    inv = NativeBankingAdapter().inventory()
    assert "sar_escalation_agent" in inv.domains["back_office"]["agents"]
    for tool in ("get_exception_case", "file_sar_report", "get_sar_status"):
        assert tool in inv.domains["back_office"]["tools"]
        # Correctly excluded from the other two domains' scoped tool lists.
        assert tool not in inv.domains["front_office"]["tools"]
        assert tool not in inv.domains["mid_office"]["tools"]


def test_sar_tools_appear_in_the_raw_discovered_tool_inventory():
    """Regression test for a real gap found via live verification: these
    tools were reachable by the agent and listed in _DOMAIN_TOOL_NAMES, but
    sar_tools was never added to _TOOL_MODULE_PATHS, so _discover_banking_tools()
    never saw them at all -- invisible to mantis --inventory's raw tool list
    despite being fully wired everywhere else."""
    from mantis.runtime.adapter import _discover_banking_tools
    tools = _discover_banking_tools()
    assert "get_exception_case" in tools
    assert "file_sar_report" in tools
    assert "get_sar_status" in tools


def test_back_office_sar_escalation_workflow_is_registered():
    from mantis.core.registry import scenario_registry, workflow_registry
    assert "back_office_sar_escalation" in scenario_registry.all()
    assert workflow_registry.get("back_office_sar_escalation") == "back_office"


def test_file_sar_report_rejects_a_nonexistent_exception_case(repo):
    from mantis.banking.tools.sar_tools import file_sar_report
    result = json.loads(file_sar_report("EX-DOES-NOT-EXIST", "made-up case"))
    assert "error" in result and "sar_id" not in result
    assert repo._all("SELECT * FROM sar_reports") == [], "a SAR may only escalate an exception case that exists"
