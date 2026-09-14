# Authoring Attack, Failure, and Policy Plugins

MANTIS provides a clean plugin contract for authoring adversarial threat injections, reliability failure controls, and (Post-Paper Extension, coding plan §11 "Security mechanism plugins") defensive guardrails -- all three register into the exact same `HookBus` through the identical `apply(ctx) -> HookResult` contract.

---

## 1. Plugin Interface Contract

Every plugin must define:
1. `name`: Unique plugin string identifier.
2. `supported_stages`: Set of hook stages (`input`, `agent`, `interaction`, `tool`, `output`).
3. `apply(ctx: HookContext) -> HookResult`: Core interception logic.

```python
from mantis.hooks import HookContext, HookAction, HookResult

class CustomDelayPlugin:
    name = "custom_delay"
    supported_stages = {"tool"}

    def __init__(self, target_tool: str, delay_seconds: float = 1.0, **kwargs):
        self.target_tool = target_tool
        self.delay_seconds = delay_seconds

    def apply(self, ctx: HookContext) -> HookResult:
        if ctx.target == self.target_tool:
            import time
            time.sleep(self.delay_seconds)
            return HookResult(action=HookAction.CONTINUE)
        return HookResult(action=HookAction.CONTINUE)
```

---

## 2. HookResult Actions

| Action | Meaning |
|---|---|
| `HookAction.CONTINUE` | Allow operation to continue without altering payload. |
| `HookAction.MUTATE` | Replace input/arguments with `payload` provided in `HookResult`. |
| `HookAction.DENY` | Block operation with an optional `error_message`. |
| `HookAction.SKIP` | Skip this stage entirely. |
| `HookAction.ERROR` | Report a failure for this stage (e.g. a simulated timeout), with `error_message`. |
| `HookAction.DELAY` | Declarative: set `delay_ms`, and the hook bus itself waits that long before continuing the chain — a slow dependency, not a blocked one. The plugin never calls `time.sleep()` itself. |

---

## 3. Registering the Plugin

Register your plugin in `src/mantis/core/registry.py` (or dynamically in an extension):

```python
from mantis.core.registry import plugin_registry
from my_module import CustomDelayPlugin

plugin_registry.register("custom_delay", CustomDelayPlugin)
```

---

## 4. Enabling in Configuration

```yaml
attack:
  plugin: custom_delay
  control_point: tool
  target: get_customer_context
  parameters:
    target_tool: get_customer_context
    delay_seconds: 2.5
```

---

## 5. Policy / Guardrail Plugins

A defense follows the identical `apply(ctx) -> HookResult` contract as an attack -- see `AmountLimitGuardrailPlugin` (`src/mantis/plugins/policies/amount_limit_guardrail.py`), registered in `plugin_registry` the same way. It's enabled via a `policies:` list in the experiment config instead of `attack:`, and (per `cli/main.py`) registered onto the `HookBus` *after* any configured attack plugin, so it evaluates a call that an attack has already mutated -- the mechanism behind `configs/extensions/guardrail_blocks_tool_mutation.yaml`, where a guardrail with `max_amount: 2000.0` denies a transfer an attack has just inflated to `5000.0`:

```yaml
policies:
  - plugin: amount_limit_guardrail
    parameters:
      target_tool: execute_transfer
      amount_field: amount
      max_amount: 2000.0
```

A guardrail's `DENY` is recorded as a `POLICY_EVENT` (not `ATTACK_INJECTED`) in the trace -- see `docs/observability.md` -- so an evaluator can tell "a defense worked as intended" apart from "an attack happened," even though both are the same `HookAction.DENY` at the hook-bus level.
