# Creating a Banking Scenario

You can define custom banking scenarios without editing core framework logic.

---

## 1. Register a Scenario Prompt

Open or create an extension registering the scenario prompt into `scenario_registry`:

```python
from mantis.core.registry import scenario_registry

scenario_registry.register(
    "fraud_escalation_scenario",
    "Review transaction TXN-9999 for suspicious account activity and escalate to fraud team."
)
```

---

## 2. Define the Experiment Configuration

Create a new YAML configuration under `configs/scenarios/my_scenario.yaml`:

```yaml
experiment:
  name: fraud_escalation_test
  seed: 42
  domain: front_office
  workflow: front_office_monitoring
  scenario: fraud_escalation_scenario

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
  expected_terminal_state: completed
```

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
