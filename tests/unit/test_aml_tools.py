"""Anti-Money Laundering office (Post-Paper Extension, ported from Citi_P3's
citi_banking_adk/bank_adk/tools/aml_tools.py and
citi_banking_backend/app/aml_alert_repository.py -- see
mantis.banking.aml_office). Mirrors test_sar_tools.py's shape: repository
layer against a real temp SQLite db, then the tool wrappers on top of it.
"""
import json
import sys
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from mantis.banking.infra.repository import BankingRepository


@pytest.fixture
def repo(monkeypatch):
    with tempfile.TemporaryDirectory() as tmpdir:
        r = BankingRepository(db_path=Path(tmpdir) / "test_banking.db")
        r.initialize()
        monkeypatch.setattr("mantis.banking.tools.aml_tools.repo", r)
        # detect_structuring's auto_trigger_review path locally imports
        # submit_manual_review from customer_tools, which binds its own
        # module-level `repo` -- must point at the same temp db or
        # create_manual_review hits the real (uninitialized) singleton.
        monkeypatch.setattr("mantis.banking.tools.customer_tools.repo", r)
        yield r


def _insert_transactions(repo, customer_id, rows):
    """rows: list of (transaction_id, source_account, destination_account,
    amount, txn_type, created_at) -- the rest of the columns the real schema
    needs are filled with neutral defaults."""
    with repo.connect() as conn:
        for transaction_id, source_account, destination_account, amount, txn_type, created_at in rows:
            conn.execute(
                "INSERT INTO transactions VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (transaction_id, customer_id, source_account, destination_account, amount,
                 "USD", "wire", txn_type, "Test Counterparty", "posted", "{}", created_at),
            )


# ---------------------------------------------------------------------------
# Repository layer: aml_alerts + status lifecycle
# ---------------------------------------------------------------------------

def test_create_and_get_aml_alert_round_trips_through_real_sqlite(repo):
    created = repo.create_aml_alert(
        customer_id="CUST-001", alert_type="structuring", detection_window_params="7d",
        cumulative_total=12000.0, threshold=10000.0, raw_payload="[]",
    )
    assert created["status"] == "open"
    assert created["alert_id"].startswith("ALT-")

    fetched = repo.get_aml_alert(created["alert_id"])
    assert fetched["customer_id"] == "CUST-001"
    assert fetched["alert_type"] == "structuring"
    assert fetched["cumulative_total"] == 12000.0


def test_get_aml_alert_returns_none_for_unknown_id(repo):
    assert repo.get_aml_alert("ALT-DOESNOTEXIST") is None


def test_list_aml_alerts_filters_by_customer_status_and_type(repo):
    """Uses CUST-951/CUST-952, not CUST-001: initialize() also seeds a
    stable reference alert (ALT-SEEDED01) for CUST-001 (see
    BankingRepository._ensure_reference_aml_alerts), which would otherwise
    collide with these count assertions."""
    repo.create_aml_alert(customer_id="CUST-951", alert_type="structuring", detection_window_params="7d", cumulative_total=12000.0, threshold=10000.0, raw_payload="[]")
    repo.create_aml_alert(customer_id="CUST-952", alert_type="structuring", detection_window_params="7d", cumulative_total=15000.0, threshold=10000.0, raw_payload="[]")

    assert len(repo.list_aml_alerts(alert_type="structuring")) == 3  # includes ALT-SEEDED01
    assert len(repo.list_aml_alerts(customer_id="CUST-951")) == 1
    assert len(repo.list_aml_alerts(customer_id="CUST-952")) == 1
    assert len(repo.list_aml_alerts(status="cleared")) == 0


def test_transition_allows_open_to_in_investigation(repo):
    created = repo.create_aml_alert(customer_id="CUST-001", alert_type="structuring", detection_window_params="7d", cumulative_total=12000.0, threshold=10000.0, raw_payload="[]")
    updated = repo.transition_aml_alert_status(created["alert_id"], "in-investigation")
    assert updated["status"] == "in-investigation"

    history = repo._all("SELECT * FROM aml_alert_status_history WHERE alert_id = ?", created["alert_id"])
    assert len(history) == 1
    assert history[0]["previous_status"] == "open"
    assert history[0]["new_status"] == "in-investigation"


