# Creating a Banking Scenario

You can define custom banking scenarios without editing core framework logic.

---

## 1. Register a Scenario Prompt

Scenario prompts live in `src/mantis/banking/scenarios/__init__.py`'s `SCENARIOS` dict, which `mantis.core.registry` reads at import time to populate `scenario_registry` -- that's what the `mantis` CLI actually loads, so a scenario added anywhere else won't be visible to `mantis --run` even though `scenario_registry.register(...)` itself is a perfectly real, callable API for programmatic use (e.g. from a notebook or your own script):

```python
from mantis.banking.scenarios import SCENARIOS

SCENARIOS["front_office_fraud_escalation"] = (
    "Review transaction TXN-9999 for suspicious account activity and escalate to the fraud team."
)
```

The id's prefix must be one of `front_office`, `mid_office`, or `back_office` -- `mantis.banking.workflows` derives each workflow's domain from that prefix, so an id like `fraud_escalation_scenario` (no real domain prefix) will register but resolve to a domain that doesn't exist in `domain_registry`.

---

## 2. Define the Experiment Configuration

Create a new YAML configuration under `configs/scenarios/my_scenario.yaml`:

```yaml
experiment:
  name: fraud_escalation_test
  seed: 42
  domain: front_office
  workflow: front_office_fraud_escalation
  scenario: front_office_fraud_escalation

observability:
  mode: full
  export:
    - jsonl

evaluation:
  expected_tools:
    - get_customer_context
    - get_transaction_context
  forbidden_tools:
    - execute_transfer
  expected_terminal_state: manual_review
```

This exact scenario and config are checked into the repo (`configs/scenarios/my_scenario.yaml`) so the commands below work as shown, not just as a template.

---

## 3. Validate and Run

```bash
# Validate against schema
mantis --validate configs/scenarios/my_scenario.yaml

# Run the scenario
mantis --run configs/scenarios/my_scenario.yaml

# Evaluate the execution trace
mantis --evaluate run_artifacts/fraud_escalation_test
```

`expected_terminal_state` here reflects what this scenario's prompt asks the agents to do (escalate for manual review), not a guarantee -- like every live-LLM scenario in this repo, the exact path taken can vary between runs.
