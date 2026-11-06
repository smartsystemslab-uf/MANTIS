# Zero Trust Backplane -- toggleable integration

A real, toggleable integration of the independently-developed
[`Citi_P3_Zero_Trust_Backplane`](https://github.com/smartsystemslab-uf/Citi_P3_Zero_Trust_Backplane)
project with MANTIS. Strictly an **opt-in extension**: a stock
`pip install -e .` never installs or imports anything here, and every
existing config, test, and run behaves exactly as it does without this
folder.

## Which version this tracks

The Backplane's 2026-10 rewrite (tags `v1.0.0`/`v1.0.1`) replaced its
earlier task-specific PDP microservice entirely with a generic Zero Trust
system for *any* Google ADK application: a real `ZeroTrustPlugin` (an ADK
plugin) registered directly on the application's own `App`/`Runner`, built
from a signed protection bundle that `zt-adk` generates by importing and
introspecting the live agent graph -- not from a hand-written policy file.
This integration tracks that current architecture. The repo is vendored as
a git submodule at `extensions/zero_trust/backplane`, pinned to `v1.0.1`,
the same way every other dependency in this repo is pinned rather than
tracking a moving branch.

(An earlier revision of this integration targeted the superseded
task-specific PDP; see `CHANGELOG.md` for the migration.)

## How the toggle works

`zero_trust: {enabled: true}` in any config turns it on for that run; leave
it out and it is off, with zero code-path difference from a stock MANTIS
run. Unlike every other MANTIS defense, this one is **not** a `PolicyPlugin`
dispatched through `mantis.hooks.HookBus` -- the real Backplane plugin
intercepts at the ADK layer directly, the same layer
`mantis.runtime.plugin.MantisHookPlugin` (MANTIS's own hook bus) is
implemented at. `mantis.banking.runner.run_message` appends it to the ADK
`App`'s own `plugins` list, deliberately *after* `MantisHookPlugin` -- see
the comment there for why that order (not the reverse the Backplane's own
`protected_runner()` helper would use) is the right one for this testbed:
it keeps every attack/policy/observability plugin's dispatch through the
hook bus unconditional, so Zero Trust is a final, independent layer on top
rather than something that can silently prevent MANTIS's own trace from
seeing a call. See `../../configs/extensions/zero_trust_demo.yaml`.

## What's real here, and what's ours

The actual discovery, authorization decision, PSL policy engine, signing,
and audit trail are **the real project's own code** -- nothing here
reimplements that logic. What's new in this folder and in
`src/mantis/plugins/policies/zero_trust_enforcement.py` is the glue:

- `zt_adk.yaml` -- the profile `zt-adk` reads to protect MANTIS. Points
  `app` at `mantis.banking.app:create_app()` (MANTIS's real ADK `App`
  factory, unmodified) so the Backplane's own scanner discovers MANTIS's
  *actual* live agent/tool graph itself, rather than anything hand-written
  here. Two scoping decisions worth being explicit about, both preserving
  the original integration's deliberate choices:
  - `policies.deny_cross_domain_routes: false` -- the build's own warnings
    showed MANTIS's agent tree uses legitimate cross-domain *routing*
    (e.g. `back_office_router` handing off directly to
    `front_office_router`) as normal behavior. This toggle enforces
    domain-scoped *tool* access, not routing; `transfer_to_agent` stays
    unconstrained by it, same as before --
    `risk_aware_routing_guard` already covers routing decisions.
  - `approvals.critical: none` -- the Backplane's human-approval workflow
    for critical tools (e.g. `execute_transfer`) is a real capability this
    profile does not enable, because MANTIS's evaluation is fully
    automated and no paper or test ever put a human in the loop for a
    critical call; enabling it would turn every zero_trust-on critical-tool
    run into a 120s hang waiting for an approval nothing will supply.
- `.zt/bundle/` -- the generated, signed protection bundle (`zt-adk build`
  against the profile above). Committed, like the old integration's
  generated policy files, so a fresh clone doesn't need to rebuild it --
  only after an agent/tool change (`ZeroTrustPlugin.from_profile` checks
  the bundle's fingerprint against the live graph and raises
  `StaleBundleError` if they no longer match; see
  `tests/unit/test_zero_trust_regression_guard.py`).
- `src/mantis/plugins/policies/zero_trust_enforcement.py` -- `ZERO_TRUST_AVAILABLE`
  (the single source of truth for whether the optional dependency is
  installed) and `build_zero_trust_plugin(root_agent)`, which loads the
  committed bundle and constructs the real `ZeroTrustPlugin` against this
  run's actual root agent.

**A finding worth stating plainly, not glossing over**: the new generic
scanner's placements are *per-agent* (which agent's own `tools=[]` list a
tool is actually wired into), not per-domain the way the earlier
integration's own hand-written policy was. That's *stricter*, not looser --
an agent in the same domain as a tool's real owner, but never wired to call
it, is denied too (`tests/unit/test_zero_trust_enforcement.py`'s
`test_same_domain_sibling_agent_without_the_tool_is_still_denied`).
Cross-domain denial (the original claim) still holds, as a strict
consequence of per-agent placement rather than the only boundary enforced.

**A real bug the unit suite didn't catch, a live run did**: the first
version of this migration built the bundle against a bare `create_app()`
(no MCP session). Every live `mantis --run`, though, gives
`build_root_agent` a real session, which attaches one extra passthrough
tool per MCP tool directly onto `user_proxy_agent` -- a structurally
different graph. The unit suite made the identical mistake (it also called
bare `create_app()`), so it passed while every real run would have raised
`StaleBundleError`. Only running `configs/extensions/zero_trust_demo.yaml`
live surfaced it. Fixed by building the bundle against
`create_app_for_scan()` (`src/mantis/banking/app.py`), which spawns the
real MCP server the same way the CLI does; the tests were then corrected
to match. Both `configs/extensions/zero_trust_demo.yaml` and the combined
`configs/extensions/zero_trust_aml_combined_demo.yaml` now run live end to
end with tool-use correctness 1.0.

## Setup

```bash
cd /path/to/MANTIS
extensions/zero_trust/setup.sh                    # once: editable-installs the 7 packages from the pinned submodule
cd extensions/zero_trust
zt-adk keys init --approver ops_lead --secondary risk_officer   # once; local dev keys, never committed
zt-adk build                                       # regenerates .zt/bundle/ -- already committed, re-run after an agent/tool change
zt-adk --profile zt_adk_aml.yaml keys init --approver ops_lead --secondary risk_officer   # once, for the AML-inclusive bundle
zt-adk --profile zt_adk_aml.yaml build              # regenerates .zt_aml/bundle/ -- for aml_office: + zero_trust: together
```

Then, in any config:

```yaml
zero_trust:
  enabled: true     # flip to false (or delete the block) to run the same config without it
```

(The UI's Experiment Editor has the same toggle as a checkbox.)

`mantis --run configs/extensions/zero_trust_demo.yaml` runs a full,
undefended-equivalent legitimate workflow with the toggle on -- every real
tool call is checked by the real plugin, and the run completes identically
to the undefended baseline (`run_artifacts/front_office_monitoring`), which
is the point: a real, independent security layer that is a no-op for
legitimate traffic and fails closed for anything it doesn't recognize.
`configs/extensions/zero_trust_aml_combined_demo.yaml` runs the same check
with `aml_office:` also enabled, against the second bundle below.

## Regenerating the bundle

Re-run after MANTIS's agents, tools, or domains change:

```bash
cd extensions/zero_trust
zt-adk build                                       # the base bundle (zt_adk.yaml)
zt-adk --profile zt_adk_aml.yaml build              # the AML-inclusive bundle (zt_adk_aml.yaml)
```

`zt_adk.yaml` and `.zt/bundle/` are committed (generated, signed,
reproducible from MANTIS's own live agent/tool graph). `.zt/keys/`,
`.zt/approver-keys/`, and `.zt/state/` (dev signing keys, audit log) are
git-ignored and regenerated locally, the same as `.env`.

## Known limits

- Dev signing keys only -- never meant to secure anything beyond a local
  demo.
- `approvals.critical: none` -- the Backplane's human-approval workflow for
  critical operations is a real capability this profile deliberately
  doesn't enable here (see above). `content.prompt_injection` and the other
  input/output-boundary checks the profile leaves at their defaults are a
  real additional surface this integration hasn't separately live-verified
  beyond the `tool`-boundary claims above.
- The distributed runtime (`zt-distributed`, one container per agent,
  SPIFFE identities) is a real capability of the upstream project this
  integration doesn't use -- MANTIS registers the plugin in-process, the
  same way `MantisHookPlugin` itself runs.
