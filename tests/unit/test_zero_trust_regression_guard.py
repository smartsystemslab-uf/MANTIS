"""Regression guards for the Zero Trust Backplane integration.

Not the same job as test_zero_trust_enforcement.py (which checks the real
plugin's actual authorization decisions) or
test_zero_trust_toggle_without_dependency.py (the missing-dependency error
path). This file exists so that a future, unrelated change elsewhere in
MANTIS -- renaming an agent, reshaping the plugin-ordering contract,
editing the config model, adding a domain -- fails loudly here instead of
silently breaking Zero Trust enforcement, the on/off toggle, or its
SecurityEvent classification. Three risk categories, one class each:

1. MANTIS-side drift: the committed, signed bundle still matches MANTIS's
   actual *live* agent/tool graph -- so if someone adds an agent or tool
   without re-running `zt-adk build`, this notices (via the real
   `fingerprint_matches_running_code` check `ZeroTrustPlugin.from_profile`
   itself performs -- not reimplemented here), and a genuinely mismatched
   graph is confirmed to still raise, by deliberately building against the
   wrong root agent.
2. Toggle wiring drift: `zero_trust: {enabled: true}` keeps threading
   through to LegacyBankingHandle's enable_zero_trust flag the same way
   aml_office's does, and the registry visibility / _POLICY_PLUGIN_NAMES /
   MantisHookPlugin.after_tool_callback synthesized security_actions
   symmetry (on which "denied vs a normal tool result" trace
   classification depends, since Zero Trust denies outside HookBus
   entirely -- see runner.py's plugin-ordering comment) stays intact --
   this class runs even without the optional dependency installed, since
   that's precisely the state most future changes will be tested in.
3. External contract drift: the real project's own API surface this
   integration calls by name (ZeroTrustPlugin.from_profile's signature,
   before_tool_callback's kwargs, the denial dict's shape) hasn't silently
   changed underneath us. We don't control that project's release cadence
   -- see extensions/zero_trust/README.md's "Keeping this in sync" note.
"""
import asyncio
import inspect
from unittest.mock import MagicMock

import pytest

from mantis.config.models import ExperimentConfig, ZeroTrustConfig
from mantis.observability.plugin import _POLICY_PLUGIN_NAMES


# ---------------------------------------------------------------------------
# 1. MANTIS-side drift: the committed bundle vs. the system's actual live state
#
# pytest.importorskip("zt_adk") is called *inside* each test below, not at
# module level -- a module-level importorskip skips the whole file's
# collection, which would also skip category 2's tests that must run
# without the optional dependency installed.
# ---------------------------------------------------------------------------


def test_the_committed_bundle_matches_the_live_agent_graph_right_now():
    """Catches: an agent/tool added to MANTIS's banking code without
    re-running `zt-adk build` (from extensions/zero_trust/) -- the plugin
    would otherwise either run with a silently-stale graph, or refuse to
    start. If this fails, run `zt-adk build` and commit the regenerated
    extensions/zero_trust/.zt/bundle/. Uses create_app_for_scan(), not
    create_app(): the bundle was built against a real MCP session (one
    extra passthrough tool per MCP tool on user_proxy_agent -- see that
    function's own docstring), so this spawns the real MCP server
    subprocess, the same as a live run would."""
    pytest.importorskip("zt_adk")
    from mantis.banking.app import create_app_for_scan
    from mantis.plugins.policies.zero_trust_enforcement import build_zero_trust_plugin

    build_zero_trust_plugin(create_app_for_scan().root_agent)  # raises StaleBundleError if mismatched


def test_the_aml_inclusive_bundle_also_matches_its_own_live_agent_graph():
    """The AML office router is a 4th sub_agent, which changes the live
    graph's fingerprint -- a run with both zero_trust and aml_office
    enabled needs the *other* committed bundle (zt_adk_aml.yaml's), not the
    one above. If this fails, rebuild it:
    `zt-adk --profile extensions/zero_trust/zt_adk_aml.yaml build`.
    Uses create_app_with_aml_for_scan() for the same reason the test above
    uses create_app_for_scan() -- see that function's own docstring."""
    pytest.importorskip("zt_adk")
    from mantis.banking.app import create_app_with_aml_for_scan
    from mantis.plugins.policies.zero_trust_enforcement import build_zero_trust_plugin

    build_zero_trust_plugin(create_app_with_aml_for_scan().root_agent, enable_aml=True)


