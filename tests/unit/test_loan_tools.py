"""Post-Paper Extension: additional banking workloads (coding plan §11).

Covers the new mid-office loan-pre-approval capability -- a genuinely new
mid-office business process with a real, computed decision persisted to
the database, not a reworded prompt into the existing informational
loan_agent (see loan_preapproval_agent in
src/mantis/banking/mid_office/__init__.py). Mirrors test_dispute_tools.py
/ test_sar_tools.py's shape.
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
        monkeypatch.setattr("mantis.banking.tools.loan_tools.repo", r)
        yield r


def test_create_loan_application_approves_when_within_25_percent_of_balance(repo):
    # CUST-002 seeds a single checking account with balance 9620.13.
    created = repo.create_loan_application("CUST-002", 2000.0, "home improvement")
    assert created["decision"] == "approved"
    assert created["status"] == "approved"
    assert created["application_id"].startswith("LOAN-")

    fetched = repo.get_loan_application(created["application_id"])
    assert fetched["decision"] == "approved"
    assert fetched["customer_id"] == "CUST-002"


def test_create_loan_application_refers_when_amount_exceeds_25_percent_of_balance(repo):
    created = repo.create_loan_application("CUST-002", 9000.0, "debt consolidation")
    assert created["decision"] == "referred"
    assert created["status"] == "referred"
    assert "exceeds 25%" in created["decision_reason"]


def test_create_loan_application_refers_high_risk_customers_regardless_of_amount(repo):
    with repo.connect() as conn:
        conn.execute(
            "INSERT INTO customers VALUES (?, ?, ?, ?, ?, ?, ?)",
            ("CUST-HIGHRISK", "Test Customer", "high", "verified", "Unemployed", "US", "{}"),
        )
        conn.execute(
            "INSERT INTO accounts VALUES (?, ?, ?, ?, ?, ?)",
            ("CHK-HIGHRISK", "CUST-HIGHRISK", "checking", "USD", 1000000.0, "active"),
        )
    created = repo.create_loan_application("CUST-HIGHRISK", 10.0, "small personal loan")
    assert created["decision"] == "referred"
    assert "risk tier is high" in created["decision_reason"]


def test_create_loan_application_raises_for_unknown_customer(repo):
    with pytest.raises(ValueError):
        repo.create_loan_application("CUST-DOESNOTEXIST", 100.0, "test")


def test_get_loan_application_returns_none_for_unknown_id(repo):
    assert repo.get_loan_application("LOAN-DOESNOTEXIST") is None


def test_submit_loan_application_tool_returns_valid_json_with_a_real_application_id(repo):
    from mantis.banking.tools.loan_tools import submit_loan_application
    result = json.loads(submit_loan_application("CUST-002", 2000.0, "home improvement"))
    assert result["decision"] == "approved"
    assert result["application_id"].startswith("LOAN-")


def test_submit_loan_application_tool_reports_error_for_unknown_customer(repo):
    from mantis.banking.tools.loan_tools import submit_loan_application
    result = json.loads(submit_loan_application("CUST-DOESNOTEXIST", 100.0, "test"))
    assert "error" in result


def test_get_loan_application_status_tool_reflects_a_real_submitted_application(repo):
    from mantis.banking.tools.loan_tools import submit_loan_application, get_loan_application_status
    submitted = json.loads(submit_loan_application("CUST-002", 2000.0, "home improvement"))
    status = json.loads(get_loan_application_status(submitted["application_id"]))
    assert status["decision"] == "approved"
    assert status["customer_id"] == "CUST-002"


def test_get_loan_application_status_tool_reports_not_found_for_unknown_id(repo):
    from mantis.banking.tools.loan_tools import get_loan_application_status
    result = json.loads(get_loan_application_status("LOAN-DOESNOTEXIST"))
    assert "error" in result


def test_loan_preapproval_agent_and_tools_appear_in_mid_office_inventory():
    from mantis.runtime.adapter import NativeBankingAdapter
    inv = NativeBankingAdapter().inventory()
    assert "loan_preapproval_agent" in inv.domains["mid_office"]["agents"]
    for tool in ("submit_loan_application", "get_loan_application_status"):
        assert tool in inv.domains["mid_office"]["tools"]
        assert tool not in inv.domains["front_office"]["tools"]
        assert tool not in inv.domains["back_office"]["tools"]


def test_loan_tools_appear_in_the_raw_discovered_tool_inventory():
    from mantis.runtime.adapter import _discover_banking_tools
    tools = _discover_banking_tools()
    assert "submit_loan_application" in tools
    assert "get_loan_application_status" in tools


def test_mid_office_loan_preapproval_workflow_is_registered():
    from mantis.core.registry import scenario_registry, workflow_registry
    assert "mid_office_loan_preapproval" in scenario_registry.all()
    assert workflow_registry.get("mid_office_loan_preapproval") == "mid_office"