@pytest.mark.parametrize("next_status", ["cleared", "escalated-to-sar"])
def test_transition_allows_in_investigation_to_terminal_states(repo, next_status):
    created = repo.create_aml_alert(customer_id="CUST-001", alert_type="structuring", detection_window_params="7d", cumulative_total=12000.0, threshold=10000.0, raw_payload="[]")
    repo.transition_aml_alert_status(created["alert_id"], "in-investigation")
    updated = repo.transition_aml_alert_status(created["alert_id"], next_status)
    assert updated["status"] == next_status


def test_transition_rejects_skipping_straight_to_escalated(repo):
    """open -> escalated-to-sar is not allowed; must pass through in-investigation."""
    created = repo.create_aml_alert(customer_id="CUST-001", alert_type="structuring", detection_window_params="7d", cumulative_total=12000.0, threshold=10000.0, raw_payload="[]")
    with pytest.raises(ValueError, match="Invalid AML alert status transition"):
        repo.transition_aml_alert_status(created["alert_id"], "escalated-to-sar")


def test_transition_rejects_leaving_a_terminal_state(repo):
    created = repo.create_aml_alert(customer_id="CUST-001", alert_type="structuring", detection_window_params="7d", cumulative_total=12000.0, threshold=10000.0, raw_payload="[]")
    repo.transition_aml_alert_status(created["alert_id"], "in-investigation")
    repo.transition_aml_alert_status(created["alert_id"], "cleared")
    with pytest.raises(ValueError, match="Invalid AML alert status transition"):
        repo.transition_aml_alert_status(created["alert_id"], "in-investigation")


def test_transition_rejects_unknown_alert_id(repo):
    with pytest.raises(ValueError, match="not found"):
        repo.transition_aml_alert_status("ALT-DOESNOTEXIST", "in-investigation")


# ---------------------------------------------------------------------------
# Tool wrappers: JSON-string shape, matching this codebase's other tools/*.py
# ---------------------------------------------------------------------------

def test_get_aml_alert_tool_reflects_a_real_alert(repo):
    from mantis.banking.tools.aml_tools import get_aml_alert
    created = repo.create_aml_alert(customer_id="CUST-001", alert_type="structuring", detection_window_params="7d", cumulative_total=12000.0, threshold=10000.0, raw_payload="[]")
    result = json.loads(get_aml_alert(created["alert_id"]))
    assert result["alert_id"] == created["alert_id"]
    assert result["status"] == "open"


def test_get_aml_alert_tool_reports_not_found(repo):
    from mantis.banking.tools.aml_tools import get_aml_alert
    result = json.loads(get_aml_alert("ALT-DOESNOTEXIST"))
    assert "error" in result


def test_list_aml_alerts_tool_round_trips(repo):
    """Uses CUST-950, not CUST-001: initialize() also seeds a stable
    reference alert (ALT-SEEDED01) for CUST-001 (see
    BankingRepository._ensure_reference_aml_alerts), which would otherwise
    collide with this count assertion."""
    from mantis.banking.tools.aml_tools import list_aml_alerts
    repo.create_aml_alert(customer_id="CUST-950", alert_type="structuring", detection_window_params="7d", cumulative_total=12000.0, threshold=10000.0, raw_payload="[]")
    result = json.loads(list_aml_alerts(customer_id="CUST-950"))
    assert len(result) == 1
    assert result[0]["customer_id"] == "CUST-950"


def test_transition_aml_alert_status_tool_reports_invalid_transition_as_json_error(repo):
    from mantis.banking.tools.aml_tools import transition_aml_alert_status
    created = repo.create_aml_alert(customer_id="CUST-001", alert_type="structuring", detection_window_params="7d", cumulative_total=12000.0, threshold=10000.0, raw_payload="[]")
    result = json.loads(transition_aml_alert_status(created["alert_id"], "escalated-to-sar"))
    assert "error" in result
    # The repo-level state must not have moved despite the rejected call.
    assert repo.get_aml_alert(created["alert_id"])["status"] == "open"


def test_transition_aml_alert_status_tool_reports_unknown_alert_as_json_error(repo):
    from mantis.banking.tools.aml_tools import transition_aml_alert_status
    result = json.loads(transition_aml_alert_status("ALT-DOESNOTEXIST", "in-investigation"))
    assert "error" in result


# ---------------------------------------------------------------------------
# detect_structuring: the sliding-window structuring detector
# ---------------------------------------------------------------------------

