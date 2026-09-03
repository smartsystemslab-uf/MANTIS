# Authoring Attack and Failure Plugins

MANTIS provides a clean plugin contract for authoring adversarial threat injections and reliability failure controls.

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
