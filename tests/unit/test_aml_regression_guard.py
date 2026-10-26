"""Regression guards for the AML office integration (Post-Paper Extension,
ported from Citi_P3 -- see mantis.banking.aml_office).

Mirrors test_zero_trust_regression_guard.py's structure and purpose: not the
same job as test_aml_tools.py (which checks the ported detection logic
itself), this file exists so a future, unrelated change elsewhere in MANTIS
fails loudly here instead of silently breaking the aml_office: toggle or
the registry/inventory wiring it depends on. Three risk categories:

1. MANTIS-side drift: domain_registry/DOMAIN_AGENTS, _DOMAIN_TOOL_NAMES, and
   the agents build_aml_office_router() actually builds stay consistent --
   so adding/renaming an AML agent or tool in only one of those three
   places is caught, not silently inconsistent.
2. Toggle wiring drift: AMLConfig's defaults, build_root_agent's two code
   paths, and the adapter's derivation of enable_aml from
   ExperimentConfig.aml_office keep producing exactly "no change at all"
   when disabled/absent, and exactly "front+mid+back+aml" when enabled.
3. Ported-logic drift: the external networkx API this integration calls by
   name (DiGraph, simple_cycles) hasn't silently changed shape underneath
   us, the same class of check test_zero_trust_regression_guard.py applies
   to the real Zero Trust Backplane project's API.
"""
import pytest

from mantis.config.models import AMLConfig, ExperimentConfig


# ---------------------------------------------------------------------------
# 1. MANTIS-side drift: registry/inventory consistency
# ---------------------------------------------------------------------------

def test_domain_agents_matches_what_build_aml_office_router_actually_builds():
    """Catches: DOMAIN_AGENTS["aml_office"] listing an agent name that
    doesn't exist in the real built tree, or vice versa -- the same failure
    mode that would make mantis --inventory lie about what a run actually
    does."""
    from mantis.banking.domains import DOMAIN_AGENTS
    from mantis.banking.aml_office import build_aml_office_router

    def _collect_names(agent):
        names = {agent.name}
        for sub in getattr(agent, "sub_agents", None) or []:
            names |= _collect_names(sub)
        return names

    built = _collect_names(build_aml_office_router())
    assert built == set(DOMAIN_AGENTS["aml_office"])


def test_domain_tool_names_matches_the_tools_aml_investigator_actually_has():
    """Catches: _DOMAIN_TOOL_NAMES["aml_office"] drifting from the tools
    actually wired onto aml_investigator -- the list a default-deny-by-domain
    policy (if one is ever added for this domain) would scope against."""
    from mantis.runtime.adapter import _DOMAIN_TOOL_NAMES
    from mantis.banking.aml_office import build_aml_office_router

    router = build_aml_office_router()
    investigator = router.sub_agents[0].investigator_agent
    real_tool_names = {t.__name__ for t in investigator.tools}

    assert set(_DOMAIN_TOOL_NAMES["aml_office"]) == real_tool_names


def test_aml_tools_module_is_in_the_tool_discovery_path():
    """Catches: aml_tools being added to _DOMAIN_TOOL_NAMES without also
    being added to _TOOL_MODULE_PATHS -- the exact gap test_sar_tools.py's
    own regression test for sar_tools once caught (invisible to
    mantis --inventory's raw tool list despite being fully wired
    everywhere else)."""
    from mantis.runtime.adapter import _TOOL_MODULE_PATHS
    assert "mantis.banking.tools.aml_tools" in _TOOL_MODULE_PATHS


# ---------------------------------------------------------------------------
# 2. Toggle wiring drift
# ---------------------------------------------------------------------------

def test_aml_config_default_is_unchanged():
    """Catches: someone changing AMLConfig's default, silently changing
    what a bare `aml_office: {}` means."""
    assert AMLConfig().enabled is True


def test_experiment_config_without_aml_office_block_defaults_to_none():
    """Catches: aml_office ever defaulting to something other than None on
    ExperimentConfig -- every config written before this domain existed
    must still resolve to "no AML" with zero code changes."""
    cfg = ExperimentConfig(**{
        "experiment": {"name": "x", "domain": "front_office", "workflow": "w", "scenario": "s"},
    })
    assert cfg.aml_office is None


