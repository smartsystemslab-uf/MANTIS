"""Generated PEP adapters. Regenerate rather than editing this file."""
from __future__ import annotations
import inspect
from typing import Any, Callable

from zt_pep.runtime import PEPEnforcer

class AgentRoutePEPMiddleware:
    def __init__(self, app: Any, enforcer: PEPEnforcer, placement_resolver: Callable[[Any], str | None]):
        self.app = app
        self.enforcer = enforcer
        self.placement_resolver = placement_resolver

    async def __call__(self, scope: Any, receive: Any, send: Any) -> None:
        placement_id = self.placement_resolver(scope)
        if placement_id:
            decision, _ = self.enforcer.authorize(placement_id, parameters={"route": scope.get("path")})
            if decision.get("decision") not in {"ALLOW", "ALLOW_WITH_OBLIGATIONS"}:
                raise PermissionError(f"agent route blocked by {placement_id}")
        await self.app(scope, receive, send)

def protect_pep_entry_ingress_aml_office_router(enforcer: PEPEnforcer, operation: Callable[..., Any]) -> Callable[..., Any]:
    return protect(enforcer, 'pep.entry.ingress__aml_office_router', operation)

def protect_pep_entry_ingress_back_office_router(enforcer: PEPEnforcer, operation: Callable[..., Any]) -> Callable[..., Any]:
    return protect(enforcer, 'pep.entry.ingress__back_office_router', operation)

def protect_pep_entry_ingress_dispute_resolution_agent(enforcer: PEPEnforcer, operation: Callable[..., Any]) -> Callable[..., Any]:
    return protect(enforcer, 'pep.entry.ingress__dispute_resolution_agent', operation)

def protect_pep_entry_ingress_front_office_router(enforcer: PEPEnforcer, operation: Callable[..., Any]) -> Callable[..., Any]:
    return protect(enforcer, 'pep.entry.ingress__front_office_router', operation)

def protect_pep_entry_ingress_loan_preapproval_agent(enforcer: PEPEnforcer, operation: Callable[..., Any]) -> Callable[..., Any]:
    return protect(enforcer, 'pep.entry.ingress__loan_preapproval_agent', operation)

def protect_pep_entry_ingress_mid_office_router(enforcer: PEPEnforcer, operation: Callable[..., Any]) -> Callable[..., Any]:
    return protect(enforcer, 'pep.entry.ingress__mid_office_router', operation)

def protect_pep_entry_ingress_sar_escalation_agent(enforcer: PEPEnforcer, operation: Callable[..., Any]) -> Callable[..., Any]:
    return protect(enforcer, 'pep.entry.ingress__sar_escalation_agent', operation)

def protect_pep_entry_ingress_user_proxy_agent(enforcer: PEPEnforcer, operation: Callable[..., Any]) -> Callable[..., Any]:
    return protect(enforcer, 'pep.entry.ingress__user_proxy_agent', operation)

def protect_pep_orchestrate_aml_investigation_workflow_aml_investigator(enforcer: PEPEnforcer, operation: Callable[..., Any]) -> Callable[..., Any]:
    return protect(enforcer, 'pep.orchestrate.aml_investigation_workflow__aml_investigator', operation)

def protect_pep_orchestrate_aml_investigation_workflow_sar_drafting_agent(enforcer: PEPEnforcer, operation: Callable[..., Any]) -> Callable[..., Any]:
    return protect(enforcer, 'pep.orchestrate.aml_investigation_workflow__sar_drafting_agent', operation)

def protect_pep_orchestrate_back_office_eod_workflow_eod_processing_agent(enforcer: PEPEnforcer, operation: Callable[..., Any]) -> Callable[..., Any]:
    return protect(enforcer, 'pep.orchestrate.back_office_eod_workflow__eod_processing_agent', operation)

def protect_pep_orchestrate_back_office_eod_workflow_exception_agent(enforcer: PEPEnforcer, operation: Callable[..., Any]) -> Callable[..., Any]:
    return protect(enforcer, 'pep.orchestrate.back_office_eod_workflow__exception_agent', operation)

def protect_pep_orchestrate_back_office_eod_workflow_ledger_update_agent(enforcer: PEPEnforcer, operation: Callable[..., Any]) -> Callable[..., Any]:
    return protect(enforcer, 'pep.orchestrate.back_office_eod_workflow__ledger_update_agent', operation)

