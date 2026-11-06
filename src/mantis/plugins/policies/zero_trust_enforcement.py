"""Zero Trust Backplane enforcement (toggleable integration of the real,
independently-developed project github.com/smartsystemslab-uf/Citi_P3_Zero_Trust_Backplane)
-- not a reimplementation.

## Which version this tracks

The Backplane's 2026-10 rewrite (tags v1.0.0/v1.0.1) replaced its earlier
task-specific PDP microservice entirely with a generic Zero Trust system for
*any* Google ADK application: a real `ZeroTrustPlugin` (an ADK `BasePlugin`)
registered directly on the application's own ADK `App`/`Runner`, built from
a signed protection bundle that `zt-adk` generates by importing and
introspecting the live agent graph -- not from a hand-written policy file.
This module tracks that current architecture, pinned via the git submodule
at `extensions/zero_trust/backplane` (tag v1.0.1).

## How the toggle works

Exactly like every other MANTIS defense: `zero_trust: {enabled: true}` in a
config turns it on for that run; leave it out and it is off, with zero
code-path difference from a stock MANTIS run. A stock install never imports
`zt_adk`: `ZERO_TRUST_AVAILABLE` below is the single source of truth for
whether the optional dependency is present, checked the same way
`core/registry.py` already guards every other optional extension.

Unlike every other MANTIS defense, this one is *not* a `PolicyPlugin`
dispatched through `mantis.hooks.HookBus` -- the real Backplane plugin
intercepts at the ADK layer directly (`before_tool_callback` etc.), the same
layer `mantis.runtime.plugin.MantisHookPlugin` itself is implemented at (see
its module docstring). `build_zero_trust_plugin()` just constructs the real
plugin from the committed bundle; `mantis.banking.runner.run_message` is
what appends it to the ADK `App`'s own `plugins` list, deliberately *after*
`MantisHookPlugin` -- see the comment there for why that order, not the
reverse the Backplane's own `protected_runner()` helper would use, is the
right one for this testbed.

## What it actually does

Domain-scoped tool access: an agent may call a tool in its own domain
(front/mid/back office, or the AML office when enabled); a cross-domain
call, or a call from an agent entirely outside the bundle, is denied by the
PDP's own default. `transfer_to_agent` (routing) is deliberately left
unconstrained by this toggle's profile (`policies.deny_cross_domain_routes:
false` in zt_adk.yaml) -- MANTIS's own agent tree uses legitimate
cross-domain *routing* (e.g. back_office_router handing off directly to
front_office_router) as normal behavior, and MANTIS's own
`risk_aware_routing_guard` already covers routing decisions; this mirrors
the old integration's identical scoping decision. Likewise
`approvals.critical: none`: the Backplane's human-approval workflow for
critical tools is a real capability this profile does not enable here,
because MANTIS's own evaluation is fully automated and no paper or test
ever put a human in the loop for a critical tool call -- enabling it would
silently turn every zero_trust-on critical-tool run into a 120s hang.

The bundle is generated from MANTIS's own live agent/tool graph (`zt-adk
build`, run from `extensions/zero_trust/`, reading
`extensions/zero_trust/zt_adk.yaml`) -- not a hand-written policy file --
and is committed (`extensions/zero_trust/.zt/bundle/`) so it does not need
regenerating on every clone, only after an agent/tool change (the plugin
refuses to start against a stale bundle: `fingerprint_matches_running_code`
is checked on load). The profile's `app:` points at
`mantis.banking.app:create_app_for_scan()`, not the plain `create_app()`
every other caller in this codebase uses: a live `mantis --run` always
gives `build_root_agent` a real MCP session, which attaches one extra
passthrough tool per MCP tool directly onto `user_proxy_agent`, so scanning
with `create_app()` (no session) builds a structurally different graph
that *every* real run's own staleness check then rejects -- a real bug a
first live run (not the unit suite, which made the identical mistake)
caught immediately. `create_app_for_scan()` spawns the real MCP server
subprocess the same way the CLI does, builds the app inside that session,
then returns it; `zt-adk build` tolerates the session closing afterward
because discovery only reads each tool wrapper's `__name__`/`__doc__`, it
never calls one.

## Fail-closed

If the bundle is missing, unsigned, or stale, the plugin raises at
construction time rather than silently running unprotected.

## Setup

    extensions/zero_trust/setup.sh                   # once: editable-installs the 7 packages
    cd extensions/zero_trust && zt-adk keys init --approver ops_lead --secondary risk_officer
    zt-adk build                                      # regenerate after any agent/tool change

Then add `zero_trust: {enabled: true}` to any config.
"""
from pathlib import Path
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parents[4]
_ZT_DIR = _REPO_ROOT / "extensions" / "zero_trust"
# Two profiles, two bundles: the AML office router is a 4th sub_agent on
# the root agent, which changes the live graph's fingerprint, so a run
# with aml_office: also enabled needs the bundle built against
# create_app_with_aml_for_scan() (zt_adk_aml.yaml), not the one built
# against create_app_for_scan() (zt_adk.yaml) -- ZeroTrustPlugin.from_profile's
# own fingerprint check rejects the wrong one as stale. See zt_adk_aml.yaml's
# own comment.
_PROFILE_PATH = _ZT_DIR / "zt_adk.yaml"
_PROFILE_PATH_AML = _ZT_DIR / "zt_adk_aml.yaml"

# Deliberately NOT wrapped in try/except here, for the same reason the old
# integration's import of zt_backplane wasn't: this import must fail loudly
# when the optional dependency isn't installed, so that the *caller's* own
# try/except (around importing *this module*) is the single place that
# decides whether Zero Trust is available at all.
import zt_adk  # noqa: F401
from zt_adk import ZeroTrustPlugin

ZERO_TRUST_AVAILABLE = True


def build_zero_trust_plugin(root_agent: Any, enable_aml: bool = False) -> ZeroTrustPlugin:
    """Load the committed, signed bundle and build the real enforcement
    plugin against this run's actual root agent. enable_aml selects the
    bundle built against the matching agent/tool graph (see the module
    comment above _PROFILE_PATH_AML) -- pass the same flag the caller
    passed to create_app(). Raises if the bundle is missing, unsigned, or
    no longer matches the running agent/tool graph (StaleBundleError) -- a
    security layer that can't verify its own premise must not silently
    start unprotected."""
    profile = _PROFILE_PATH_AML if enable_aml else _PROFILE_PATH
    return ZeroTrustPlugin.from_profile(str(profile), root_agent=root_agent)
