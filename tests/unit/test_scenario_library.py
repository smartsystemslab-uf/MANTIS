"""Consistency tests over the scenario library, seed data, and tool metadata.

Offline (temp SQLite databases, no LLM, no backend). Each test encodes a
gap this repo actually had, not a hypothetical one:

* a scenario prompt that omits an identifier its tool needs makes the model
  silently decline to call the tool (found twice; a clean exit code looks
  identical to correct behavior);
* a scenario that references a customer/exception the seed data does not
  contain fails the same silent way;
* a tool with no entry in TOOL_SEMANTICS emits trace events with null
  risk/sensitivity fields (the WP4 gap), and one with no terminal outcome
  can never be asserted as an expected_terminal_state;
* a payload library whose "default" file differs from the plugin's built-in
  fallback would change Paper 1's already-reported prompt-injection evidence.
"""
import logging
import re
import tempfile
from pathlib import Path

import pytest

from mantis.banking.infra.repository import BankingRepository
from mantis.banking.scenarios import SCENARIOS
from mantis.banking.tool_semantics import TERMINAL_TOOL_OUTCOMES, TOOL_SEMANTICS
from mantis.banking.workflows import WORKFLOW_DOMAINS
from mantis.core.registry import domain_registry
from mantis.plugins.attacks.prompt_injection import PromptInjectionPlugin
from mantis.runtime.adapter import NativeBankingAdapter

REPO_ROOT = Path(__file__).resolve().parents[2]

ID_PATTERN = re.compile(r"\b(?:CUST|TXN|EOD|EX|SAR|LOAN|DSP)-[A-Z0-9-]+\b|\b\d{4}-\d{2}-\d{2}\b")
# The FAQ chatbot scenario is a general question, not a record lookup.
NO_IDENTIFIER_NEEDED = {"front_office_chatbot"}
# Identifiers a scenario names *on purpose* though nothing is seeded for them
# (a nonexistent record is the whole point of these robustness scenarios).
INTENTIONALLY_ABSENT = {
    "mid_office_loan_unknown_customer": {"CUST-777"},
    "back_office_sar_status_unknown": {"SAR-00000000"},
    "front_office_fraud_escalation": {"TXN-9999"},
}
CREDIT_UNION_SCENARIOS = {"mid_office_loan_preapproval_credit_union"}


@pytest.fixture(scope="module")
def default_repo():
    with tempfile.TemporaryDirectory() as tmp:
        r = BankingRepository(db_path=Path(tmp) / "default.db", institution="default")
        r.initialize()
        yield r


@pytest.fixture(scope="module")
def credit_union_repo():
    with tempfile.TemporaryDirectory() as tmp:
        r = BankingRepository(db_path=Path(tmp) / "cu.db", institution="regional_credit_union")
        r.initialize()
        yield r


def _backend_transaction_ids():
    text = (REPO_ROOT / "citi_banking_backend" / "app" / "seed.py").read_text()
    return set(re.findall(r'transaction_id="(TXN-[A-Z0-9-]+)"', text))


@pytest.mark.parametrize("scenario_id", sorted(SCENARIOS))
def test_scenario_prompt_names_a_concrete_identifier(scenario_id):
    if scenario_id in NO_IDENTIFIER_NEEDED:
        pytest.skip("general-question scenario")
    assert ID_PATTERN.search(SCENARIOS[scenario_id]), (
        f"{scenario_id} names no customer/transaction/batch/exception id or date; "
        "an under-specified prompt makes the model silently decline to call its target tool"
    )


@pytest.mark.parametrize("scenario_id", sorted(SCENARIOS))
def test_scenario_references_only_records_that_exist_in_the_seed_data(scenario_id, default_repo, credit_union_repo):
    repo = credit_union_repo if scenario_id in CREDIT_UNION_SCENARIOS else default_repo
    absent_ok = INTENTIONALLY_ABSENT.get(scenario_id, set())
    txns = _backend_transaction_ids()
    for ident in set(re.findall(r"\b(?:CUST|TXN|EOD|EX)-[A-Z0-9-]+\b", SCENARIOS[scenario_id])):
        if ident in absent_ok:
            continue
        if ident.startswith("CUST-"):
            assert repo.get_customer(ident), f"{scenario_id}: customer {ident} is not seeded"
        elif ident.startswith("EX-"):
            assert repo.get_exception(ident), f"{scenario_id}: exception {ident} is not seeded"
        elif ident.startswith("EOD-"):
            assert repo.get_eod_batch(ident), f"{scenario_id}: batch {ident} is not seeded"
        elif ident.startswith("TXN-"):
            assert ident in txns, f"{scenario_id}: transaction {ident} is not in the backend seed"


def test_intentionally_absent_records_really_are_absent(default_repo):
    """Guards the allowlist itself: if one of these ever gets seeded, the
    robustness scenario silently stops testing the not-found path."""
    assert default_repo.get_customer("CUST-777") is None
    assert default_repo.get_sar("SAR-00000000") is None
    assert "TXN-9999" not in _backend_transaction_ids()


def test_every_scenario_maps_to_a_registered_domain():
    assert set(WORKFLOW_DOMAINS) == set(SCENARIOS)
    assert set(WORKFLOW_DOMAINS.values()) <= set(domain_registry.all())


def test_scenario_library_covers_every_domain_with_multiple_scenarios():
    per_domain = {}
    for domain in WORKFLOW_DOMAINS.values():
        per_domain[domain] = per_domain.get(domain, 0) + 1
    assert set(per_domain) == {"front_office", "mid_office", "back_office"}
    assert all(n >= 5 for n in per_domain.values()), per_domain


