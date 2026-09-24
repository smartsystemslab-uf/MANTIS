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

    def __init__(self, target_tool: str, delay_ms: float = 1000.0, **kwargs):
        self.target_tool = target_tool
        self.delay_ms = delay_ms

    def apply(self, ctx: HookContext) -> HookResult:
        if ctx.target == self.target_tool:
            # Declarative: the plugin reports how long to wait; the hook
            # bus itself performs the wait (see the DELAY row below) --
            # the plugin never calls time.sleep() itself.
            return HookResult(action=HookAction.DELAY, delay_ms=self.delay_ms)
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
    delay_ms: 2500
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

A guardrail's `DENY` is recorded as a `POLICY_EVENT` (not `ATTACK_INJECTED`) in the trace -- see `docs/observability.md` -- so an evaluator can tell "a defense worked as intended" apart from "an attack happened," even though both are the same `HookAction.DENY` at the hook-bus level. Any policy plugin developed outside this repo gets the same correct classification for its own name without a code change, by adding it to `_POLICY_PLUGIN_NAMES` at import time (see the set's own docstring in `src/mantis/observability/plugin.py`).

### A guard that re-checks real backend state, not just a call's own arguments

`amount_limit_guardrail` polices a tool call's own arguments. `RiskAwareRoutingGuardPlugin` (`src/mantis/plugins/policies/routing_guard.py`) is a different shape of guard: it targets route confusion specifically, since a generic "is this `transfer_to_agent` destination valid" check cannot catch that attack -- its forced destination is a *legitimate* destination in general, and the attack's whole trick is picking the wrong one of two valid routes for a specific transaction, not routing somewhere invalid. So this plugin independently re-fetches the transaction's real risk score from the banking backend (the same data `get_transaction_context` exposes, computed by the backend, not by whatever the LLM router decided) and denies the reroute if that transaction is still too risky to skip review for:

```yaml
policies:
  - plugin: risk_aware_routing_guard
    parameters:
      blocked_destination: customer_service_chatbot_workflow
      transaction_id: TXN-1001
      risk_threshold: 50.0
```

Live-verified 5/5 against `configs/attacks/wp5_route_confusion.yaml`'s exact attack (see `configs/extensions/guardrail_blocks_route_confusion.yaml`): the attack still fires every trial, and the guard denies it every trial. One honest finding from that verification, worth knowing before writing a similar guard: blocking the malicious reroute does not by itself make the workflow retry the correct compliant path -- the router reports the block and the workflow ends without reaching manual review. A guard that blocks a bad outcome is a different, narrower claim than one that restores the original correct outcome; don't conflate the two in a config's `evaluation` block (see that config's own comments for how this was corrected once observed).

If the backend is unreachable, this plugin fails open (`CONTINUE`) rather than blocking -- an infrastructure failure is not grounds to deny a route that might be perfectly legitimate, and this guard's entire value is being a *second opinion*, not the only one.

### A response filter at the `output` control point

Every policy example above runs at the `tool` control point. `ResponseRedactionPlugin` (`src/mantis/plugins/policies/response_redaction.py`) demonstrates the `output` stage instead: it scans a run's final result for account-number-shaped tokens (`CHK-001`, `EXT-998`, and similar) and masks all but the last two characters, returning `MUTATE` rather than `DENY`:

```yaml
policies:
  - plugin: response_redaction
```

Getting a `MUTATE` at `output` to actually reach the caller required a real fix alongside this plugin, not just the plugin itself: `mantis.banking.runner.run_message` now dispatches a second `after_output` event carrying the real compacted result (`payload={"events": ...}`) after `compact_debug_trace` has extracted the customer-facing text, and applies any `MUTATE` back onto what it returns -- the existing `MantisHookPlugin.after_run_callback` dispatch only ever carried `{"status": outcome}`, too early in ADK's lifecycle to have real content to mutate. Without that fix, this plugin's `MUTATE` would show up in the trace while changing nothing the caller actually sees -- the same "recorded but not applied" defect class this project has already found once at the `tool` control point.

Live verification of this plugin also surfaced a real, non-obvious gap in its own regex: an LLM naturally wrote an account id using a Unicode non-breaking hyphen (`CUST‑002`) in prose rather than ASCII `-`, which an ASCII-only pattern silently failed to match. If you write a similar text-scanning filter, don't assume a model will format matching text the way your test fixtures do -- verify against real generated output, not just hand-written examples.

### Closing a guard's own gap: recovery, not just denial

