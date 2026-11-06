"""Generated PEP adapters. Regenerate rather than editing this file."""
from __future__ import annotations
import inspect
from typing import Any, Callable

from zt_pep.runtime import PEPEnforcer

def protect(enforcer: PEPEnforcer, placement_id: str, operation: Callable[..., Any]) -> Callable[..., Any]:
    return enforcer.wrap_async(placement_id, operation) if inspect.iscoroutinefunction(operation) else enforcer.wrap_sync(placement_id, operation)

def protect_pep_input_ingress(enforcer: PEPEnforcer, operation: Callable[..., Any]) -> Callable[..., Any]:
    return protect(enforcer, 'pep.input.ingress', operation)

def protect_pep_output_aml_investigation_workflow(enforcer: PEPEnforcer, operation: Callable[..., Any]) -> Callable[..., Any]:
    return protect(enforcer, 'pep.output.aml_investigation_workflow', operation)

def protect_pep_output_aml_investigator(enforcer: PEPEnforcer, operation: Callable[..., Any]) -> Callable[..., Any]:
    return protect(enforcer, 'pep.output.aml_investigator', operation)

def protect_pep_output_aml_office_router(enforcer: PEPEnforcer, operation: Callable[..., Any]) -> Callable[..., Any]:
    return protect(enforcer, 'pep.output.aml_office_router', operation)

def protect_pep_output_back_office_eod_workflow(enforcer: PEPEnforcer, operation: Callable[..., Any]) -> Callable[..., Any]:
    return protect(enforcer, 'pep.output.back_office_eod_workflow', operation)

def protect_pep_output_back_office_router(enforcer: PEPEnforcer, operation: Callable[..., Any]) -> Callable[..., Any]:
    return protect(enforcer, 'pep.output.back_office_router', operation)

def protect_pep_output_chatbot_intent_agent(enforcer: PEPEnforcer, operation: Callable[..., Any]) -> Callable[..., Any]:
    return protect(enforcer, 'pep.output.chatbot_intent_agent', operation)

def protect_pep_output_compliance_agent(enforcer: PEPEnforcer, operation: Callable[..., Any]) -> Callable[..., Any]:
    return protect(enforcer, 'pep.output.compliance_agent', operation)

def protect_pep_output_customer_service_agent(enforcer: PEPEnforcer, operation: Callable[..., Any]) -> Callable[..., Any]:
    return protect(enforcer, 'pep.output.customer_service_agent', operation)

def protect_pep_output_customer_service_chatbot_workflow(enforcer: PEPEnforcer, operation: Callable[..., Any]) -> Callable[..., Any]:
    return protect(enforcer, 'pep.output.customer_service_chatbot_workflow', operation)

def protect_pep_output_data_analysis_agent(enforcer: PEPEnforcer, operation: Callable[..., Any]) -> Callable[..., Any]:
    return protect(enforcer, 'pep.output.data_analysis_agent', operation)

def protect_pep_output_decision_making_agent(enforcer: PEPEnforcer, operation: Callable[..., Any]) -> Callable[..., Any]:
    return protect(enforcer, 'pep.output.decision_making_agent', operation)

def protect_pep_output_dispute_resolution_agent(enforcer: PEPEnforcer, operation: Callable[..., Any]) -> Callable[..., Any]:
    return protect(enforcer, 'pep.output.dispute_resolution_agent', operation)

def protect_pep_output_eod_processing_agent(enforcer: PEPEnforcer, operation: Callable[..., Any]) -> Callable[..., Any]:
    return protect(enforcer, 'pep.output.eod_processing_agent', operation)

def protect_pep_output_exception_agent(enforcer: PEPEnforcer, operation: Callable[..., Any]) -> Callable[..., Any]:
    return protect(enforcer, 'pep.output.exception_agent', operation)

def protect_pep_output_financial_data_agent(enforcer: PEPEnforcer, operation: Callable[..., Any]) -> Callable[..., Any]:
    return protect(enforcer, 'pep.output.financial_data_agent', operation)

def protect_pep_output_forecasting_agent(enforcer: PEPEnforcer, operation: Callable[..., Any]) -> Callable[..., Any]:
    return protect(enforcer, 'pep.output.forecasting_agent', operation)

def protect_pep_output_fraud_detection_agent(enforcer: PEPEnforcer, operation: Callable[..., Any]) -> Callable[..., Any]:
    return protect(enforcer, 'pep.output.fraud_detection_agent', operation)

def protect_pep_output_front_office_router(enforcer: PEPEnforcer, operation: Callable[..., Any]) -> Callable[..., Any]:
    return protect(enforcer, 'pep.output.front_office_router', operation)

