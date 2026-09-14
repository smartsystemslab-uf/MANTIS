"""Post-Paper Extension: minimal UI (coding plan §11).

Read-only endpoints are checked against the real schema/registries/
inventory and a real checked-in run_artifacts directory. The mutating
endpoints (validate/run) are checked for the property that actually
matters -- they invoke the real `mantis` CLI as a subprocess rather than
reimplementing config validation in the UI layer -- using a deliberately
invalid config for --validate (fast, no LLM/backend needed) rather than
--run (which needs a live backend and is already covered end-to-end by
scripts/ci_attack_smoke_test.sh).
"""
from fastapi.testclient import TestClient

from mantis.ui.server import app, UI_CONFIG_DIR
from mantis.config.models import ExperimentConfig
from mantis.core.registry import domain_registry, plugin_registry
from mantis.runtime.adapter import NativeBankingAdapter

client = TestClient(app)

# A real, checked-in run_artifacts directory this repo ships (see
# run_artifacts/front_office_monitoring/) -- used to verify the trace/
# evaluation endpoints against genuine data, not a fixture built for this
# test.
REAL_RUN = "front_office_monitoring"


def test_index_serves_the_static_page():
    r = client.get("/")
    assert r.status_code == 200
    assert "MANTIS" in r.text


def test_schema_endpoint_matches_the_real_config_model():
    r = client.get("/api/schema")
    assert r.status_code == 200
    schema = r.json()
    assert schema == ExperimentConfig.model_json_schema(), "must be the exact schema, not a UI-maintained copy"


def test_registries_endpoint_matches_the_real_registries():
    r = client.get("/api/registries")
    data = r.json()
    assert set(data["domains"]) == set(domain_registry.all().keys())
    assert set(data["plugins"]) == set(plugin_registry.all().keys())
    assert "front_office_monitoring" in data["scenarios"]


def test_inventory_endpoint_matches_the_real_adapter():
    r = client.get("/api/inventory")
    data = r.json()
    real = NativeBankingAdapter().inventory()
    assert set(data["agents"]) == set(real.agents)
    assert set(data["tools"]) == set(real.tools)
    assert set(data["domains"].keys()) == {"front_office", "mid_office", "back_office"}


def test_list_runs_includes_a_real_checked_in_run():
    r = client.get("/api/runs")
    names = [run["name"] for run in r.json()]
    assert REAL_RUN in names


def test_get_trace_returns_real_events_from_a_real_run():
    r = client.get(f"/api/runs/{REAL_RUN}/trace")
    assert r.status_code == 200
    events = r.json()
    assert len(events) > 0
    event_types = {e["event_type"] for e in events}
    assert "WORKFLOW_START" in event_types


def test_get_trace_404s_for_an_unknown_run():
    r = client.get("/api/runs/this_run_does_not_exist/trace")
    assert r.status_code == 404


def test_validate_writes_a_real_config_file_and_invokes_the_real_cli():
    """The actual point of this extension: no separate business logic --
    an intentionally invalid domain must be rejected by the real
    mantis --validate subprocess (the same check every terminal user's
    config goes through), not by UI-side validation logic."""
    config = {
        "experiment": {
            "name": "ui_test_invalid_domain",
            "seed": 1,
            "domain": "not_a_real_domain",
            "workflow": "front_office_monitoring",
            "scenario": "front_office_monitoring",
        }
    }
    r = client.post("/api/validate", json={"config": config})
    assert r.status_code == 200
    data = r.json()
    assert data["returncode"] != 0
    assert "Unknown domain" in data["stdout"] + data["stderr"]
    # Confirms _write_config really wrote a file for the CLI to read, not
    # an in-memory-only shortcut.
    assert (UI_CONFIG_DIR / "ui_test_invalid_domain.yaml").exists()


def test_validate_accepts_a_real_valid_config():
    config = {
        "experiment": {
            "name": "ui_test_valid",
            "seed": 1,
            "domain": "front_office",
            "workflow": "front_office_monitoring",
            "scenario": "front_office_monitoring",
        }
    }
    r = client.post("/api/validate", json={"config": config})
    data = r.json()
    assert data["returncode"] == 0
    assert "valid" in data["stdout"].lower()


def test_write_config_rejects_a_config_that_fails_real_pydantic_validation():
    r = client.post("/api/validate", json={"config": {"experiment": {"name": "missing_required_fields"}}})
    assert r.status_code == 422