def test_detect_structuring_true_positive_on_synthetic_window(repo):
    from mantis.banking.tools.aml_tools import detect_structuring
    now = datetime.now(timezone.utc)
    _insert_transactions(repo, "CUST-900", [
        ("TXN-S1", "EXT-1", "CHK-900", 4000.0, "wire_in", (now - timedelta(days=5)).isoformat()),
        ("TXN-S2", "EXT-1", "CHK-900", 4000.0, "wire_in", (now - timedelta(days=3)).isoformat()),
        ("TXN-S3", "EXT-1", "CHK-900", 4000.0, "wire_in", (now - timedelta(days=1)).isoformat()),
    ])
    result = json.loads(detect_structuring("CUST-900"))
    assert result["structuring_detected"] is True
    assert result["peak_cumulative_total"] == 12000.0
    assert result["alert_id"].startswith("ALT-")
    assert result["manual_review_case_id"] is not None

    # A real alert and manual review were actually created, not just reported.
    alert = repo.get_aml_alert(result["alert_id"])
    assert alert["alert_type"] == "structuring"
    assert alert["status"] == "open"


def test_detect_structuring_true_negative_below_threshold(repo):
    from mantis.banking.tools.aml_tools import detect_structuring
    now = datetime.now(timezone.utc)
    _insert_transactions(repo, "CUST-901", [
        ("TXN-S4", "EXT-1", "CHK-901", 500.0, "wire_in", now.isoformat()),
    ])
    result = json.loads(detect_structuring("CUST-901"))
    assert result["structuring_detected"] is False
    assert repo.list_aml_alerts(customer_id="CUST-901") == []


def test_detect_structuring_ignores_deposits_outside_the_window(repo):
    """Two deposits that individually clear the threshold only when summed,
    but are more than window_days apart, must not be combined."""
    from mantis.banking.tools.aml_tools import detect_structuring
    now = datetime.now(timezone.utc)
    _insert_transactions(repo, "CUST-902", [
        ("TXN-S5", "EXT-1", "CHK-902", 6000.0, "wire_in", (now - timedelta(days=20)).isoformat()),
        ("TXN-S6", "EXT-1", "CHK-902", 6000.0, "wire_in", now.isoformat()),
    ])
    result = json.loads(detect_structuring("CUST-902", window_days=7))
    assert result["structuring_detected"] is False


def test_detect_structuring_ignores_outbound_transactions(repo):
    """An outbound transfer from the customer's own account is not a deposit,
    even if it's large and frequent -- only inbound deposit-like flow counts."""
    from mantis.banking.tools.aml_tools import detect_structuring
    now = datetime.now(timezone.utc)
    _insert_transactions(repo, "CUST-903", [
        ("TXN-S7", "CHK-903", "EXT-1", 5000.0, "transfer", (now - timedelta(days=2)).isoformat()),
        ("TXN-S8", "CHK-903", "EXT-1", 6000.0, "transfer", now.isoformat()),
    ])
    result = json.loads(detect_structuring("CUST-903"))
    assert result["structuring_detected"] is False


def test_detect_structuring_without_auto_trigger_review_skips_manual_review(repo):
    from mantis.banking.tools.aml_tools import detect_structuring
    now = datetime.now(timezone.utc)
    _insert_transactions(repo, "CUST-904", [
        ("TXN-S9", "EXT-1", "CHK-904", 12000.0, "wire_in", now.isoformat()),
    ])
    result = json.loads(detect_structuring("CUST-904", auto_trigger_review=False))
    assert result["structuring_detected"] is True
    assert result["manual_review_case_id"] is None


def test_detect_structuring_with_no_transactions_is_a_clean_negative(repo):
    from mantis.banking.tools.aml_tools import detect_structuring
    result = json.loads(detect_structuring("CUST-NOBODY"))
    assert result["structuring_detected"] is False


def test_seeded_cust_001_trips_structuring_and_cust_002_does_not():
    """Against the real default seed (mantis.banking.infra.repository's
    BankingRepository._seed): CUST-001 has three inbound wires from the
    same counterparty within 7 days summing to $12,000; CUST-002 has only
    a single routine bill payment. Exercises the shipped demo path, not
    just a synthetic fixture."""
    with tempfile.TemporaryDirectory() as tmpdir:
        r = BankingRepository(db_path=Path(tmpdir) / "seeded.db")
        r.initialize()
        import mantis.banking.tools.aml_tools as aml_tools
        import mantis.banking.tools.customer_tools as customer_tools
        orig_aml_repo, orig_customer_repo = aml_tools.repo, customer_tools.repo
        aml_tools.repo = r
        customer_tools.repo = r
        try:
            positive = json.loads(aml_tools.detect_structuring("CUST-001"))
            negative = json.loads(aml_tools.detect_structuring("CUST-002"))
        finally:
            aml_tools.repo = orig_aml_repo
            customer_tools.repo = orig_customer_repo

    assert positive["structuring_detected"] is True
    assert positive["peak_cumulative_total"] == 12000.0
    assert negative["structuring_detected"] is False


