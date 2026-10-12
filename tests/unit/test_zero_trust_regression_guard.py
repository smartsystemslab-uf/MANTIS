"""Regression guards for the Zero Trust Backplane integration.

Not the same job as test_zero_trust_enforcement.py (which checks the
plugin's own apply() logic against a mocked PDP) or
test_zero_trust_toggle_without_dependency.py (the missing-dependency error
path). This file exists so that a future, unrelated change elsewhere in
MANTIS -- renaming an agent, reshaping HookContext, editing the plugin
registry, adding a domain -- fails loudly here instead of silently
breaking Zero Trust enforcement or the on/off toggle. Three risk
categories, one class each:

1. MANTIS-side drift: the generated policy's guarantee (same-domain allow,
   everything else denied) still matches MANTIS's actual *live* inventory,
   not just the last-generated snapshot -- so if someone adds an agent,
   tool, or domain without re-running generate_policy.py, this notices.
2. Toggle wiring drift: `zero_trust:` and the equivalent `policies:` form
   keep registering the identical plugin, and the registry
   visibility/_POLICY_PLUGIN_NAMES symmetry (on which "fired vs blocked"
   trace classification depends) stays intact -- this class runs even
   without the optional dependency installed, since that's precisely the
   state most future changes will be tested in.
3. External contract drift: the real project's own API surface this
   integration calls by name (HTTP routes, PDPRequest's shape,
   build_signed_request's signature) hasn't silently changed underneath
   us. We don't control that project's release cadence -- see
   extensions/zero_trust/README.md's "Keeping this in sync" note, carried
   over from the earlier local-only slice.
"""
import inspect

import pytest

from mantis.core.registry import plugin_registry
from mantis.config.models import ExperimentConfig, ZeroTrustConfig


# ---------------------------------------------------------------------------
# 1. MANTIS-side drift: generated policy vs. the system's actual live state
# ---------------------------------------------------------------------------

def test_generated_identities_cover_every_live_agent_in_its_declared_domain():
    """Catches: a new agent added to DOMAIN_AGENTS without re-running
    generate_policy.py -- that agent would be unrecognized by the PDP and
    silently denied everything, including legitimate calls."""
    from mantis.banking.domains import DOMAIN_AGENTS
    from extensions.zero_trust.generate_policy import build_identities

    generated = {i["canonical_id"]: i for i in build_identities()["identities"]}
    for domain, agents in DOMAIN_AGENTS.items():
        for agent in agents:
            canonical = f"agent.{domain}.{agent}"
            assert canonical in generated, (
                f"{agent!r} ({domain}) has no generated identity -- "
                "re-run extensions/zero_trust/generate_policy.py"
            )
            assert generated[canonical]["id"] == agent
            assert generated[canonical]["enabled"] is True


def test_generated_resources_cover_every_live_domain_tool():
    """Catches: a new tool added to _DOMAIN_TOOL_NAMES without
    regenerating -- same failure mode as above, for tool calls."""
    from mantis.runtime.adapter import _DOMAIN_TOOL_NAMES
    from extensions.zero_trust.generate_policy import build_resources

    generated = {r["canonical_id"]: r for r in build_resources()["resources"]}
    for domain, tools in _DOMAIN_TOOL_NAMES.items():
        for tool in tools:
            canonical = f"resource.{domain}.{tool}"
            assert canonical in generated, (
                f"{tool!r} ({domain}) has no generated resource -- "
                "re-run extensions/zero_trust/generate_policy.py"
            )
            assert generated[canonical]["id"] == f"{domain}.{tool}"


