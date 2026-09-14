# Zero Trust Backplane — Extension Points

Not implemented in Paper 1. This directory exists so a later Zero Trust
Backplane (a separate research contribution — see the Zero Trust Backplane
Work Plan) has one documented place to plug into MANTIS, without MANTIS
depending on it or requiring it to install or run.

**A real, independently-developed Zero Trust Backplane for this same
banking testbed already exists**:
[smartsystemslab-uf/Citi_P3_Zero_Trust_Backplane](https://github.com/smartsystemslab-uf/Citi_P3_Zero_Trust_Backplane).
It implements a much fuller pipeline than this directory's representative
slice — a source-code scanner (Task 2) that discovers agents/tools/edges,
PEP placement (Task 3), a signed PDP issuing `ALLOW`/`DENY`/`MANUAL_REVIEW`/
`ALLOW_WITH_OBLIGATIONS`/`REAUTHENTICATE` decisions (Task 4), and short-lived
signed Permit Leases with replay/request-binding protection (Task 5) — and
already protects real read and write operations against this repo's
`citi_banking_backend`. Its own stated next stage (Task 6) is exactly what
this directory demonstrates a slice of: moving from Backplane-driven direct
tool calls to interception inside the real agent-routed workflow.

The two projects are compatible by construction, not by coincidence: that
project's Task 1/2 *discovers* agents and tools by scanning source code into
a canonical/runtime-binding manifest (e.g. `agent.front_office.fraud` bound
to `runtime_id: fraud_agent`); MANTIS's `inventory()` already reports that
same information live and structurally, since it's introspected from the
running system rather than maintained by hand. `policy_generator.py`'s
`to_zt_manifest_subjects()` demonstrates the mapping directly. A production
integration would use MANTIS's `inventory()` as a live data source for (part
of) that project's `zt_manifest.yaml` in place of its source scanner, and
would swap this directory's own `ZeroTrustEnforcementPlugin` (a minimal,
self-contained default-deny-by-domain stand-in) for a thin `PolicyPlugin`
that calls that project's real, signed Task 4 PDP over its documented
request/response contract instead — the extension point below is unchanged
either way.

Zero Trust consumes two things MANTIS already produces: a banking system
**inventory** and per-run **control-point metadata**. Both are real,
stable interfaces today, not placeholders.

## 1. Application inventory

`BankingRuntimeAdapter.inventory()` (`src/mantis/runtime/adapter.py`) returns a
`BankingSystemInventory` (`src/mantis/runtime/interfaces.py`):

```python
class BankingSystemInventory(BaseModel):
    agents: list[str]
    tools: list[str]
    workflows: list[str]
    domains: dict[str, dict[str, list[str]]]  # domain -> {"agents": [...], "tools": [...]}
```

It's introspected live from `src/mantis/banking/tools/` and
`src/mantis/banking/domains.py` — a PEP/PDP generator can call
`NativeBankingAdapter().inventory()` directly (no ADK/MCP session required)
to get the current agent/tool/domain surface to scope policy over.

## 2. Control-point metadata

Every hook dispatch carries a `HookContext` (`src/mantis/hooks/__init__.py`):

```python
class HookContext(BaseModel):
    run_id: str
    trace_id: str
    workflow_id: str
    stage: Literal['input', 'agent', 'interaction', 'tool', 'output']
    source: str | None
    target: str | None
    payload: dict
    metadata: dict  # business_domain, scenario, specific_hook, security_actions
```

A policy engine registers the same way an attack/failure plugin does —
implementing `apply(ctx: HookContext) -> HookResult` and calling
`hooks.register(...)` — and can `SKIP`/`DENY`/`MUTATE` at any of the five
control points. `src/mantis/plugins/policies/__init__.py` defines
`PolicyPlugin`, the same shape as `ExperimentPlugin`, as the interface a
Zero Trust enforcement plugin implements; Paper 1 itself shipped no
concrete policy engine, but a real one now exists both here (this
directory's representative slice) and, far more completely, in the
Backplane project linked above.

## 3. What this directory implements (a representative slice, not the full Backplane)

- `policy_generator.py`: a PEP/PDP generator reading `inventory()` to scope
  permits per agent/tool/domain (default-deny: an agent may only call
  tools its own domain declares), plus `to_zt_manifest_subjects()` mapping
  that same inventory onto the real Backplane project's canonical/runtime
  ID convention.
- `enforcement_plugin.py`: a concrete `PolicyPlugin`
  (`ZeroTrustEnforcementPlugin`) registered into the existing `HookBus` —
  same mechanism attack and guardrail plugins already use, so it gets the
  same `hook_coverage.json` and trace visibility for free. It lives
  entirely outside `src/mantis` and self-registers into the shared
  `plugin_registry` on import (see `run_with_zero_trust.py`) — MANTIS's own
  code never imports it.
- Permit leases, revocation, and signed decisions are *not* reimplemented
  here — that state lives entirely in a real Zero Trust Backplane's own
  service (see the linked project's Task 4/5); this slice's own enforcement
  logic is intentionally simple (in-process, unsigned, no lease/revocation
  state) so the extension point itself — not a competing security product
  — is what's being demonstrated.

None of this requires changes to `mantis.core`, `mantis.hooks`, or the
banking modules — that's the point of routing through the plugin
interface and the inventory/registry surface instead of a bespoke
integration.