# ---------------------------------------------------------------------------
# check_threshold_anomaly
# ---------------------------------------------------------------------------

def test_check_threshold_anomaly_flags_amount_over_5x_peak():
    from mantis.banking.tools.aml_tools import check_threshold_anomaly
    result = check_threshold_anomaly("CHK-001", "TXN-1001", 5001.0)
    assert result["flagged"] is True
    assert result["status"] == "review"


def test_check_threshold_anomaly_does_not_flag_amount_within_5x_peak():
    from mantis.banking.tools.aml_tools import check_threshold_anomaly
    result = check_threshold_anomaly("CHK-001", "TXN-1001", 5000.0)
    assert result["flagged"] is False


# ---------------------------------------------------------------------------
# find_mule_rings_for_customer -- requires the optional 'aml' dependency
# ---------------------------------------------------------------------------

def test_find_mule_rings_requires_networkx_or_gives_an_actionable_error(monkeypatch):
    """Forces the lazy `import networkx` inside the function to fail
    regardless of whether it's actually installed in this environment, so
    this test is meaningful either way."""
    from mantis.banking.tools.aml_tools import find_mule_rings_for_customer
    monkeypatch.setitem(sys.modules, "networkx", None)
    with pytest.raises(ImportError, match=r'pip install -e ".\[aml\]"'):
        find_mule_rings_for_customer("CUST-001")


def test_find_mule_rings_detects_a_synthetic_closed_loop(repo):
    pytest.importorskip("networkx")
    from mantis.banking.tools.aml_tools import find_mule_rings_for_customer
    now = datetime.now(timezone.utc)
    _insert_transactions(repo, "CUST-905", [
        ("TXN-R1", "Account_A", "Account_B", 1000.0, "transfer", now.isoformat()),
        ("TXN-R2", "Account_B", "Account_C", 1000.0, "transfer", now.isoformat()),
        ("TXN-R3", "Account_C", "Account_A", 1000.0, "transfer", now.isoformat()),
    ])
    rings = find_mule_rings_for_customer("CUST-905")
    assert len(rings) == 1
    assert set(rings[0]) == {"Account_A", "Account_B", "Account_C"}


def test_find_mule_rings_reports_no_rings_for_acyclic_flow(repo):
    pytest.importorskip("networkx")
    from mantis.banking.tools.aml_tools import find_mule_rings_for_customer
    now = datetime.now(timezone.utc)
    _insert_transactions(repo, "CUST-906", [
        ("TXN-R4", "Account_X", "Account_Y", 1000.0, "transfer", now.isoformat()),
        ("TXN-R5", "Account_Y", "Account_Z", 1000.0, "transfer", now.isoformat()),
    ])
    assert find_mule_rings_for_customer("CUST-906") == []


def test_find_mule_rings_respects_max_depth(repo):
    pytest.importorskip("networkx")
    from mantis.banking.tools.aml_tools import find_mule_rings_for_customer
    now = datetime.now(timezone.utc)
    _insert_transactions(repo, "CUST-907", [
        ("TXN-R6", "Account_A", "Account_B", 1000.0, "transfer", now.isoformat()),
        ("TXN-R7", "Account_B", "Account_C", 1000.0, "transfer", now.isoformat()),
        ("TXN-R8", "Account_C", "Account_A", 1000.0, "transfer", now.isoformat()),
    ])
    assert find_mule_rings_for_customer("CUST-907", max_depth=2) == []


# ---------------------------------------------------------------------------
# verify_identity_document (ported test cases, from Citi_P3's
# citi_banking_adk_mlflow_observability/tests/test_aml_tools.py)
# ---------------------------------------------------------------------------

def _score(**overrides):
    from mantis.banking.tools.aml_tools import verify_identity_document
    fields = {
        "submitted_name": "Ava Patel",
        "submitted_dob": "2000-02-29",
        "submitted_id_number": "FL-001234",
        "reference_name": "Ava Patel",
        "reference_dob": "2000-02-29",
        "reference_id_number": "FL-001234",
    }
    fields.update(overrides)
    return verify_identity_document(**fields)


def test_verify_identity_exact_match_returns_full_score():
    result = _score()
    assert result == {
        "status": "success",
        "match_confidence": 1.0,
        "field_scores": {"name": 1.0, "dob": 1.0, "id_number": 1.0},
    }
    assert json.loads(json.dumps(result)) == result