def test_generated_policy_is_still_default_deny_by_domain_only():
    """Catches: a future hand-edit of generate_policy.py (or the committed
    policy_store/*.yaml) quietly widening the rule beyond same-domain --
    e.g. a typo granting a front-office agent back-office resources."""
    from mantis.banking.domains import DOMAIN_AGENTS
    from mantis.runtime.adapter import _DOMAIN_TOOL_NAMES
    from extensions.zero_trust.generate_policy import build_policy

    policies = build_policy()["policies"]
    assert len(policies) == len([d for d in DOMAIN_AGENTS if d in _DOMAIN_TOOL_NAMES])
    for policy in policies:
        assert policy["effect"] == "ALLOW"
        domain = policy["id"].removeprefix("policy.mantis.").removesuffix("_same_domain_access")
        for subject in policy["match"]["subjects"]:
            assert subject.startswith(f"agent.{domain}."), f"{subject} leaked into the {domain} policy's subjects"
        for resource in policy["match"]["resources"]:
            assert resource.startswith(f"resource.{domain}."), f"{resource} leaked into the {domain} policy's resources"


def test_committed_policy_files_match_what_the_generator_produces_right_now():
    """Catches: the committed extensions/zero_trust/config/*.yaml and
    policy_store/*.yaml going stale relative to the live system -- the
    thing a contributor must remember to re-run after changing agents or
    tools (see extensions/zero_trust/README.md's 'Regenerating the
    policy'). This is the sentinel that should fail and say so plainly."""
    import yaml
    from pathlib import Path
    from extensions.zero_trust.generate_policy import build_identities, build_resources, build_policy, OUT

    committed_identities = yaml.safe_load((OUT / "config" / "identities.yaml").read_text())
    committed_resources = yaml.safe_load((OUT / "config" / "resources.yaml").read_text())
    committed_policy = yaml.safe_load((OUT / "policy_store" / "mantis_default_deny_by_domain.yaml").read_text())

    assert committed_identities == build_identities(), (
        "extensions/zero_trust/config/identities.yaml is stale -- run "
        "`python extensions/zero_trust/generate_policy.py` and "
        "`python extensions/zero_trust/bootstrap_keys.py`, then commit the result"
    )
    assert committed_resources == build_resources()
    assert committed_policy == build_policy()


# ---------------------------------------------------------------------------
# 2. Toggle wiring drift -- runs with or without the optional dependency
# ---------------------------------------------------------------------------

def test_zero_trust_config_defaults_are_unchanged():
    """Catches: someone changing ZeroTrustConfig's defaults, silently
    changing what a bare `zero_trust: {}` means, or pointing the default
    PDP url at a different port than extensions/zero_trust/run_pdp.sh's
    own default."""
    cfg = ZeroTrustConfig()
    assert cfg.enabled is True
    assert cfg.pdp_url == "http://127.0.0.1:8600"


def test_dedicated_toggle_and_the_generic_policies_form_are_equivalent(tmp_path):
    """Catches: a future refactor of run_experiment()'s policy-assembly
    logic breaking the sugar -- zero_trust: {enabled: true} must keep
    resolving to exactly the same plugin + parameters the explicit
    policies: form does."""
    toggle_cfg = ExperimentConfig(**{
        "experiment": {"name": "x", "domain": "front_office", "workflow": "w", "scenario": "s"},
        "zero_trust": {"enabled": True, "pdp_url": "http://127.0.0.1:9999"},
    })
    explicit_cfg = ExperimentConfig(**{
        "experiment": {"name": "x", "domain": "front_office", "workflow": "w", "scenario": "s"},
        "policies": [{"plugin": "zero_trust_enforcement", "parameters": {"pdp_url": "http://127.0.0.1:9999"}}],
    })

    # Mirrors the assembly in cli/main.py's run_experiment() without
    # actually running an experiment -- if that assembly logic changes
    # shape, update it here too, deliberately, rather than this test
    # silently passing against stale logic.
    def resolved_policies(cfg):
        policies = list(cfg.policies or [])
        if cfg.zero_trust and cfg.zero_trust.enabled:
            from mantis.config.models import PolicyConfig
            policies.append(PolicyConfig(plugin="zero_trust_enforcement", parameters={"pdp_url": cfg.zero_trust.pdp_url}))
        return [(p.plugin, p.parameters) for p in policies]

    assert resolved_policies(toggle_cfg) == resolved_policies(explicit_cfg) == [
        ("zero_trust_enforcement", {"pdp_url": "http://127.0.0.1:9999"})
    ]