def protect_pep_orchestrate_back_office_eod_workflow_reconciliation_agent(enforcer: PEPEnforcer, operation: Callable[..., Any]) -> Callable[..., Any]:
    return protect(enforcer, 'pep.orchestrate.back_office_eod_workflow__reconciliation_agent', operation)

def protect_pep_orchestrate_back_office_eod_workflow_report_writing_agent(enforcer: PEPEnforcer, operation: Callable[..., Any]) -> Callable[..., Any]:
    return protect(enforcer, 'pep.orchestrate.back_office_eod_workflow__report_writing_agent', operation)

def protect_pep_orchestrate_back_office_eod_workflow_validation_checkpoint_agent(enforcer: PEPEnforcer, operation: Callable[..., Any]) -> Callable[..., Any]:
    return protect(enforcer, 'pep.orchestrate.back_office_eod_workflow__validation_checkpoint_agent', operation)

def protect_pep_orchestrate_customer_service_chatbot_workflow_chatbot_intent_agent(enforcer: PEPEnforcer, operation: Callable[..., Any]) -> Callable[..., Any]:
    return protect(enforcer, 'pep.orchestrate.customer_service_chatbot_workflow__chatbot_intent_agent', operation)

def protect_pep_orchestrate_customer_service_chatbot_workflow_customer_service_agent(enforcer: PEPEnforcer, operation: Callable[..., Any]) -> Callable[..., Any]:
    return protect(enforcer, 'pep.orchestrate.customer_service_chatbot_workflow__customer_service_agent', operation)

def protect_pep_orchestrate_customer_service_chatbot_workflow_knowledge_base_agent(enforcer: PEPEnforcer, operation: Callable[..., Any]) -> Callable[..., Any]:
    return protect(enforcer, 'pep.orchestrate.customer_service_chatbot_workflow__knowledge_base_agent', operation)

def protect_pep_orchestrate_customer_service_chatbot_workflow_transaction_processing_agent(enforcer: PEPEnforcer, operation: Callable[..., Any]) -> Callable[..., Any]:
    return protect(enforcer, 'pep.orchestrate.customer_service_chatbot_workflow__transaction_processing_agent', operation)

def protect_pep_orchestrate_front_office_transaction_workflow_compliance_agent(enforcer: PEPEnforcer, operation: Callable[..., Any]) -> Callable[..., Any]:
    return protect(enforcer, 'pep.orchestrate.front_office_transaction_workflow__compliance_agent', operation)

def protect_pep_orchestrate_front_office_transaction_workflow_decision_making_agent(enforcer: PEPEnforcer, operation: Callable[..., Any]) -> Callable[..., Any]:
    return protect(enforcer, 'pep.orchestrate.front_office_transaction_workflow__decision_making_agent', operation)

def protect_pep_orchestrate_front_office_transaction_workflow_fraud_detection_agent(enforcer: PEPEnforcer, operation: Callable[..., Any]) -> Callable[..., Any]:
    return protect(enforcer, 'pep.orchestrate.front_office_transaction_workflow__fraud_detection_agent', operation)

def protect_pep_orchestrate_front_office_transaction_workflow_transaction_monitoring_agent(enforcer: PEPEnforcer, operation: Callable[..., Any]) -> Callable[..., Any]:
    return protect(enforcer, 'pep.orchestrate.front_office_transaction_workflow__transaction_monitoring_agent', operation)

def protect_pep_orchestrate_mid_office_planning_parallel_support_guidance_agent(enforcer: PEPEnforcer, operation: Callable[..., Any]) -> Callable[..., Any]:
    return protect(enforcer, 'pep.orchestrate.mid_office_planning_parallel__support_guidance_agent', operation)

def protect_pep_orchestrate_mid_office_planning_parallel_validation_agent(enforcer: PEPEnforcer, operation: Callable[..., Any]) -> Callable[..., Any]:
    return protect(enforcer, 'pep.orchestrate.mid_office_planning_parallel__validation_agent', operation)

def protect_pep_orchestrate_mid_office_planning_workflow_data_analysis_agent(enforcer: PEPEnforcer, operation: Callable[..., Any]) -> Callable[..., Any]:
    return protect(enforcer, 'pep.orchestrate.mid_office_planning_workflow__data_analysis_agent', operation)

