"""Generated PEP adapters. Regenerate rather than editing this file."""
from __future__ import annotations
import inspect
from typing import Any, Callable

from zt_pep.runtime import PEPEnforcer

def protect(enforcer: PEPEnforcer, placement_id: str, operation: Callable[..., Any]) -> Callable[..., Any]:
    return enforcer.wrap_async(placement_id, operation) if inspect.iscoroutinefunction(operation) else enforcer.wrap_sync(placement_id, operation)

def protect_pep_tool_compliance_agent_get_customer_context(enforcer: PEPEnforcer, operation: Callable[..., Any]) -> Callable[..., Any]:
    return protect(enforcer, 'pep.tool.compliance_agent__get_customer_context', operation)

def protect_pep_tool_compliance_agent_get_transaction_context(enforcer: PEPEnforcer, operation: Callable[..., Any]) -> Callable[..., Any]:
    return protect(enforcer, 'pep.tool.compliance_agent__get_transaction_context', operation)

def protect_pep_tool_compliance_agent_search_policies(enforcer: PEPEnforcer, operation: Callable[..., Any]) -> Callable[..., Any]:
    return protect(enforcer, 'pep.tool.compliance_agent__search_policies', operation)

def protect_pep_tool_data_analysis_agent_get_operations_snapshot(enforcer: PEPEnforcer, operation: Callable[..., Any]) -> Callable[..., Any]:
    return protect(enforcer, 'pep.tool.data_analysis_agent__get_operations_snapshot', operation)

def protect_pep_tool_decision_making_agent_submit_manual_review(enforcer: PEPEnforcer, operation: Callable[..., Any]) -> Callable[..., Any]:
    return protect(enforcer, 'pep.tool.decision_making_agent__submit_manual_review', operation)

def protect_pep_tool_dispute_resolution_agent_file_dispute(enforcer: PEPEnforcer, operation: Callable[..., Any]) -> Callable[..., Any]:
    return protect(enforcer, 'pep.tool.dispute_resolution_agent__file_dispute', operation)

def protect_pep_tool_dispute_resolution_agent_get_dispute_status(enforcer: PEPEnforcer, operation: Callable[..., Any]) -> Callable[..., Any]:
    return protect(enforcer, 'pep.tool.dispute_resolution_agent__get_dispute_status', operation)

def protect_pep_tool_eod_processing_agent_get_eod_batch(enforcer: PEPEnforcer, operation: Callable[..., Any]) -> Callable[..., Any]:
    return protect(enforcer, 'pep.tool.eod_processing_agent__get_eod_batch', operation)

def protect_pep_tool_exception_agent_create_exception_case(enforcer: PEPEnforcer, operation: Callable[..., Any]) -> Callable[..., Any]:
    return protect(enforcer, 'pep.tool.exception_agent__create_exception_case', operation)

def protect_pep_tool_financial_data_agent_get_customer_financial_profile(enforcer: PEPEnforcer, operation: Callable[..., Any]) -> Callable[..., Any]:
    return protect(enforcer, 'pep.tool.financial_data_agent__get_customer_financial_profile', operation)

def protect_pep_tool_forecasting_agent_get_operations_snapshot(enforcer: PEPEnforcer, operation: Callable[..., Any]) -> Callable[..., Any]:
    return protect(enforcer, 'pep.tool.forecasting_agent__get_operations_snapshot', operation)

def protect_pep_tool_fraud_detection_agent_get_customer_context(enforcer: PEPEnforcer, operation: Callable[..., Any]) -> Callable[..., Any]:
    return protect(enforcer, 'pep.tool.fraud_detection_agent__get_customer_context', operation)

def protect_pep_tool_fraud_detection_agent_get_transaction_context(enforcer: PEPEnforcer, operation: Callable[..., Any]) -> Callable[..., Any]:
    return protect(enforcer, 'pep.tool.fraud_detection_agent__get_transaction_context', operation)

