# Modifying an Agent via YAML

In MANTIS, individual agent behaviors, underlying models, or enablement can be modified declaratively in the configuration file without touching Python code.

---

## 1. Syntax for Agent Modifications

Use the `modifications.agents` block in any experiment YAML:

```yaml
experiment:
  name: modified_agent_experiment
  seed: 42
  domain: front_office
  workflow: front_office_monitoring
  scenario: front_office_monitoring

modifications:
  agents:
    transaction_monitoring_agent:
      model: gpt-4-turbo
      enabled: true
    fraud_detection_agent:
      model: default
      enabled: false  # Bypasses or disables this agent
```

---

## 2. Supported Properties

| Property | Type | Description |
|---|---|---|
| `model` | `string` | Target LLM endpoint or model tag |
| `enabled` | `boolean` | Flag to enable or disable the agent in workflow routing |

---

## 3. Validating Modifications

Verify that the modifications conform to the Pydantic schema:

```bash
mantis --validate configs/my_experiment.yaml
mantis --inspect configs/my_experiment.yaml
```