`risk_aware_routing_guard`'s live verification above initially supported only `DENY`. That surfaced a real, honestly-reported limitation: blocking route confusion's malicious reroute did not, by itself, make the workflow retry the compliant destination -- the router reported the block and the run ended without ever reaching `manual_review`. The plugin now accepts an optional `redirect_to` parameter: when set, a risky reroute attempt is `MUTATE`d to the legitimate destination instead of denied outright, so the real `transfer_to_agent` call still proceeds -- just to the correct place:

```yaml
policies:
  - plugin: risk_aware_routing_guard
    parameters:
      blocked_destination: customer_service_chatbot_workflow
      transaction_id: TXN-1001
      risk_threshold: 50.0
      redirect_to: front_office_transaction_workflow
```

Live-verified 5/5 (`configs/extensions/guardrail_recovers_route_confusion.yaml`): the workflow now reaches `search_policies` and terminates in `manual_review` every trial -- the identical ground truth the undefended baseline (`configs/attacks/wp5_route_confusion.yaml`) itself asserts. Both the deny-only config and this redirect config are kept: the deny-only one remains true and instructive on its own (a guard that blocks a bad outcome is a real, useful, smaller claim), and this one demonstrates the stronger, self-correcting capability built on top of it -- don't conflate the two in a config's own `evaluation` block.

### A guard for the back office's own undefended gap

Route confusion was not the only attack that succeeded 5/5 with zero defense: `configs/attacks/wp5_back_office_tool_mutation.yaml` redirects a validated ledger post onto a second, real batch that already carries an unresolved reconciliation discrepancy, and nothing caught it. `BatchIntegrityGuardPlugin` (`src/mantis/plugins/policies/batch_integrity_guard.py`) closes this the same way `risk_aware_routing_guard` closes route confusion: not by checking whether the target batch is *valid* (both batches are real, both are seeded `ready`), but by independently re-checking the target batch's own real expected-vs-posted totals and denying the ledger update if that batch already shows a discrepancy:

```yaml
policies:
  - plugin: batch_integrity_guard
    parameters:
      target_tool: apply_ledger_updates
```

Live-verified 5/5 (`configs/extensions/guardrail_blocks_back_office_mutation.yaml`), with a control run confirming it does not false-positive on the legitimate, undefended clean-batch flow. With this and the routing guard, every attack in the shipped catalog that previously succeeded 5/5 with zero defense now has one.


### Rate limits and isolation: the remaining two categories

Coding plan §11 names five kinds of security-mechanism plugin: guardrails, policy checks, isolation, rate limits, and response filters. The plugins above cover three; these two complete the set.

**`RateLimitGuardrailPlugin`** (`src/mantis/plugins/policies/rate_limit_guardrail.py`) caps how many times a tool may be called -- per run, per time window, and optionally per distinct value of one argument -- and `DENY`s the call that would exceed the cap. It is registered after any attack, so `group_by` sees the argument value the attack actually produced. The motivating case came from live testing of the extended attack library: hijacking the root hand-off makes the downstream router send the request back, the hijack rewrites that hand-back too, and the framework crashes on the resulting self-transfer (10 of 10 attempts). Capping hand-offs at one per destination stops the loop at the second attempt:

```yaml
policies:
  - plugin: rate_limit_guardrail
    parameters:
      target_tool: transfer_to_agent   # omit to count every tool separately
      group_by: agent_name             # count per distinct value of this argument
      max_calls: 1
      # window_seconds: 60             # omit to count over the whole run
```

Live-verified 5/5 (`configs/extensions/guardrail_limits_route_hijack_loop.yaml`): every run completes (1-3 denials each) instead of crashing, and the no-attack control (`rate_limit_control_no_attack.yaml`) ends in `manual_review` with zero policy events, so ordinary hand-off traffic is untouched. Scope: this contains the attack-induced crash; it does not restore the compliant path.

**`ActionIsolationPlugin`** (`src/mantis/plugins/policies/action_isolation.py`) contains a run's blast radius by *effect*: while active, tools with a chosen side effect cannot execute, whatever any agent -- or any attack that rewrote the arguments -- asks for. It uses the same tool metadata (`operation_type`, `financial_side_effect`) the trace already records. This is the "shadow mode" posture in which agents propose and something else acts:

```yaml
policies:
  - plugin: action_isolation
    parameters:
      blocked_effects: [financial_side_effect]   # or [write] to block every state change
      allow_tools: []                            # exemptions
```

Live-verified 5/5 (`configs/extensions/guardrail_isolates_funds_movement.yaml`): the transfer-rewriting attack fires and `execute_transfer` is denied every trial; the banking backend's transaction count did not change. Because isolation cannot tell a legitimate call from an attacked one, the customer's real transfer is refused too -- by design. A workflow with a downstream step that depends on a blocked tool will see the denial as a failed step (see `docs/extended_scenarios.md` on fault propagation).