def test_enable_aml_selects_the_matching_bundle_not_the_mismatched_one():
    """Catches: build_zero_trust_plugin's enable_aml flag not actually
    switching which profile/bundle loads -- each graph is only valid
    against its own bundle, so the wrong pairing must raise, and the
    right pairing must not."""
    pytest.importorskip("zt_adk")
    from zt_adk.plugin import StaleBundleError

    from mantis.banking.app import create_app
    from mantis.plugins.policies.zero_trust_enforcement import build_zero_trust_plugin

    aml_root = create_app(enable_aml=True).root_agent
    with pytest.raises(StaleBundleError):
        build_zero_trust_plugin(aml_root, enable_aml=False)  # AML graph, non-AML bundle

    plain_root = create_app().root_agent
    with pytest.raises(StaleBundleError):
        build_zero_trust_plugin(plain_root, enable_aml=True)  # plain graph, AML bundle


def test_a_genuinely_different_agent_graph_is_rejected_as_stale():
    """Deliberately injects drift (a different root agent than the bundle
    was built for) and confirms the real StaleBundleError actually fires --
    the thing the test above relies on to ever catch a real mismatch."""
    pytest.importorskip("zt_adk")
    from zt_adk.plugin import StaleBundleError

    from mantis.banking.app import create_app
    from mantis.plugins.policies.zero_trust_enforcement import build_zero_trust_plugin

    wrong_root = create_app().root_agent.sub_agents[0]  # a real agent, just not the bundle's root
    with pytest.raises(StaleBundleError):
        build_zero_trust_plugin(wrong_root)


# ---------------------------------------------------------------------------
# 2. Toggle wiring drift -- runs with or without the optional dependency
# ---------------------------------------------------------------------------

def test_zero_trust_config_defaults_are_unchanged():
    """Catches: someone changing ZeroTrustConfig's default, silently
    changing what a bare `zero_trust: {}` means."""
    cfg = ZeroTrustConfig()
    assert cfg.enabled is True


def test_toggle_threads_through_to_enable_zero_trust_exactly_like_aml_office(monkeypatch):
    """Catches: a future refactor of LegacyBankingHandle.run_message (or
    runner.run_message's signature) breaking the config -> flag wiring --
    mirrors how test_aml_office's own regression guard checks enable_aml."""
    from mantis.runtime.adapter import LegacyBankingHandle

    captured = {}

    async def fake_run_message(message, **kwargs):
        captured.update(kwargs)
        return {}

    monkeypatch.setattr("mantis.banking.runner.run_message", fake_run_message)

    cfg_on = ExperimentConfig(**{
        "experiment": {"name": "x", "domain": "front_office", "workflow": "w", "scenario": "s"},
        "zero_trust": {"enabled": True},
    })
    asyncio.run(LegacyBankingHandle(config=cfg_on).run_message("hi"))
    assert captured["enable_zero_trust"] is True

    captured.clear()
    cfg_off = ExperimentConfig(**{
        "experiment": {"name": "x", "domain": "front_office", "workflow": "w", "scenario": "s"},
        "zero_trust": {"enabled": False},
    })
    asyncio.run(LegacyBankingHandle(config=cfg_off).run_message("hi"))
    assert captured["enable_zero_trust"] is False

    captured.clear()
    cfg_absent = ExperimentConfig(**{
        "experiment": {"name": "x", "domain": "front_office", "workflow": "w", "scenario": "s"},
    })
    asyncio.run(LegacyBankingHandle(config=cfg_absent).run_message("hi"))
    assert captured["enable_zero_trust"] is False


