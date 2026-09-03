"""Front/mid/back office domain membership -- which agents belong to which
banking domain. Lives here (not in mantis.core.registry) so shared MANTIS
infrastructure has no hardcoded banking branches; mantis.core.registry only
imports and registers this data, it doesn't define it.
"""

DOMAIN_AGENTS: dict[str, list[str]] = {
    "front_office": [
        "transaction_monitoring_agent", "fraud_detection_agent", "compliance_agent",
        "decision_making_agent", "front_office_transaction_workflow", "knowledge_base_agent",
        "transaction_processing_agent", "customer_service_agent", "chatbot_intent_agent",
        "customer_service_chatbot_workflow", "front_office_router",
    ],
    "mid_office": [
        "data_analysis_agent", "forecasting_agent", "staff_scheduling_agent", "validation_agent",
        "support_guidance_agent", "planning_summary_agent", "financial_data_agent",
        "recommender_agent", "loan_agent", "risk_compliance_agent", "representative_merge_agent",
        "mid_office_router",
    ],
    "back_office": [
        "validation_checkpoint_agent", "eod_processing_agent", "ledger_update_agent",
        "reconciliation_agent", "report_writing_agent", "exception_agent",
        "back_office_eod_workflow", "back_office_router",
    ],
}