def test_build_root_agent_disabled_is_identical_to_before_aml_existed():
    """The actual behavioral contract: disabled (the default for every
    existing config) must produce exactly front+mid+back, nothing more."""
    from mantis.banking.agents.root import build_root_agent
    agent = build_root_agent(enable_aml=False)
    assert [sa.name for sa in agent.sub_agents] == ["front_office_router", "mid_office_router", "back_office_router"]
    assert "aml_office_router" not in agent.instruction
    assert "AML office" not in agent.description


def test_build_root_agent_enabled_adds_exactly_one_more_router():
    from mantis.banking.agents.root import build_root_agent
    agent = build_root_agent(enable_aml=True)
    assert [sa.name for sa in agent.sub_agents] == ["front_office_router", "mid_office_router", "back_office_router", "aml_office_router"]
    assert "aml_office_router" in agent.instruction


def test_legacy_banking_handle_derives_enable_aml_from_config(monkeypatch):
    """Catches: a future refactor of adapter.py's run_message breaking the
    derivation of enable_aml from ExperimentConfig.aml_office -- mirrors
    test_zero_trust_regression_guard.py's
    test_dedicated_toggle_and_the_generic_policies_form_are_equivalent in
    spirit (lock in the exact resolution logic, not just its outcome)."""
    import asyncio
    from mantis.runtime.adapter import LegacyBankingHandle
    from mantis.hooks import HookBus

    captured = {}

    async def fake_run_message(message, mcp_session=None, mcp_tools=None, compact=True, mantis_plugin=None, enable_aml=False):
        captured["enable_aml"] = enable_aml
        return "ok"

    monkeypatch.setattr("mantis.banking.runner.run_message", fake_run_message)

    for aml_block, expected in [
        (None, False),
        ({"enabled": False}, False),
        ({"enabled": True}, True),
    ]:
        cfg = ExperimentConfig(**{
            "experiment": {"name": "x", "domain": "front_office", "workflow": "w", "scenario": "s"},
            **({"aml_office": aml_block} if aml_block is not None else {}),
        })
        handle = LegacyBankingHandle(hooks=HookBus(), config=cfg)
        asyncio.run(handle.run_message("hello"))
        assert captured["enable_aml"] is expected, f"aml_office={aml_block!r} should resolve to enable_aml={expected}"


def test_domain_aml_office_without_toggle_fails_validation(tmp_path):
    from mantis.cli.main import validate_config
    cfg = tmp_path / "aml_no_toggle.yaml"
    cfg.write_text(
        "experiment:\n  name: aml_no_toggle_test\n  domain: aml_office\n"
        "  workflow: aml_office_structuring_investigation\n  scenario: aml_office_structuring_investigation\n"
    )
    assert validate_config(str(cfg)) is False


def test_domain_aml_office_with_toggle_passes_validation(tmp_path):
    from mantis.cli.main import validate_config
    cfg = tmp_path / "aml_with_toggle.yaml"
    cfg.write_text(
        "experiment:\n  name: aml_with_toggle_test\n  domain: aml_office\n"
        "  workflow: aml_office_structuring_investigation\n  scenario: aml_office_structuring_investigation\n"
        "aml_office:\n  enabled: true\n"
    )
    assert validate_config(str(cfg)) is True


# ---------------------------------------------------------------------------
# 3. Ported-logic / external-contract drift
# ---------------------------------------------------------------------------

def test_networkx_api_this_integration_calls_by_name_still_exists():
    """Catches: a future networkx major version renaming/removing DiGraph,
    simple_cycles, or NetworkXNoCycle out from under find_mule_rings_for_customer."""
    nx = pytest.importorskip("networkx")
    assert hasattr(nx, "DiGraph")
    assert hasattr(nx, "simple_cycles")
    assert hasattr(nx, "NetworkXNoCycle")
    assert list(nx.simple_cycles(nx.DiGraph())) == []  # simple_cycles(G) must still accept one positional graph


def test_allowed_status_transitions_still_match_citi_p3s_lifecycle():
    """Locks in the exact lifecycle ported from
    citi_banking_backend/app/aml_alert_repository.py's
    ALLOWED_STATUS_TRANSITIONS -- a future edit that loosens or narrows
    this (e.g. allowing cleared -> escalated-to-sar) changes real
    compliance behavior and must be a deliberate, reviewed choice."""
    from mantis.banking.infra.repository import AML_ALERT_STATUS_TRANSITIONS
    assert AML_ALERT_STATUS_TRANSITIONS == {
        "open": {"in-investigation"},
        "in-investigation": {"cleared", "escalated-to-sar"},
        "cleared": set(),
        "escalated-to-sar": set(),
    }