def protect_pep_tool_fraud_detection_agent_list_recent_transactions(enforcer: PEPEnforcer, operation: Callable[..., Any]) -> Callable[..., Any]:
    return protect(enforcer, 'pep.tool.fraud_detection_agent__list_recent_transactions', operation)

def protect_pep_tool_knowledge_base_agent_search_faqs(enforcer: PEPEnforcer, operation: Callable[..., Any]) -> Callable[..., Any]:
    return protect(enforcer, 'pep.tool.knowledge_base_agent__search_faqs', operation)

def protect_pep_tool_ledger_update_agent_apply_ledger_updates(enforcer: PEPEnforcer, operation: Callable[..., Any]) -> Callable[..., Any]:
    return protect(enforcer, 'pep.tool.ledger_update_agent__apply_ledger_updates', operation)

def protect_pep_tool_loan_agent_search_loan_playbooks(enforcer: PEPEnforcer, operation: Callable[..., Any]) -> Callable[..., Any]:
    return protect(enforcer, 'pep.tool.loan_agent__search_loan_playbooks', operation)

def protect_pep_tool_loan_preapproval_agent_get_loan_application_status(enforcer: PEPEnforcer, operation: Callable[..., Any]) -> Callable[..., Any]:
    return protect(enforcer, 'pep.tool.loan_preapproval_agent__get_loan_application_status', operation)

def protect_pep_tool_loan_preapproval_agent_submit_loan_application(enforcer: PEPEnforcer, operation: Callable[..., Any]) -> Callable[..., Any]:
    return protect(enforcer, 'pep.tool.loan_preapproval_agent__submit_loan_application', operation)

def protect_pep_tool_recommender_agent_search_product_catalog(enforcer: PEPEnforcer, operation: Callable[..., Any]) -> Callable[..., Any]:
    return protect(enforcer, 'pep.tool.recommender_agent__search_product_catalog', operation)

def protect_pep_tool_reconciliation_agent_get_reconciliation_data(enforcer: PEPEnforcer, operation: Callable[..., Any]) -> Callable[..., Any]:
    return protect(enforcer, 'pep.tool.reconciliation_agent__get_reconciliation_data', operation)

def protect_pep_tool_report_writing_agent_store_report(enforcer: PEPEnforcer, operation: Callable[..., Any]) -> Callable[..., Any]:
    return protect(enforcer, 'pep.tool.report_writing_agent__store_report', operation)

def protect_pep_tool_risk_compliance_agent_search_policies(enforcer: PEPEnforcer, operation: Callable[..., Any]) -> Callable[..., Any]:
    return protect(enforcer, 'pep.tool.risk_compliance_agent__search_policies', operation)

def protect_pep_tool_sar_escalation_agent_file_sar_report(enforcer: PEPEnforcer, operation: Callable[..., Any]) -> Callable[..., Any]:
    return protect(enforcer, 'pep.tool.sar_escalation_agent__file_sar_report', operation)

def protect_pep_tool_sar_escalation_agent_get_exception_case(enforcer: PEPEnforcer, operation: Callable[..., Any]) -> Callable[..., Any]:
    return protect(enforcer, 'pep.tool.sar_escalation_agent__get_exception_case', operation)

def protect_pep_tool_sar_escalation_agent_get_sar_status(enforcer: PEPEnforcer, operation: Callable[..., Any]) -> Callable[..., Any]:
    return protect(enforcer, 'pep.tool.sar_escalation_agent__get_sar_status', operation)

def protect_pep_tool_support_guidance_agent_get_support_playbooks(enforcer: PEPEnforcer, operation: Callable[..., Any]) -> Callable[..., Any]:
    return protect(enforcer, 'pep.tool.support_guidance_agent__get_support_playbooks', operation)

def protect_pep_tool_transaction_monitoring_agent_get_customer_context(enforcer: PEPEnforcer, operation: Callable[..., Any]) -> Callable[..., Any]:
    return protect(enforcer, 'pep.tool.transaction_monitoring_agent__get_customer_context', operation)

