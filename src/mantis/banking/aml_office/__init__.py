"""AML (Anti-Money Laundering) office, ported from Citi_P3's
citi_banking_adk/bank_adk/agents/aml_office.py. A 4th banking domain,
toggleable per-run via ExperimentConfig.aml_office (see
mantis.banking.agents.root.build_root_agent) -- disabled by default so
every existing front/mid/back-office experiment is unaffected.
"""
from google.adk.agents import LlmAgent
from mantis.banking.llm import build_model
from mantis.banking.callbacks import sanitize_tool_call_names
from ..tools.aml_tools import (
    check_threshold_anomaly,
    detect_structuring,
    find_mule_rings_for_customer,
    get_aml_alert,
    list_aml_alerts,
    transition_aml_alert_status,
    verify_identity_document,
)
from ..tools.customer_tools import get_customer_context, list_recent_transactions
from ..agents.workflow_agents import AmlInvestigationWorkflowAgent


def build_aml_office_router() -> LlmAgent:
    aml_investigator = LlmAgent(
        after_model_callback=sanitize_tool_call_names,
        name="aml_investigator",
        model=build_model("aml_investigator"),
        description="Analyzes customer transactions for structuring, threshold anomalies, mule-ring patterns, and identity verification; also looks up and triages existing AML alerts.",
        instruction=(
            "You are an AML Investigator. Use your tools to analyze the requested entity, or to "
            "look up or triage an existing AML alert by id (open -> in-investigation -> "
            "cleared/escalated-to-sar). "
            "Return a compact JSON string with keys investigation_status, findings, risk_score, "
            "and case_facts. case_facts must contain names, amounts, dates, and red_flags as arrays."
        ),
        tools=[
            detect_structuring,
            verify_identity_document,
            check_threshold_anomaly,
            find_mule_rings_for_customer,
            list_recent_transactions,
            get_customer_context,
            get_aml_alert,
            list_aml_alerts,
            transition_aml_alert_status,
        ],
        output_key="aml_investigation_summary",
    )

    sar_drafting_agent = LlmAgent(
        after_model_callback=sanitize_tool_call_names,
        name="sar_drafting_agent",
        model=build_model("sar_drafting_agent"),
        description="Drafts a Suspicious Activity Report (SAR) based on AML investigation findings.",
        instruction=(
            "You are a SAR drafting agent. "
            "Read the investigation summary from {aml_investigation_summary} "
            "and the compiled case facts from {aml_sar_case_facts}. "
            "Use the supplied names, amounts, dates, and red flags when drafting the SAR. "
            "Do not invent missing case facts. "
            "Return a compact JSON string with keys sar_required, sar_draft, and next_steps."
        ),
        tools=[],
        output_key="aml_sar_draft",
    )

    aml_workflow_agent = AmlInvestigationWorkflowAgent(
        name="aml_investigation_workflow",
        investigator_agent=aml_investigator,
        reporter_agent=sar_drafting_agent,
    )

    return LlmAgent(
        after_model_callback=sanitize_tool_call_names,
        name="aml_office_router",
        model=build_model("aml_office_router"),
        description="Routes compliance, fraud, suspicious activity, identity-verification, and AML alert-triage requests into the AML investigation workflow.",
        instruction="Use aml_investigation_workflow for investigations regarding money laundering, sanctions checks, suspicious transactions, identity-document verification (e.g. a submitted name/DOB/ID number against an on-file reference), and for looking up or triaging an existing AML alert by id.",
        sub_agents=[aml_workflow_agent],
        output_key="aml_office_router_result",
    )