def protect_pep_orchestrate_mid_office_planning_workflow_forecasting_agent(enforcer: PEPEnforcer, operation: Callable[..., Any]) -> Callable[..., Any]:
    return protect(enforcer, 'pep.orchestrate.mid_office_planning_workflow__forecasting_agent', operation)

def protect_pep_orchestrate_mid_office_planning_workflow_mid_office_planning_parallel(enforcer: PEPEnforcer, operation: Callable[..., Any]) -> Callable[..., Any]:
    return protect(enforcer, 'pep.orchestrate.mid_office_planning_workflow__mid_office_planning_parallel', operation)

def protect_pep_orchestrate_mid_office_planning_workflow_planning_summary_agent(enforcer: PEPEnforcer, operation: Callable[..., Any]) -> Callable[..., Any]:
    return protect(enforcer, 'pep.orchestrate.mid_office_planning_workflow__planning_summary_agent', operation)

def protect_pep_orchestrate_mid_office_planning_workflow_staff_scheduling_agent(enforcer: PEPEnforcer, operation: Callable[..., Any]) -> Callable[..., Any]:
    return protect(enforcer, 'pep.orchestrate.mid_office_planning_workflow__staff_scheduling_agent', operation)

def protect_pep_orchestrate_representative_assist_parallel_financial_data_agent(enforcer: PEPEnforcer, operation: Callable[..., Any]) -> Callable[..., Any]:
    return protect(enforcer, 'pep.orchestrate.representative_assist_parallel__financial_data_agent', operation)

def protect_pep_orchestrate_representative_assist_parallel_loan_agent(enforcer: PEPEnforcer, operation: Callable[..., Any]) -> Callable[..., Any]:
    return protect(enforcer, 'pep.orchestrate.representative_assist_parallel__loan_agent', operation)

def protect_pep_orchestrate_representative_assist_parallel_recommender_agent(enforcer: PEPEnforcer, operation: Callable[..., Any]) -> Callable[..., Any]:
    return protect(enforcer, 'pep.orchestrate.representative_assist_parallel__recommender_agent', operation)

def protect_pep_orchestrate_representative_assist_parallel_risk_compliance_agent(enforcer: PEPEnforcer, operation: Callable[..., Any]) -> Callable[..., Any]:
    return protect(enforcer, 'pep.orchestrate.representative_assist_parallel__risk_compliance_agent', operation)

def protect_pep_orchestrate_representative_assistant_workflow_representative_assist_parallel(enforcer: PEPEnforcer, operation: Callable[..., Any]) -> Callable[..., Any]:
    return protect(enforcer, 'pep.orchestrate.representative_assistant_workflow__representative_assist_parallel', operation)

def protect_pep_orchestrate_representative_assistant_workflow_representative_merge_agent(enforcer: PEPEnforcer, operation: Callable[..., Any]) -> Callable[..., Any]:
    return protect(enforcer, 'pep.orchestrate.representative_assistant_workflow__representative_merge_agent', operation)

def protect_pep_transfer_aml_office_router_aml_investigation_workflow(enforcer: PEPEnforcer, operation: Callable[..., Any]) -> Callable[..., Any]:
    return protect(enforcer, 'pep.transfer.aml_office_router__aml_investigation_workflow', operation)

def protect_pep_transfer_aml_office_router_back_office_router(enforcer: PEPEnforcer, operation: Callable[..., Any]) -> Callable[..., Any]:
    return protect(enforcer, 'pep.transfer.aml_office_router__back_office_router', operation)

def protect_pep_transfer_aml_office_router_front_office_router(enforcer: PEPEnforcer, operation: Callable[..., Any]) -> Callable[..., Any]:
    return protect(enforcer, 'pep.transfer.aml_office_router__front_office_router', operation)

def protect_pep_transfer_aml_office_router_mid_office_router(enforcer: PEPEnforcer, operation: Callable[..., Any]) -> Callable[..., Any]:
    return protect(enforcer, 'pep.transfer.aml_office_router__mid_office_router', operation)

def protect_pep_transfer_aml_office_router_user_proxy_agent(enforcer: PEPEnforcer, operation: Callable[..., Any]) -> Callable[..., Any]:
    return protect(enforcer, 'pep.transfer.aml_office_router__user_proxy_agent', operation)

