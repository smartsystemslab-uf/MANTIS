"""Post-Paper Extension: additional banking workloads and deployment
variants (coding plan §11) -- specifically the "institutions" half of
that bullet, distinct from the "more banking processes" half already
covered by test_sar_tools.py/test_loan_tools.py.

A second, smaller institution profile (regional_credit_union) reuses the
identical loan_preapproval_agent, submit_loan_application tool, and
BankingRepository.create_loan_application code path as the default
institution -- only the seeded data and the institution-specific
threshold in _LOAN_APPROVAL_THRESHOLD_PCT differ.
"""
import tempfile
from pathlib import Path

import pytest

from mantis.banking.infra.repository import BankingRepository
from mantis.config.models import ExperimentConfig


@pytest.fixture
def default_repo():
    with tempfile.TemporaryDirectory() as tmpdir:
        r = BankingRepository(db_path=Path(tmpdir) / "default.db", institution="default")
        r.initialize()
        yield r


@pytest.fixture
def credit_union_repo():
    with tempfile.TemporaryDirectory() as tmpdir:
        r = BankingRepository(db_path=Path(tmpdir) / "credit_union.db", institution="regional_credit_union")
        r.initialize()
        yield r


def test_institution_field_is_optional_and_accepted_by_the_config_schema():
    cfg = ExperimentConfig(experiment={
        "name": "t", "domain": "mid_office", "workflow": "mid_office_loan_preapproval",
        "scenario": "mid_office_loan_preapproval", "institution": "regional_credit_union",
    })
    assert cfg.experiment.institution == "regional_credit_union"

    cfg_default = ExperimentConfig(experiment={
        "name": "t", "domain": "mid_office", "workflow": "mid_office_loan_preapproval",
        "scenario": "mid_office_loan_preapproval",
    })
    assert cfg_default.experiment.institution is None


def test_credit_union_repo_seeds_its_own_distinct_member_not_the_default_customers(credit_union_repo):
    assert credit_union_repo.get_customer("CUST-101")["full_name"] == "Maria Alvarez"
    assert credit_union_repo.get_customer("CUST-001") is None
    assert credit_union_repo.get_customer("CUST-002") is None


def test_default_repo_does_not_seed_the_credit_unions_member(default_repo):
    assert default_repo.get_customer("CUST-101") is None
    assert default_repo.get_customer("CUST-001") is not None


def test_same_request_gets_a_different_real_decision_under_each_institutions_threshold(default_repo, credit_union_repo):
    """The actual point of this extension: identical code path
    (create_loan_application), genuinely different real outcome, because
    the institution's own threshold differs -- not because the logic
    differs. $500 against CUST-101's $3,000 balance is 16.7%: referred at
    the credit union's 10% threshold, but would be approved at the default
    institution's 25%."""
    referred = credit_union_repo.create_loan_application("CUST-101", 500.0, "home appliance repair")
    assert referred["decision"] == "referred"
    assert "10%" in referred["decision_reason"]

    # Same 16.7%-of-balance ratio, but against a default-institution
    # customer, to isolate that the *threshold* -- not the customer or the
    # amount -- is what changed the outcome.
    approved = default_repo.create_loan_application("CUST-002", 1600.0, "home appliance repair")  # ~16.6% of $9,620.13
    assert approved["decision"] == "approved"
    assert "25%" in approved["decision_reason"]


def test_sqlite_path_is_isolated_per_institution(monkeypatch):
    from mantis.banking.settings import Settings
    default_settings = Settings(institution="default")
    cu_settings = Settings(institution="regional_credit_union")
    assert default_settings.sqlite_path.name == "banking.db"
    assert cu_settings.sqlite_path.name == "banking_regional_credit_union.db"
    assert default_settings.sqlite_path != cu_settings.sqlite_path