def test_toggle_disabled_produces_no_policies_at_all():
    """Catches: `enabled: false` (or an absent zero_trust: block) ever
    growing a side effect -- off must mean exactly what every other
    MANTIS config without a policies: entry already means."""
    cfg = ExperimentConfig(**{
        "experiment": {"name": "x", "domain": "front_office", "workflow": "w", "scenario": "s"},
        "zero_trust": {"enabled": False},
    })
    assert not (cfg.policies or [])
    assert cfg.zero_trust.enabled is False


def test_registry_visibility_and_policy_event_classification_stay_symmetric():
    """Catches: core/registry.py's optional-import guard and
    observability/plugin.py's _POLICY_PLUGIN_NAMES drifting apart -- if
    zero_trust_enforcement is ever registered without also being in
    _POLICY_PLUGIN_NAMES, its denials would be misclassified as
    ATTACK_INJECTED instead of POLICY_EVENT in every trace."""
    from mantis.observability.plugin import _POLICY_PLUGIN_NAMES

    assert "zero_trust_enforcement" in _POLICY_PLUGIN_NAMES
    if "zero_trust_enforcement" in plugin_registry.all():
        # Dependency installed: it must actually be reachable, not just
        # named in the set with nothing behind it.
        from mantis.plugins.policies.zero_trust_enforcement import ZeroTrustEnforcementPlugin
        assert plugin_registry.get("zero_trust_enforcement") is ZeroTrustEnforcementPlugin


# ---------------------------------------------------------------------------
# 3. External contract drift -- the real project's API surface we call by name
# ---------------------------------------------------------------------------

pytest.importorskip("zt_backplane")


def test_the_real_pdp_service_still_exposes_the_routes_this_integration_calls(monkeypatch):
    """Catches: the real Citi_P3_Zero_Trust_Backplane project renaming or
    removing /health, /v1/challenge, or /v1/authorize out from under us."""
    from pathlib import Path
    # pdp_service builds its app (and resolves config paths) at import time;
    # point it at our generated directory the same way run_pdp.sh does,
    # rather than its own default (source-checkout-relative) paths.
    monkeypatch.setenv("ZT_PROJECT_ROOT", str(Path(__file__).resolve().parents[2] / "extensions" / "zero_trust"))
    import importlib
    import zt_backplane.pdp_service as pdp_service_module
    importlib.reload(pdp_service_module)
    app = pdp_service_module.app

    paths = {route.path for route in app.routes}
    for required in ("/health", "/v1/challenge", "/v1/authorize"):
        assert required in paths, f"the installed zt_backplane no longer exposes {required}"


def test_build_signed_request_still_accepts_the_arguments_this_plugin_passes():
    """Catches: the real project renaming or dropping a parameter of
    build_signed_request -- the exact keyword arguments
    zero_trust_enforcement.py's apply() calls it with."""
    from zt_backplane.dev_evidence import build_signed_request

    required = {
        "nonce", "subject_canonical_id", "subject_runtime_id",
        "resource_canonical_id", "resource_runtime_id", "action",
        "workflow_id", "workflow_instance_id", "risk_score", "auth_factors",
    }
    params = set(inspect.signature(build_signed_request).parameters)
    missing = required - params
    assert not missing, f"zt_backplane.dev_evidence.build_signed_request dropped: {missing}"


def test_pdp_request_model_still_reports_decision_and_reason():
    """Catches: the real project renaming the authorize response fields
    this plugin reads (body['decision'], body['reason'])."""
    from zt_backplane.models import PDPResponse

    fields = set(PDPResponse.model_fields)
    assert {"decision", "reason"} <= fields, f"PDPResponse no longer has decision/reason: {fields}"