def protect_pep_output_front_office_transaction_workflow(enforcer: PEPEnforcer, operation: Callable[..., Any]) -> Callable[..., Any]:
    return protect(enforcer, 'pep.output.front_office_transaction_workflow', operation)

def protect_pep_output_knowledge_base_agent(enforcer: PEPEnforcer, operation: Callable[..., Any]) -> Callable[..., Any]:
    return protect(enforcer, 'pep.output.knowledge_base_agent', operation)

def protect_pep_output_ledger_update_agent(enforcer: PEPEnforcer, operation: Callable[..., Any]) -> Callable[..., Any]:
    return protect(enforcer, 'pep.output.ledger_update_agent', operation)

def protect_pep_output_loan_agent(enforcer: PEPEnforcer, operation: Callable[..., Any]) -> Callable[..., Any]:
    return protect(enforcer, 'pep.output.loan_agent', operation)

def protect_pep_output_loan_preapproval_agent(enforcer: PEPEnforcer, operation: Callable[..., Any]) -> Callable[..., Any]:
    return protect(enforcer, 'pep.output.loan_preapproval_agent', operation)

def protect_pep_output_mid_office_router(enforcer: PEPEnforcer, operation: Callable[..., Any]) -> Callable[..., Any]:
    return protect(enforcer, 'pep.output.mid_office_router', operation)

def protect_pep_output_planning_summary_agent(enforcer: PEPEnforcer, operation: Callable[..., Any]) -> Callable[..., Any]:
    return protect(enforcer, 'pep.output.planning_summary_agent', operation)

def protect_pep_output_recommender_agent(enforcer: PEPEnforcer, operation: Callable[..., Any]) -> Callable[..., Any]:
    return protect(enforcer, 'pep.output.recommender_agent', operation)

def protect_pep_output_reconciliation_agent(enforcer: PEPEnforcer, operation: Callable[..., Any]) -> Callable[..., Any]:
    return protect(enforcer, 'pep.output.reconciliation_agent', operation)

def protect_pep_output_report_writing_agent(enforcer: PEPEnforcer, operation: Callable[..., Any]) -> Callable[..., Any]:
    return protect(enforcer, 'pep.output.report_writing_agent', operation)

def protect_pep_output_representative_merge_agent(enforcer: PEPEnforcer, operation: Callable[..., Any]) -> Callable[..., Any]:
    return protect(enforcer, 'pep.output.representative_merge_agent', operation)

def protect_pep_output_risk_compliance_agent(enforcer: PEPEnforcer, operation: Callable[..., Any]) -> Callable[..., Any]:
    return protect(enforcer, 'pep.output.risk_compliance_agent', operation)

def protect_pep_output_sar_drafting_agent(enforcer: PEPEnforcer, operation: Callable[..., Any]) -> Callable[..., Any]:
    return protect(enforcer, 'pep.output.sar_drafting_agent', operation)

def protect_pep_output_sar_escalation_agent(enforcer: PEPEnforcer, operation: Callable[..., Any]) -> Callable[..., Any]:
    return protect(enforcer, 'pep.output.sar_escalation_agent', operation)

def protect_pep_output_staff_scheduling_agent(enforcer: PEPEnforcer, operation: Callable[..., Any]) -> Callable[..., Any]:
    return protect(enforcer, 'pep.output.staff_scheduling_agent', operation)

def protect_pep_output_support_guidance_agent(enforcer: PEPEnforcer, operation: Callable[..., Any]) -> Callable[..., Any]:
    return protect(enforcer, 'pep.output.support_guidance_agent', operation)

def protect_pep_output_transaction_monitoring_agent(enforcer: PEPEnforcer, operation: Callable[..., Any]) -> Callable[..., Any]:
    return protect(enforcer, 'pep.output.transaction_monitoring_agent', operation)

def protect_pep_output_transaction_processing_agent(enforcer: PEPEnforcer, operation: Callable[..., Any]) -> Callable[..., Any]:
    return protect(enforcer, 'pep.output.transaction_processing_agent', operation)

def protect_pep_output_user_proxy_agent(enforcer: PEPEnforcer, operation: Callable[..., Any]) -> Callable[..., Any]:
    return protect(enforcer, 'pep.output.user_proxy_agent', operation)

def protect_pep_output_validation_agent(enforcer: PEPEnforcer, operation: Callable[..., Any]) -> Callable[..., Any]:
    return protect(enforcer, 'pep.output.validation_agent', operation)

def protect_pep_output_validation_checkpoint_agent(enforcer: PEPEnforcer, operation: Callable[..., Any]) -> Callable[..., Any]:
    return protect(enforcer, 'pep.output.validation_checkpoint_agent', operation)
