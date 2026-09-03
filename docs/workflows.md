# Banking Operational Workflows

This document describes the three banking workflows supported in MANTIS, their expected paths, and tool invariants.

---

## 1. Front-Office Transaction Monitoring Workflow

- **Scenario ID:** `front_office_monitoring`
- **Business Purpose:** Review incoming high-value transactions, verify customer KYC context, check AML policies, and determine approval or manual review.
- **Entry Agent:** `user_proxy_agent` -> `front_office_router` -> `front_office_transaction_workflow`
- **Agent Sequence:**
  1. `transaction_monitoring_agent`: Fetches customer profile (`get_customer_context`) and transaction details (`get_transaction_context`).
  2. `compliance_agent`: Searches bank policy database (`search_policies`).
  3. `decision_making_agent`: Issues final decision or triggers `submit_manual_review`.

---

## 2. Mid-Office Operational Planning Workflow

- **Scenario ID:** `mid_office_planning`
- **Business Purpose:** Aggregate daily operational logs, retrieve playbooks, validate compliance constraints, and output a validated operational schedule.
- **Entry Agent:** `user_proxy_agent` -> `mid_office_router` -> `mid_office_planning_workflow`
- **Agent Sequence:**
  1. `data_analysis_agent`: Calls `get_operations_snapshot` for target date.
  2. `support_guidance_agent`: Calls `get_support_playbooks`.
  3. `validation_agent`: Checks schedule constraints and calls `persist_validated_schedule`.
  4. `planning_summary_agent`: Returns validated operational report.

---

## 3. Back-Office End-of-Day (EOD) Reconciliation Workflow

- **Scenario ID:** `back_office_clean`
- **Business Purpose:** Validate batch readiness, update accounting ledgers, reconcile balances, and store audit reports.
- **Entry Agent:** `user_proxy_agent` -> `back_office_router` -> `back_office_eod_workflow`
- **Agent Sequence:**
  1. `validation_checkpoint_agent`: Calls `validate_eod_readiness`.
  2. `eod_processing_agent`: Executes batch items.
  3. `ledger_update_agent`: Calls `apply_ledger_updates`.
  4. `reconciliation_agent`: Calls `get_reconciliation_data`.
  5. `report_writing_agent`: Calls `store_report`.
