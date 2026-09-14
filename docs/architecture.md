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

MANTIS implements three banking workflow domains (see `src/mantis/banking/domains.py` for the authoritative agent list -- `mantis --inventory` introspects the tool list live from `src/mantis/banking/tools/`, so it never drifts from what's below):

- **Front Office (Real-Time Monitoring, Fraud, Customer Service, and Dispute Resolution)** -- 12 agents:
  - `front_office_router` dispatches into three routes: `front_office_transaction_workflow` (`transaction_monitoring_agent` -> `fraud_detection_agent` -> `compliance_agent` -> `decision_making_agent`), `customer_service_chatbot_workflow` (`chatbot_intent_agent` -> `knowledge_base_agent` or `customer_service_agent` -> `transaction_processing_agent`), and `dispute_resolution_agent` (a single agent, not a multi-step workflow -- Post-Paper Extension, coding plan §11 "Additional banking workloads").
  - Tools (own domain only -- see `src/mantis/runtime/adapter.py:_DOMAIN_TOOL_NAMES`): `get_customer_context`, `get_transaction_context`, `list_recent_transactions`, `submit_manual_review`, `execute_transfer`, `search_policies`, `search_faqs`, `file_dispute`, `get_dispute_status`.

- **Mid Office (Operational Planning and Representative Assist)** -- 12 agents:
  - `mid_office_router` dispatches into `mid_office_planning_workflow` (`data_analysis_agent` -> `forecasting_agent` -> `staff_scheduling_agent` -> `validation_agent` + `support_guidance_agent` in parallel -> `planning_summary_agent`) and `representative_assistant_workflow` (`financial_data_agent`, `recommender_agent`, `loan_agent`, `risk_compliance_agent` in parallel -> `representative_merge_agent`).
  - Tools: `get_customer_financial_profile`, `search_product_catalog`, `search_loan_playbooks`, `get_operations_snapshot`, `get_support_playbooks`, `persist_validated_schedule`, `search_policies` (shared with front office -- both domains' compliance-adjacent work needs policy lookup).

- **Back Office (End-of-Day Reconciliation and Settlement)** -- 8 agents:
  - `back_office_router` coordinates `back_office_eod_workflow`: `validation_checkpoint_agent` -> `eod_processing_agent` -> `ledger_update_agent` -> `reconciliation_agent` -> `report_writing_agent` (clean batch) or `exception_agent` (mismatch).
  - Tools: `validate_eod_readiness`, `get_eod_batch`, `apply_ledger_updates`, `get_reconciliation_data`, `create_exception_case`, `store_report`.
