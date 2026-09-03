# MANTIS & Banking Testbed Architecture

MANTIS provides an adversarial experimentation and observability layer over multi-agent workflows.

---

## 1. High-Level System Architecture

```text
               +-------------------------------------------------+
               |             Declarative Experiment YAML         |
               +-------------------------------------------------+
                                        |
                                        v
+---------------------------------------------------------------------------------+
|                               MANTIS Core                                       |
|                                                                                 |
|   +-------------------+   +--------------------+   +-----------------------+    |
|   | Scenario Registry |   |  Plugin Registry   |   |   Pydantic Schema     |    |
|   +-------------------+   +--------------------+   +-----------------------+    |
|                                                                                 |
|   +-------------------------------------------------------------------------+   |
|   |                         Hook Bus Middleware                             |   |
|   |   Control Points: [input] -> [agent] -> [interaction] -> [tool] -> [out]|   |
|   +-------------------------------------------------------------------------+   |
+---------------------------------------------------------------------------------+
            |                                           |
            v                                           v
+-----------------------+                   +-----------------------+
| Banking Multi-Agent   |                   | Observability Stack   |
| Testbed (ADK/LiteLLM) |                   | (JSONL, OTel, MLflow) |
+-----------------------+                   +-----------------------+
            |
            v
+-----------------------+
| FastMCP Server &      |
| Banking API Backend   |
+-----------------------+
```

---

## 2. The Five Control Points (Hook Bus)

The `HookBus` interceptor sits between agent transitions, tools, and message buses without requiring edits to business logic:

1. **`before_input` / `after_input`**: Raw user prompt interception before agents process it. Used for prompt injection attacks.
2. **`before_agent` / `after_agent`**: Intercepts the agent instruction and context before model invocation. Used for context corruption.
3. **`before_message` / `after_message`**: Intercepts multi-agent routing messages. Used for sender spoofing and route confusion.
4. **`before_tool` / `after_tool`**: Intercepts function tool names, arguments, and return values. Used for unauthorized tool invocation, parameter mutation, and reliability fault injection (delays/errors).
5. **`before_output` / `after_output`**: Filters or audits final responses returned to the caller.

---

## 3. Banking Multi-Agent Workflows

MANTIS implements three production banking workflow domains:

- **Front Office (Real-Time Monitoring & Fraud)**:
  - Router Agent (`front_office_router`) routes requests to `transaction_monitoring_agent`, `fraud_detection_agent`, and `compliance_agent`.
  - Tools: `get_customer_context`, `get_transaction_context`, `search_policies`, `submit_manual_review`.

- **Mid Office (Operational Planning & Schedule Analysis)**:
  - Router Agent (`mid_office_router`) routes requests to `data_analysis_agent`, `support_guidance_agent`, and `validation_agent`.
  - Tools: `get_operations_snapshot`, `get_support_playbooks`, `persist_validated_schedule`.

- **Back Office (End-of-Day Reconciliation & Settlement)**:
  - Router Agent (`back_office_router`) coordinates `validation_checkpoint_agent`, `eod_processing_agent`, `ledger_update_agent`, `reconciliation_agent`, and `report_writing_agent`.
  - Tools: `validate_eod_readiness`, `apply_ledger_updates`, `get_reconciliation_data`, `store_report`.