def protect_pep_transfer_back_office_router_aml_office_router(enforcer: PEPEnforcer, operation: Callable[..., Any]) -> Callable[..., Any]:
    return protect(enforcer, 'pep.transfer.back_office_router__aml_office_router', operation)

def protect_pep_transfer_back_office_router_back_office_eod_workflow(enforcer: PEPEnforcer, operation: Callable[..., Any]) -> Callable[..., Any]:
    return protect(enforcer, 'pep.transfer.back_office_router__back_office_eod_workflow', operation)

def protect_pep_transfer_back_office_router_front_office_router(enforcer: PEPEnforcer, operation: Callable[..., Any]) -> Callable[..., Any]:
    return protect(enforcer, 'pep.transfer.back_office_router__front_office_router', operation)

def protect_pep_transfer_back_office_router_mid_office_router(enforcer: PEPEnforcer, operation: Callable[..., Any]) -> Callable[..., Any]:
    return protect(enforcer, 'pep.transfer.back_office_router__mid_office_router', operation)

def protect_pep_transfer_back_office_router_sar_escalation_agent(enforcer: PEPEnforcer, operation: Callable[..., Any]) -> Callable[..., Any]:
    return protect(enforcer, 'pep.transfer.back_office_router__sar_escalation_agent', operation)

def protect_pep_transfer_back_office_router_user_proxy_agent(enforcer: PEPEnforcer, operation: Callable[..., Any]) -> Callable[..., Any]:
    return protect(enforcer, 'pep.transfer.back_office_router__user_proxy_agent', operation)

def protect_pep_transfer_dispute_resolution_agent_customer_service_chatbot_workflow(enforcer: PEPEnforcer, operation: Callable[..., Any]) -> Callable[..., Any]:
    return protect(enforcer, 'pep.transfer.dispute_resolution_agent__customer_service_chatbot_workflow', operation)

def protect_pep_transfer_dispute_resolution_agent_front_office_router(enforcer: PEPEnforcer, operation: Callable[..., Any]) -> Callable[..., Any]:
    return protect(enforcer, 'pep.transfer.dispute_resolution_agent__front_office_router', operation)

def protect_pep_transfer_dispute_resolution_agent_front_office_transaction_workflow(enforcer: PEPEnforcer, operation: Callable[..., Any]) -> Callable[..., Any]:
    return protect(enforcer, 'pep.transfer.dispute_resolution_agent__front_office_transaction_workflow', operation)

def protect_pep_transfer_front_office_router_aml_office_router(enforcer: PEPEnforcer, operation: Callable[..., Any]) -> Callable[..., Any]:
    return protect(enforcer, 'pep.transfer.front_office_router__aml_office_router', operation)

def protect_pep_transfer_front_office_router_back_office_router(enforcer: PEPEnforcer, operation: Callable[..., Any]) -> Callable[..., Any]:
    return protect(enforcer, 'pep.transfer.front_office_router__back_office_router', operation)

def protect_pep_transfer_front_office_router_customer_service_chatbot_workflow(enforcer: PEPEnforcer, operation: Callable[..., Any]) -> Callable[..., Any]:
    return protect(enforcer, 'pep.transfer.front_office_router__customer_service_chatbot_workflow', operation)

def protect_pep_transfer_front_office_router_dispute_resolution_agent(enforcer: PEPEnforcer, operation: Callable[..., Any]) -> Callable[..., Any]:
    return protect(enforcer, 'pep.transfer.front_office_router__dispute_resolution_agent', operation)

def protect_pep_transfer_front_office_router_front_office_transaction_workflow(enforcer: PEPEnforcer, operation: Callable[..., Any]) -> Callable[..., Any]:
    return protect(enforcer, 'pep.transfer.front_office_router__front_office_transaction_workflow', operation)

def protect_pep_transfer_front_office_router_mid_office_router(enforcer: PEPEnforcer, operation: Callable[..., Any]) -> Callable[..., Any]:
    return protect(enforcer, 'pep.transfer.front_office_router__mid_office_router', operation)

def protect_pep_transfer_front_office_router_user_proxy_agent(enforcer: PEPEnforcer, operation: Callable[..., Any]) -> Callable[..., Any]:
    return protect(enforcer, 'pep.transfer.front_office_router__user_proxy_agent', operation)