def test_verify_identity_all_fields_mismatch_returns_zero():
    result = _score(submitted_name="X", submitted_dob="1999-01-01", submitted_id_number="ZZ9")
    assert result["match_confidence"] == 0.0


@pytest.mark.parametrize("argument,value,field,expected", [
    ("submitted_name", "X", "name", 0.7),
    ("submitted_dob", "1999-01-01", "dob", 0.7),
    ("submitted_id_number", "ZZ9", "id_number", 0.6),
])
def test_verify_identity_individual_mismatch_removes_only_that_fields_weight(argument, value, field, expected):
    result = _score(**{argument: value})
    assert result["match_confidence"] == expected
    assert result["field_scores"][field] == 0.0


def test_verify_identity_name_typo_earns_partial_credit():
    result = _score(submitted_name="Eva Patel")
    assert result["field_scores"]["name"] == 0.8889
    assert result["match_confidence"] == 0.9667


def test_verify_identity_name_normalizes_case_whitespace_and_unicode():
    for submitted, reference in [
        ("  AVA\t  PATEL\n", "Ava Patel"),
        ("JOSÉ   ÁLVAREZ", "José Álvarez"),
    ]:
        assert _score(submitted_name=submitted, reference_name=reference)["match_confidence"] == 1.0


def test_verify_identity_invalid_dob_never_matches_even_itself():
    for invalid in ["", "not-a-date", "2001-02-29", "2000-13-01", None]:
        result = _score(submitted_dob=invalid)
        assert result["field_scores"]["dob"] == 0.0
        assert result["match_confidence"] == 0.7


def test_verify_identity_id_preserves_case_and_internal_characters():
    assert _score(submitted_id_number=" FL-001234\t")["match_confidence"] == 1.0
    for mismatch in ["fl-001234", "FL001234", "FL-1234"]:
        assert _score(submitted_id_number=mismatch)["field_scores"]["id_number"] == 0.0


def test_verify_identity_names_need_letters_and_ids_need_alphanumeric():
    for invalid in ["---", "...", "123"]:
        assert _score(submitted_name=invalid, reference_name=invalid)["field_scores"]["name"] == 0.0


def test_verify_identity_score_is_bounded_and_consistent_with_breakdown():
    for name in ["", "Ava Patel", "Eva Patel", "X"]:
        for dob in ["", "2000-02-29", "1999-01-01"]:
            for id_number in ["", "FL-001234", "ZZ9"]:
                result = _score(submitted_name=name, submitted_dob=dob, submitted_id_number=id_number)
                fields = result["field_scores"]
                assert result["match_confidence"] == round(
                    0.3 * fields["name"] + 0.3 * fields["dob"] + 0.4 * fields["id_number"], 4
                )
                for value in [result["match_confidence"], *fields.values()]:
                    assert 0.0 <= value <= 1.0


# ---------------------------------------------------------------------------
# Inventory / registry wiring
# ---------------------------------------------------------------------------

def test_aml_office_agents_and_tools_appear_in_inventory():
    from mantis.runtime.adapter import NativeBankingAdapter
    inv = NativeBankingAdapter().inventory()
    assert "aml_investigator" in inv.domains["aml_office"]["agents"]
    assert "sar_drafting_agent" in inv.domains["aml_office"]["agents"]
    for tool in ("detect_structuring", "check_threshold_anomaly", "find_mule_rings_for_customer", "verify_identity_document"):
        assert tool in inv.domains["aml_office"]["tools"]
        assert tool not in inv.domains["front_office"]["tools"]
        assert tool not in inv.domains["mid_office"]["tools"]
        assert tool not in inv.domains["back_office"]["tools"]


def test_aml_tools_appear_in_the_raw_discovered_tool_inventory():
    from mantis.runtime.adapter import _discover_banking_tools
    tools = _discover_banking_tools()
    for tool in ("detect_structuring", "check_threshold_anomaly", "find_mule_rings_for_customer", "verify_identity_document", "get_aml_alert", "list_aml_alerts", "transition_aml_alert_status"):
        assert tool in tools


def test_aml_office_scenarios_are_registered():
    from mantis.core.registry import scenario_registry, workflow_registry
    assert "aml_office_structuring_investigation" in scenario_registry.all()
    assert workflow_registry.get("aml_office_structuring_investigation") == "aml_office"
    assert "aml_office_routine_customer_clear" in scenario_registry.all()