def protect_pep_tool_transaction_monitoring_agent_get_transaction_context(enforcer: PEPEnforcer, operation: Callable[..., Any]) -> Callable[..., Any]:
    return protect(enforcer, 'pep.tool.transaction_monitoring_agent__get_transaction_context', operation)

def protect_pep_tool_transaction_monitoring_agent_list_recent_transactions(enforcer: PEPEnforcer, operation: Callable[..., Any]) -> Callable[..., Any]:
    return protect(enforcer, 'pep.tool.transaction_monitoring_agent__list_recent_transactions', operation)

def protect_pep_tool_transaction_processing_agent_execute_transfer(enforcer: PEPEnforcer, operation: Callable[..., Any]) -> Callable[..., Any]:
    return protect(enforcer, 'pep.tool.transaction_processing_agent__execute_transfer', operation)

def protect_pep_tool_user_proxy_agent_get_branch_workload(enforcer: PEPEnforcer, operation: Callable[..., Any]) -> Callable[..., Any]:
    return protect(enforcer, 'pep.tool.user_proxy_agent__get_branch_workload', operation)

def protect_pep_tool_user_proxy_agent_get_customer_product_affinity(enforcer: PEPEnforcer, operation: Callable[..., Any]) -> Callable[..., Any]:
    return protect(enforcer, 'pep.tool.user_proxy_agent__get_customer_product_affinity', operation)

def protect_pep_tool_user_proxy_agent_get_reconciliation_mismatches(enforcer: PEPEnforcer, operation: Callable[..., Any]) -> Callable[..., Any]:
    return protect(enforcer, 'pep.tool.user_proxy_agent__get_reconciliation_mismatches', operation)

def protect_pep_tool_user_proxy_agent_get_transaction(enforcer: PEPEnforcer, operation: Callable[..., Any]) -> Callable[..., Any]:
    return protect(enforcer, 'pep.tool.user_proxy_agent__get_transaction', operation)

def protect_pep_tool_user_proxy_agent_propose_staffing_adjustment(enforcer: PEPEnforcer, operation: Callable[..., Any]) -> Callable[..., Any]:
    return protect(enforcer, 'pep.tool.user_proxy_agent__propose_staffing_adjustment', operation)

def protect_pep_tool_user_proxy_agent_resolve_ledger_entry(enforcer: PEPEnforcer, operation: Callable[..., Any]) -> Callable[..., Any]:
    return protect(enforcer, 'pep.tool.user_proxy_agent__resolve_ledger_entry', operation)

def protect_pep_tool_user_proxy_agent_run_fraud_and_compliance_workflow(enforcer: PEPEnforcer, operation: Callable[..., Any]) -> Callable[..., Any]:
    return protect(enforcer, 'pep.tool.user_proxy_agent__run_fraud_and_compliance_workflow', operation)

def protect_pep_tool_user_proxy_agent_trigger_eod_reconciliation(enforcer: PEPEnforcer, operation: Callable[..., Any]) -> Callable[..., Any]:
    return protect(enforcer, 'pep.tool.user_proxy_agent__trigger_eod_reconciliation', operation)

def protect_pep_tool_user_proxy_agent_update_transaction_status(enforcer: PEPEnforcer, operation: Callable[..., Any]) -> Callable[..., Any]:
    return protect(enforcer, 'pep.tool.user_proxy_agent__update_transaction_status', operation)

def protect_pep_tool_validation_agent_persist_validated_schedule(enforcer: PEPEnforcer, operation: Callable[..., Any]) -> Callable[..., Any]:
    return protect(enforcer, 'pep.tool.validation_agent__persist_validated_schedule', operation)

def protect_pep_tool_validation_checkpoint_agent_validate_eod_readiness(enforcer: PEPEnforcer, operation: Callable[..., Any]) -> Callable[..., Any]:
    return protect(enforcer, 'pep.tool.validation_checkpoint_agent__validate_eod_readiness', operation)
