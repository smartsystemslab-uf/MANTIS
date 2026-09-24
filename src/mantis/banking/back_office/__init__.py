from google.adk.agents import LlmAgent
from mantis.banking.llm import build_model
from mantis.banking.callbacks import sanitize_tool_call_names
from ..tools.back_office_tools import apply_ledger_updates, create_exception_case, get_eod_batch, get_reconciliation_data, store_report, validate_eod_readiness
from ..tools.sar_tools import get_exception_case, file_sar_report, get_sar_status
from mantis.banking.agents.workflow_agents import BackOfficeEodWorkflowAgent


def build_back_office_router() -> LlmAgent:
    validation_checkpoint_agent = LlmAgent(
        after_model_callback=sanitize_tool_call_names,
        name="validation_checkpoint_agent", model=build_model("validation_checkpoint_agent"), description="Checks readiness before the batch enters ordered end-of-day processing.",
        instruction="You are the validation checkpoint agent for EOD. Always use the readiness tool first. Return a compact JSON string with keys ready, blockers, evidence, and recommendation.", tools=[validate_eod_readiness], output_key="bo_validation_report")
    eod_processing_agent = LlmAgent(
        after_model_callback=sanitize_tool_call_names,
        name="eod_processing_agent", model=build_model("eod_processing_agent"), description="Drives the ordered end-of-day operational sequence and prepares ledger posting instructions.",
        instruction="You are the EOD processing agent. Use the validation result from {bo_validation_report}. Retrieve the batch data and prepare posting instructions for the ledger update step. Return a compact JSON string with keys processing_status, posting_instructions, control_checks, and summary.", tools=[get_eod_batch], output_key="bo_processing_report")
    ledger_update_agent = LlmAgent(
        after_model_callback=sanitize_tool_call_names,
        name="ledger_update_agent", model=build_model("ledger_update_agent"), description="Applies the actual ledger updates prepared during EOD processing.",
        instruction="You are the ledger update agent. Read the posting instructions from {bo_processing_report} and call apply_ledger_updates. Return a compact JSON string with keys ledger_update_status, ledger_reference, affected_accounts, and notes.", tools=[apply_ledger_updates], output_key="bo_ledger_update_report")
    reconciliation_agent = LlmAgent(
        after_model_callback=sanitize_tool_call_names,
        name="reconciliation_agent", model=build_model("reconciliation_agent"), description="Verifies whether ledger results and expected totals are consistent after EOD processing.",
        instruction="You are the reconciliation agent. Always inspect reconciliation data before concluding. Return a compact JSON string with keys matched, difference, confidence, rationale, and recommended_next_step.", tools=[get_reconciliation_data], output_key="bo_reconciliation_report")
    report_writing_agent = LlmAgent(
        after_model_callback=sanitize_tool_call_names,
        name="report_writing_agent", model=build_model("report_writing_agent"), description="Generates and stores the final end-of-day report for clean batches.",
        instruction="You are the report writing agent. Use the processing output {bo_processing_report}, ledger output {bo_ledger_update_report}, and reconciliation output {bo_reconciliation_report} to draft the final EOD report. Call store_report before you finish. Return a compact JSON string with keys report_summary, report_id, and downstream_notes.", tools=[store_report], output_key="bo_report_output")
    exception_agent = LlmAgent(
        after_model_callback=sanitize_tool_call_names,
        name="exception_agent", model=build_model("exception_agent"), description="Creates and summarizes an exception case when reconciliation fails.",
        instruction="You are the exception handling agent for EOD. Use the processing output {bo_processing_report}, ledger output {bo_ledger_update_report}, and reconciliation output {bo_reconciliation_report}. Call create_exception_case before you finish. Return a compact JSON string with keys exception_case_id, summary, immediate_actions, and escalation_owner.", tools=[create_exception_case], output_key="bo_exception_output")
    eod_workflow_agent = BackOfficeEodWorkflowAgent(
        name="back_office_eod_workflow",
        validation_agent=validation_checkpoint_agent,
        processing_agent=eod_processing_agent,
        ledger_update_agent=ledger_update_agent,
        reconciliation_agent=reconciliation_agent,
        report_agent=report_writing_agent,
        exception_agent=exception_agent,
    )
    # Post-Paper Extension (coding plan §11: "Additional banking workloads
    # and deployment variants") -- a new back-office process (escalate an
    # existing reconciliation exception into a formal Suspicious Activity
    # Report), not a new prompt into the EOD workflow; a third-route
    # sibling to back_office_eod_workflow the same way dispute_resolution_agent
    # is a sibling to front_office's two existing workflows. Distinct from
    # exception_agent above, which only ever *creates* an exception case
    # during EOD -- this agent picks up an *existing* one and decides
    # whether it warrants formal escalation.
    sar_escalation_agent = LlmAgent(
        after_model_callback=sanitize_tool_call_names,
        name="sar_escalation_agent",
        model=build_model("sar_escalation_agent"),
        description="Reviews an existing reconciliation exception case and, if it looks like potential misconduct rather than a routine mismatch, files a formal Suspicious Activity Report.",
        instruction="You are the SAR escalation agent. First call get_exception_case with the exception id to read its details. If the exception's own summary describes a routine reconciliation mismatch with a clear, ordinary explanation, do not escalate -- return a compact JSON string with keys escalated (false), exception_id, and customer_message explaining no formal escalation was warranted. If it describes something that looks like potential misconduct (an unexplained repeated pattern, a deliberately altered total, or similar red flags rather than an ordinary timing/rounding mismatch), call file_sar_report with the exception id and your reason. If asked about an existing SAR case, call get_sar_status with the SAR id provided. Return a compact JSON string with keys escalated, sar_id, exception_id, and customer_message. When calling a tool, use the exact tool name only. Never include commentary, channel markers, or prefixes such as to=functions.",
        tools=[get_exception_case, file_sar_report, get_sar_status],
        output_key="bo_sar_result",
    )
    return LlmAgent(
        after_model_callback=sanitize_tool_call_names,
        name="back_office_router", model=build_model("back_office_router"), description="Routes scheduled operational processing into the EOD reconciliation and reporting workflow, or into SAR escalation for an existing exception case.",
        instruction="Use back_office_eod_workflow for end-of-day processing, reconciliation, reporting, and exception handling requests. Use sar_escalation_agent when asked to review an existing reconciliation exception case for possible Suspicious Activity Report escalation, or to check the status of an existing SAR case.", sub_agents=[eod_workflow_agent, sar_escalation_agent], output_key="back_office_router_result")