def protect_pep_transfer_loan_preapproval_agent_mid_office_planning_workflow(enforcer: PEPEnforcer, operation: Callable[..., Any]) -> Callable[..., Any]:
    return protect(enforcer, 'pep.transfer.loan_preapproval_agent__mid_office_planning_workflow', operation)

def protect_pep_transfer_loan_preapproval_agent_mid_office_router(enforcer: PEPEnforcer, operation: Callable[..., Any]) -> Callable[..., Any]:
    return protect(enforcer, 'pep.transfer.loan_preapproval_agent__mid_office_router', operation)

def protect_pep_transfer_loan_preapproval_agent_representative_assistant_workflow(enforcer: PEPEnforcer, operation: Callable[..., Any]) -> Callable[..., Any]:
    return protect(enforcer, 'pep.transfer.loan_preapproval_agent__representative_assistant_workflow', operation)

def protect_pep_transfer_mid_office_router_aml_office_router(enforcer: PEPEnforcer, operation: Callable[..., Any]) -> Callable[..., Any]:
    return protect(enforcer, 'pep.transfer.mid_office_router__aml_office_router', operation)

def protect_pep_transfer_mid_office_router_back_office_router(enforcer: PEPEnforcer, operation: Callable[..., Any]) -> Callable[..., Any]:
    return protect(enforcer, 'pep.transfer.mid_office_router__back_office_router', operation)

def protect_pep_transfer_mid_office_router_front_office_router(enforcer: PEPEnforcer, operation: Callable[..., Any]) -> Callable[..., Any]:
    return protect(enforcer, 'pep.transfer.mid_office_router__front_office_router', operation)

def protect_pep_transfer_mid_office_router_loan_preapproval_agent(enforcer: PEPEnforcer, operation: Callable[..., Any]) -> Callable[..., Any]:
    return protect(enforcer, 'pep.transfer.mid_office_router__loan_preapproval_agent', operation)

def protect_pep_transfer_mid_office_router_mid_office_planning_workflow(enforcer: PEPEnforcer, operation: Callable[..., Any]) -> Callable[..., Any]:
    return protect(enforcer, 'pep.transfer.mid_office_router__mid_office_planning_workflow', operation)

def protect_pep_transfer_mid_office_router_representative_assistant_workflow(enforcer: PEPEnforcer, operation: Callable[..., Any]) -> Callable[..., Any]:
    return protect(enforcer, 'pep.transfer.mid_office_router__representative_assistant_workflow', operation)

def protect_pep_transfer_mid_office_router_user_proxy_agent(enforcer: PEPEnforcer, operation: Callable[..., Any]) -> Callable[..., Any]:
    return protect(enforcer, 'pep.transfer.mid_office_router__user_proxy_agent', operation)

def protect_pep_transfer_sar_escalation_agent_back_office_eod_workflow(enforcer: PEPEnforcer, operation: Callable[..., Any]) -> Callable[..., Any]:
    return protect(enforcer, 'pep.transfer.sar_escalation_agent__back_office_eod_workflow', operation)

def protect_pep_transfer_sar_escalation_agent_back_office_router(enforcer: PEPEnforcer, operation: Callable[..., Any]) -> Callable[..., Any]:
    return protect(enforcer, 'pep.transfer.sar_escalation_agent__back_office_router', operation)

def protect_pep_transfer_user_proxy_agent_aml_office_router(enforcer: PEPEnforcer, operation: Callable[..., Any]) -> Callable[..., Any]:
    return protect(enforcer, 'pep.transfer.user_proxy_agent__aml_office_router', operation)

def protect_pep_transfer_user_proxy_agent_back_office_router(enforcer: PEPEnforcer, operation: Callable[..., Any]) -> Callable[..., Any]:
    return protect(enforcer, 'pep.transfer.user_proxy_agent__back_office_router', operation)

def protect_pep_transfer_user_proxy_agent_front_office_router(enforcer: PEPEnforcer, operation: Callable[..., Any]) -> Callable[..., Any]:
    return protect(enforcer, 'pep.transfer.user_proxy_agent__front_office_router', operation)

def protect_pep_transfer_user_proxy_agent_mid_office_router(enforcer: PEPEnforcer, operation: Callable[..., Any]) -> Callable[..., Any]:
    return protect(enforcer, 'pep.transfer.user_proxy_agent__mid_office_router', operation)