def test_registry_visibility_flag_reflects_whether_the_dependency_is_importable():
    """Catches: ZERO_TRUST_AVAILABLE (the single source of truth
    cli/main.py's validate_config checks) drifting out of sync with
    whether zt_adk is actually importable."""
    from mantis.core import registry

    try:
        import zt_adk  # noqa: F401
        importable = True
    except ImportError:
        importable = False
    assert registry.ZERO_TRUST_AVAILABLE is importable


def test_policy_event_classification_stays_wired_for_a_zero_trust_denial():
    """Catches: _POLICY_PLUGIN_NAMES dropping "zero_trust_enforcement", or
    MantisHookPlugin.after_tool_callback's synthesized security_actions
    marker drifting out of the shape ObservabilityPlugin reads -- either
    one would silently misclassify a real Zero Trust denial as an
    indistinguishable normal tool result instead of a POLICY_EVENT."""
    assert "zero_trust_enforcement" in _POLICY_PLUGIN_NAMES

    from mantis.hooks import HookBus
    from mantis.runtime.plugin import MantisHookPlugin

    bus = HookBus()
    seen = {}

    class _Spy:
        name = "spy"
        supported_stages = {"tool"}
        def apply(self, ctx):
            from mantis.hooks import HookAction, HookResult
            seen["security_actions"] = ctx.metadata.get("security_actions")
            return HookResult(action=HookAction.CONTINUE)

    bus.register(_Spy())
    plugin = MantisHookPlugin(bus)
    tool_context = MagicMock(agent_name="transaction_monitoring_agent", function_call_id="c1")
    tool = MagicMock()
    tool.name = "get_eod_batch"
    asyncio.run(plugin.after_tool_callback(
        tool=tool, tool_args={},
        tool_context=tool_context,
        result={"status": "zero_trust_denied", "boundary": "tool", "reason": "NO_GENERATED_PEP", "decision": "DENY"},
    ))
    assert seen["security_actions"] == [{"plugin": "zero_trust_enforcement", "action": "deny"}]


# ---------------------------------------------------------------------------
# 3. External contract drift -- the real project's API surface we call by name
# ---------------------------------------------------------------------------

def test_zero_trust_plugin_from_profile_still_accepts_the_arguments_this_code_passes():
    """Catches: the real project renaming or dropping from_profile's
    `root_agent` keyword -- the exact argument build_zero_trust_plugin
    calls it with."""
    pytest.importorskip("zt_adk")
    from zt_adk import ZeroTrustPlugin

    params = set(inspect.signature(ZeroTrustPlugin.from_profile).parameters)
    assert "root_agent" in params


def test_before_tool_callback_still_accepts_the_kwargs_adk_calls_it_with():
    """Catches: the real project's before_tool_callback signature drifting
    out of sync with what ADK's PluginManager (and our own synthetic tests
    in test_zero_trust_enforcement.py) call it with."""
    pytest.importorskip("zt_adk")
    from zt_adk import ZeroTrustPlugin

    params = set(inspect.signature(ZeroTrustPlugin.before_tool_callback).parameters)
    assert {"tool", "tool_args", "tool_context"} <= params


def test_a_denial_still_has_the_shape_this_integration_reads():
    """Catches: the real project renaming status/decision in its denial
    dict -- the exact fields MantisHookPlugin.after_tool_callback's
    zero_trust_denied check, and this integration's docs/papers, read."""
    pytest.importorskip("zt_adk")
    from mantis.banking.app import create_app_for_scan
    from mantis.plugins.policies.zero_trust_enforcement import build_zero_trust_plugin

    plugin = build_zero_trust_plugin(create_app_for_scan().root_agent)
    tool_context = MagicMock(agent_name="not_a_real_mantis_agent", invocation_id="contract-check", function_call_id="c1", node_path="")
    tool = MagicMock()
    tool.name = "get_eod_batch"
    result = asyncio.run(plugin.before_tool_callback(tool=tool, tool_args={}, tool_context=tool_context))
    assert result is not None
    assert {"status", "boundary", "reason", "decision"} <= set(result)
    assert result["status"] == "zero_trust_denied"
