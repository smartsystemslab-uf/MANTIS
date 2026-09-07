# Zero Trust Backplane — Extension Points

Not implemented in Paper 1. This directory exists so a later Zero Trust
Backplane (a separate research contribution — see the Zero Trust Backplane
Work Plan) has one documented place to plug into MANTIS, without MANTIS
depending on it or requiring it to install or run.

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
Zero Trust enforcement plugin would implement; no concrete policy engine
ships in Paper 1.

## 3. What Zero Trust would add, not modify

- A PEP/PDP generator reading `inventory()` to scope permits per
  agent/tool/domain.
- A concrete `PolicyPlugin` implementation registered into the existing
  `HookBus` — same mechanism attack plugins already use, so it gets the
  same `hook_coverage.json` and trace visibility for free.
- Permit leases and revocation live entirely in the Zero Trust Backplane's
  own state; MANTIS has no enforcement state to coordinate with.

None of this requires changes to `mantis.core`, `mantis.hooks`, or the
banking modules — that's the point of routing through the plugin
interface and the inventory/registry surface instead of a bespoke
integration.
