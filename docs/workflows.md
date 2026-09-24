# Banking Operational Workflows

This document describes the banking workflows supported in MANTIS, their expected paths, and tool invariants.

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

---

## 4. Front-Office Dispute Resolution Workflow *(Post-Paper Extension, coding plan §11 "Additional banking workloads and deployment variants")*

- **Scenario ID:** `front_office_card_dispute`
- **Business Purpose:** File a new transaction dispute case, or look up the status of an existing one -- a genuinely new front-office process, not a new prompt into an existing workflow.
- **Entry Agent:** `user_proxy_agent` -> `front_office_router` -> `dispute_resolution_agent` (a third route alongside the transaction-review and chatbot workflows, not a custom multi-agent workflow of its own)
- **Agent Sequence:**
  1. `dispute_resolution_agent`: Calls `file_dispute` (new case) or `get_dispute_status` (existing case), backed by a real `disputes` table in the same SQLite repository `submit_manual_review` uses.
- Distinct from `front_office_chatbot`'s existing FAQ-style "how do I dispute a transaction" informational answer, which stays purely informational and never files a real case.

---

## 5. Back-Office SAR/Exception Escalation Workflow *(Post-Paper Extension, coding plan §11 "Additional banking workloads and deployment variants")*

- **Scenario ID:** `back_office_sar_escalation`
- **Business Purpose:** Review an existing end-of-day reconciliation exception case and, if it looks like potential misconduct rather than a routine mismatch, escalate it to a formal Suspicious Activity Report -- a genuinely new back-office process, not a new prompt into the existing EOD workflow.
- **Entry Agent:** `user_proxy_agent` -> `back_office_router` -> `sar_escalation_agent` (a second route alongside `back_office_eod_workflow`)
- **Agent Sequence:**
  1. `sar_escalation_agent`: Calls `get_exception_case` to read an existing exception's details, then `file_sar_report` if it warrants escalation (or `get_sar_status` to check an existing SAR case), backed by a new `sar_reports` table in the same SQLite repository the EOD workflow's `exceptions` table lives in.
- References `EX-SEEDED01`, a pre-seeded exception worded with clear misconduct signals (an unexplained, repeated, round-number discrepancy with no source-system corroboration) rather than an ordinary timing/rounding mismatch a model would reasonably decline to escalate.

---

## 6. Mid-Office Loan Pre-Approval Workflow *(Post-Paper Extension, coding plan §11 "Additional banking workloads and deployment variants")*

- **Scenario ID:** `mid_office_loan_preapproval`
- **Business Purpose:** Submit a loan/credit-line application and receive a real, computed pre-approval decision -- distinct from the existing `loan_agent` (inside `representative_assistant_workflow`), which only ever returns informational process guidance and never makes or persists an actual decision.
- **Entry Agent:** `user_proxy_agent` -> `front_office_router` -> `mid_office_router` -> `loan_preapproval_agent` (a third route alongside the planning and representative-assist workflows)
- **Agent Sequence:**
  1. `loan_preapproval_agent`: Calls `submit_loan_application`, which computes a deterministic decision from the customer's real seeded data (approve if the requested amount is within a threshold percentage of the customer's total account balance and risk tier is not high, else refer to manual underwriting) and persists it to a new `loan_applications` table. `get_loan_application_status` looks up an existing application.

### Deployment variant: a second institution profile

The identical agent, tool, and decision logic above also runs against a second, smaller institution profile -- the "institutions" half of coding plan §11's "Additional banking workloads *and deployment variants*" bullet, distinct from the three genuinely new processes above. Set `experiment.institution: regional_credit_union` in a config (see `configs/extensions/institution_regional_credit_union_loan.yaml`) to run against:

- **Scenario ID:** `mid_office_loan_preapproval_credit_union`
- **What differs:** a separate, isolated SQLite database (`banking_regional_credit_union.db`, never the default `banking.db`), its own seeded member (`CUST-101`, Maria Alvarez, a $3,000 checking balance), and a genuinely stricter approval threshold (10% of balance, vs. the default institution's 25% -- see `_LOAN_APPROVAL_THRESHOLD_PCT` in `src/mantis/banking/infra/repository.py`). No agent, tool, or workflow code differs between institutions; only the seeded data and the policy threshold do.
- **Live-verified 5/5:** a $500 request against CUST-101's $3,000 balance (16.7%) is correctly `referred` under this institution's 10% threshold -- the identical request would have been `approved` at the default institution's 25%.