def test_every_inventory_tool_has_trace_semantics():
    missing = set(NativeBankingAdapter().inventory().tools) - set(TOOL_SEMANTICS)
    assert not missing, f"{sorted(missing)} would emit trace events with null risk/sensitivity/side-effect fields"


def test_terminal_outcomes_belong_to_write_tools_with_semantics():
    for tool in TERMINAL_TOOL_OUTCOMES:
        assert TOOL_SEMANTICS[tool]["operation_type"] == "write", f"{tool} is a terminal outcome but not a write"


def test_new_workload_tools_are_terminal_states_a_config_can_assert():
    assert TERMINAL_TOOL_OUTCOMES["file_sar_report"] == "sar_filed"
    assert TERMINAL_TOOL_OUTCOMES["file_dispute"] == "dispute_filed"
    assert TERMINAL_TOOL_OUTCOMES["submit_loan_application"] == "loan_decision_recorded"


def test_suspicious_and_routine_reference_exceptions_are_distinguishable(default_repo):
    suspicious = default_repo.get_exception("EX-SEEDED01")["mismatch_summary"].lower()
    routine = default_repo.get_exception("EX-SEEDED02")["mismatch_summary"].lower()
    assert "unexplained" in suspicious and "no timing or rounding explanation" in suspicious
    assert "rounding" in routine and "ordinary rounding difference" in routine
    assert "unexplained items" in routine  # ...stated as absent ("No unexplained items")


def test_reference_exceptions_are_seeded_into_a_preexisting_database():
    """A machine whose banking.db predates a newly added reference case must
    still get it: _seed() only runs against an empty database."""
    with tempfile.TemporaryDirectory() as tmp:
        repo = BankingRepository(db_path=Path(tmp) / "old.db", institution="default")
        repo.initialize()
        with repo.connect() as conn:
            conn.execute("DELETE FROM exceptions")
        assert repo.get_exception("EX-SEEDED02") is None
        repo.initialize()
        assert repo.get_exception("EX-SEEDED01") and repo.get_exception("EX-SEEDED02")
        repo.initialize()  # idempotent: no duplicate-key failure
        assert len(repo._all("SELECT exception_id FROM exceptions")) == 2


def test_credit_union_institution_gets_no_default_reference_exceptions(credit_union_repo):
    assert credit_union_repo._all("SELECT * FROM exceptions") == []


def test_default_seed_is_deterministic_across_fresh_databases():
    snapshots = []
    for _ in range(2):
        with tempfile.TemporaryDirectory() as tmp:
            r = BankingRepository(db_path=Path(tmp) / "d.db", institution="default")
            r.initialize()
            snapshots.append((
                sorted((c["customer_id"], c["risk_tier"]) for c in r._all("SELECT * FROM customers")),
                sorted((a["account_id"], a["balance"]) for a in r._all("SELECT * FROM accounts")),
                sorted((b["batch_id"], b["expected_total"], b["ledger_posted_total"]) for b in r._all("SELECT * FROM eod_batches")),
                sorted(e["exception_id"] for e in r._all("SELECT * FROM exceptions")),
            ))
    assert snapshots[0] == snapshots[1]


@pytest.mark.parametrize("outcome_case", [
    ("mid_office_loan_referral", "CUST-002", 6000.0, "referred"),
    ("mid_office_loan_large_approved", "CUST-001", 30000.0, "approved"),
    ("mid_office_loan_preapproval", "CUST-002", 2000.0, "approved"),
])
def test_loan_scenarios_have_the_decision_their_ground_truth_assumes(outcome_case, default_repo):
    scenario_id, customer, amount, expected = outcome_case
    assert f"${amount:,.0f}" in SCENARIOS[scenario_id] and customer in SCENARIOS[scenario_id]
    assert default_repo.create_loan_application(customer, amount, "test")["decision"] == expected


# ---- prompt-injection payload library -------------------------------------

PAYLOADS = sorted((REPO_ROOT / "attacks").glob("prompt_*.txt"))


def test_payload_library_has_multiple_distinct_techniques():
    assert len(PAYLOADS) >= 6
    assert len({p.read_text().strip() for p in PAYLOADS}) == len(PAYLOADS)


def test_default_payload_file_matches_the_plugins_builtin_fallback():
    """Every shipped prompt-injection config pointed at attacks/prompt_01.txt,
    which did not exist, so the plugin's hardcoded fallback was what every
    reported run actually injected. The file must keep that exact text or
    Paper 1's reported evidence would no longer be reproducible."""
    fallback = PromptInjectionPlugin(target_agent="a", payload_file="definitely_missing.txt").injection_text
    assert (REPO_ROOT / "attacks" / "prompt_01.txt").read_text().strip() == fallback


@pytest.mark.parametrize("payload", PAYLOADS, ids=lambda p: p.name)
def test_each_payload_reaches_the_outgoing_model_request(payload):
    plugin = PromptInjectionPlugin(target_agent="agent_x", payload_file=str(payload))
    from mantis.hooks import HookAction, HookContext
    ctx = HookContext(
        run_id="t", trace_id="t", workflow_id="t", stage="interaction", source="agent_x", target="model",
        payload={"messages": [{"role": "user", "content": "Review transaction TXN-1001"}]},
        metadata={"specific_hook": "before_message"},
    )
    res = plugin.apply(ctx)
    assert res.action == HookAction.MUTATE
    sent = res.payload["messages"][-1]["content"]
    assert sent.startswith("Review transaction TXN-1001") and payload.read_text().strip() in sent


def test_a_missing_payload_file_is_no_longer_silent(caplog):
    with caplog.at_level(logging.WARNING):
        PromptInjectionPlugin(target_agent="a", payload_file="nope/missing_payload.txt")
    assert any("payload_file" in r.message and "not found" in r.message for r in caplog.records)
