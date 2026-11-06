# Protection report: citi_banking_adk

* root agent: `user_proxy_agent`; google-adk 2.7.1
* fingerprint: `aa6988806ff5c1ad9c773f183409f770fe47902ea80c7a730275c7cfdda6e951`
* agents: 43; tools: 51; edges: 164
* PEP placements: 165 logical, 5 physical
* policy version: `6281306f9d4d7f52`; policy sets: zt_adk.access, zt_adk.content.agent_message, zt_adk.content.input, zt_adk.content.model_request, zt_adk.content.output, zt_adk.content.tool_result, zt_adk.core, zt_adk.gateway.runtime, zt_adk.gateway.runtime.operation, zt_adk.gateway.runtime.participation, zt_adk.identity, zt_adk.workflow

## Agents

| agent | kind | domain | parent | workflow |
|---|---|---|---|---|
| aml_investigation_workflow | custom | aml_office_router | aml_office_router |  |
| aml_investigator | llm | aml_office_router | aml_investigation_workflow | aml_investigation_workflow |
| aml_office_router | llm | aml_office_router | user_proxy_agent |  |
| back_office_eod_workflow | custom | back_office_router | back_office_router |  |
| back_office_router | llm | back_office_router | user_proxy_agent |  |
| chatbot_intent_agent | llm | front_office_router | customer_service_chatbot_workflow | customer_service_chatbot_workflow |
| compliance_agent | llm | front_office_router | front_office_transaction_workflow | front_office_transaction_workflow |
| customer_service_agent | llm | front_office_router | customer_service_chatbot_workflow | customer_service_chatbot_workflow |
| customer_service_chatbot_workflow | custom | front_office_router | front_office_router |  |
| data_analysis_agent | llm | mid_office_router | mid_office_planning_workflow | mid_office_planning_workflow |
| decision_making_agent | llm | front_office_router | front_office_transaction_workflow | front_office_transaction_workflow |
| dispute_resolution_agent | llm | front_office_router | front_office_router |  |
| eod_processing_agent | llm | back_office_router | back_office_eod_workflow | back_office_eod_workflow |
| exception_agent | llm | back_office_router | back_office_eod_workflow | back_office_eod_workflow |
| financial_data_agent | llm | mid_office_router | representative_assist_parallel | representative_assist_parallel |
| forecasting_agent | llm | mid_office_router | mid_office_planning_workflow | mid_office_planning_workflow |
| fraud_detection_agent | llm | front_office_router | front_office_transaction_workflow | front_office_transaction_workflow |
| front_office_router | llm | front_office_router | user_proxy_agent |  |
| front_office_transaction_workflow | custom | front_office_router | front_office_router |  |
| knowledge_base_agent | llm | front_office_router | customer_service_chatbot_workflow | customer_service_chatbot_workflow |
| ledger_update_agent | llm | back_office_router | back_office_eod_workflow | back_office_eod_workflow |
| loan_agent | llm | mid_office_router | representative_assist_parallel | representative_assist_parallel |
| loan_preapproval_agent | llm | mid_office_router | mid_office_router |  |
| mid_office_planning_parallel | parallel | mid_office_router | mid_office_planning_workflow | mid_office_planning_workflow |
| mid_office_planning_workflow | sequential | mid_office_router | mid_office_router |  |
| mid_office_router | llm | mid_office_router | user_proxy_agent |  |
| planning_summary_agent | llm | mid_office_router | mid_office_planning_workflow | mid_office_planning_workflow |
| recommender_agent | llm | mid_office_router | representative_assist_parallel | representative_assist_parallel |
| reconciliation_agent | llm | back_office_router | back_office_eod_workflow | back_office_eod_workflow |
| report_writing_agent | llm | back_office_router | back_office_eod_workflow | back_office_eod_workflow |
| representative_assist_parallel | parallel | mid_office_router | representative_assistant_workflow | representative_assistant_workflow |
| representative_assistant_workflow | sequential | mid_office_router | mid_office_router |  |
| representative_merge_agent | llm | mid_office_router | representative_assistant_workflow | representative_assistant_workflow |
| risk_compliance_agent | llm | mid_office_router | representative_assist_parallel | representative_assist_parallel |
| sar_drafting_agent | llm | aml_office_router | aml_investigation_workflow | aml_investigation_workflow |
| sar_escalation_agent | llm | back_office_router | back_office_router |  |
| staff_scheduling_agent | llm | mid_office_router | mid_office_planning_workflow | mid_office_planning_workflow |
| support_guidance_agent | llm | mid_office_router | mid_office_planning_parallel | mid_office_planning_parallel |
| transaction_monitoring_agent | llm | front_office_router | front_office_transaction_workflow | front_office_transaction_workflow |
| transaction_processing_agent | llm | front_office_router | customer_service_chatbot_workflow | customer_service_chatbot_workflow |
| user_proxy_agent | llm | core |  |  |
| validation_agent | llm | mid_office_router | mid_office_planning_parallel | mid_office_planning_parallel |
| validation_checkpoint_agent | llm | back_office_router | back_office_eod_workflow | back_office_eod_workflow |

## Operations

| tool | kind | action | side effect | criticality | data | approval |
|---|---|---|---|---|---|---|
| aml_investigator/check_threshold_anomaly | function | read | False | low | confidential | no |
| aml_investigator/detect_structuring | function | write | True | high | confidential | no |
| aml_investigator/find_mule_rings_for_customer | function | read | False | low | confidential | no |
| aml_investigator/get_aml_alert | function | read | False | low | internal | no |
| aml_investigator/get_customer_context | function | read | False | low | confidential | no |
| aml_investigator/list_aml_alerts | function | read | False | low | confidential | no |
| aml_investigator/list_recent_transactions | function | read | False | low | confidential | no |
| aml_investigator/transition_aml_alert_status | function | write | True | high | internal | no |
| aml_investigator/verify_identity_document | function | read | False | low | confidential | no |
| compliance_agent/get_customer_context | function | read | False | low | confidential | no |
| compliance_agent/get_transaction_context | function | read | False | low | confidential | no |
| compliance_agent/search_policies | function | read | False | low | internal | no |
| data_analysis_agent/get_operations_snapshot | function | read | False | low | internal | no |
| decision_making_agent/submit_manual_review | function | create | True | high | internal | no |
| dispute_resolution_agent/file_dispute | function | create | True | high | confidential | no |
| dispute_resolution_agent/get_dispute_status | function | read | False | low | internal | no |
| eod_processing_agent/get_eod_batch | function | read | False | low | internal | no |
| exception_agent/create_exception_case | function | create | True | high | internal | no |
| financial_data_agent/get_customer_financial_profile | function | read | False | low | confidential | no |
| forecasting_agent/get_operations_snapshot | function | read | False | low | internal | no |
| fraud_detection_agent/get_customer_context | function | read | False | low | confidential | no |
| fraud_detection_agent/get_transaction_context | function | read | False | low | confidential | no |
| fraud_detection_agent/list_recent_transactions | function | read | False | low | confidential | no |
| knowledge_base_agent/search_faqs | function | read | False | low | confidential | no |
| ledger_update_agent/apply_ledger_updates | function | update | True | high | internal | no |
| loan_agent/search_loan_playbooks | function | read | False | low | internal | no |
| loan_preapproval_agent/get_loan_application_status | function | read | False | low | internal | no |
| loan_preapproval_agent/submit_loan_application | function | create | True | high | confidential | no |
| recommender_agent/search_product_catalog | function | read | False | low | confidential | no |
| reconciliation_agent/get_reconciliation_data | function | read | False | low | internal | no |
| report_writing_agent/store_report | function | create | True | high | internal | no |
| risk_compliance_agent/search_policies | function | read | False | low | internal | no |
| sar_escalation_agent/file_sar_report | function | create | True | high | internal | no |
| sar_escalation_agent/get_exception_case | function | read | False | low | internal | no |
| sar_escalation_agent/get_sar_status | function | read | False | low | internal | no |
| support_guidance_agent/get_support_playbooks | function | read | False | low | internal | no |
| transaction_monitoring_agent/get_customer_context | function | read | False | low | confidential | no |
| transaction_monitoring_agent/get_transaction_context | function | read | False | low | confidential | no |
| transaction_monitoring_agent/list_recent_transactions | function | read | False | low | confidential | no |
| transaction_processing_agent/execute_transfer | function | execute | True | critical | confidential | no |
| user_proxy_agent/get_branch_workload | function | read | False | low | internal | no |
| user_proxy_agent/get_customer_product_affinity | function | read | False | low | confidential | no |
| user_proxy_agent/get_reconciliation_mismatches | function | read | False | low | confidential | no |
| user_proxy_agent/get_transaction | function | read | False | low | confidential | no |
| user_proxy_agent/propose_staffing_adjustment | function | execute | True | high | confidential | no |
| user_proxy_agent/resolve_ledger_entry | function | update | True | high | confidential | no |
| user_proxy_agent/run_fraud_and_compliance_workflow | function | execute | True | critical | confidential | no |
| user_proxy_agent/trigger_eod_reconciliation | function | execute | True | critical | internal | no |
| user_proxy_agent/update_transaction_status | function | update | True | high | confidential | no |
| validation_agent/persist_validated_schedule | function | write | True | high | internal | no |
| validation_checkpoint_agent/validate_eod_readiness | function | read | False | low | internal | no |

## Routes

* entry: ingress -> user_proxy_agent
* entry: ingress -> front_office_router
* entry: ingress -> dispute_resolution_agent
* entry: ingress -> mid_office_router
* entry: ingress -> loan_preapproval_agent
* entry: ingress -> back_office_router
* entry: ingress -> sar_escalation_agent
* entry: ingress -> aml_office_router
* transfer: user_proxy_agent -> front_office_router
* transfer: user_proxy_agent -> mid_office_router
* transfer: user_proxy_agent -> back_office_router
* transfer: user_proxy_agent -> aml_office_router
* transfer: front_office_router -> front_office_transaction_workflow
* transfer: front_office_router -> customer_service_chatbot_workflow
* transfer: front_office_router -> dispute_resolution_agent
* transfer: front_office_router -> user_proxy_agent
* transfer: front_office_router -> mid_office_router
* transfer: front_office_router -> back_office_router
* transfer: front_office_router -> aml_office_router
* orchestrate: front_office_transaction_workflow -> transaction_monitoring_agent (workflow front_office_transaction_workflow)
* orchestrate: front_office_transaction_workflow -> fraud_detection_agent (workflow front_office_transaction_workflow)
* orchestrate: front_office_transaction_workflow -> compliance_agent (workflow front_office_transaction_workflow)
* orchestrate: front_office_transaction_workflow -> decision_making_agent (workflow front_office_transaction_workflow)
* orchestrate: customer_service_chatbot_workflow -> chatbot_intent_agent (workflow customer_service_chatbot_workflow)
* orchestrate: customer_service_chatbot_workflow -> knowledge_base_agent (workflow customer_service_chatbot_workflow)
* orchestrate: customer_service_chatbot_workflow -> customer_service_agent (workflow customer_service_chatbot_workflow)
* orchestrate: customer_service_chatbot_workflow -> transaction_processing_agent (workflow customer_service_chatbot_workflow)
* transfer: dispute_resolution_agent -> front_office_router
* transfer: dispute_resolution_agent -> front_office_transaction_workflow
* transfer: dispute_resolution_agent -> customer_service_chatbot_workflow
* transfer: mid_office_router -> mid_office_planning_workflow
* transfer: mid_office_router -> representative_assistant_workflow
* transfer: mid_office_router -> loan_preapproval_agent
* transfer: mid_office_router -> user_proxy_agent
* transfer: mid_office_router -> front_office_router
* transfer: mid_office_router -> back_office_router
* transfer: mid_office_router -> aml_office_router
* orchestrate: mid_office_planning_workflow -> data_analysis_agent (workflow mid_office_planning_workflow)
* orchestrate: mid_office_planning_workflow -> forecasting_agent (workflow mid_office_planning_workflow)
* orchestrate: mid_office_planning_workflow -> staff_scheduling_agent (workflow mid_office_planning_workflow)
* orchestrate: mid_office_planning_workflow -> mid_office_planning_parallel (workflow mid_office_planning_workflow)
* orchestrate: mid_office_planning_workflow -> planning_summary_agent (workflow mid_office_planning_workflow)
* orchestrate: mid_office_planning_parallel -> validation_agent (workflow mid_office_planning_parallel)
* orchestrate: mid_office_planning_parallel -> support_guidance_agent (workflow mid_office_planning_parallel)
* orchestrate: representative_assistant_workflow -> representative_assist_parallel (workflow representative_assistant_workflow)
* orchestrate: representative_assistant_workflow -> representative_merge_agent (workflow representative_assistant_workflow)
* orchestrate: representative_assist_parallel -> financial_data_agent (workflow representative_assist_parallel)
* orchestrate: representative_assist_parallel -> recommender_agent (workflow representative_assist_parallel)
* orchestrate: representative_assist_parallel -> loan_agent (workflow representative_assist_parallel)
* orchestrate: representative_assist_parallel -> risk_compliance_agent (workflow representative_assist_parallel)
* transfer: loan_preapproval_agent -> mid_office_router
* transfer: loan_preapproval_agent -> mid_office_planning_workflow
* transfer: loan_preapproval_agent -> representative_assistant_workflow
* transfer: back_office_router -> back_office_eod_workflow
* transfer: back_office_router -> sar_escalation_agent
* transfer: back_office_router -> user_proxy_agent
* transfer: back_office_router -> front_office_router
* transfer: back_office_router -> mid_office_router
* transfer: back_office_router -> aml_office_router
* orchestrate: back_office_eod_workflow -> validation_checkpoint_agent (workflow back_office_eod_workflow)
* orchestrate: back_office_eod_workflow -> eod_processing_agent (workflow back_office_eod_workflow)
* orchestrate: back_office_eod_workflow -> ledger_update_agent (workflow back_office_eod_workflow)
* orchestrate: back_office_eod_workflow -> reconciliation_agent (workflow back_office_eod_workflow)
* orchestrate: back_office_eod_workflow -> report_writing_agent (workflow back_office_eod_workflow)
* orchestrate: back_office_eod_workflow -> exception_agent (workflow back_office_eod_workflow)
* transfer: sar_escalation_agent -> back_office_router
* transfer: sar_escalation_agent -> back_office_eod_workflow
* transfer: aml_office_router -> aml_investigation_workflow
* transfer: aml_office_router -> user_proxy_agent
* transfer: aml_office_router -> front_office_router
* transfer: aml_office_router -> mid_office_router
* transfer: aml_office_router -> back_office_router
* orchestrate: aml_investigation_workflow -> aml_investigator (workflow aml_investigation_workflow)
* orchestrate: aml_investigation_workflow -> sar_drafting_agent (workflow aml_investigation_workflow)

## Policy rules

* `core.critical_risk_requires_approval` (pdp_request, constraint, MANUAL_REVIEW)
* `access.entry.ingress__aml_office_router` (pdp_request, permit)
* `access.entry.ingress__back_office_router` (pdp_request, permit)
* `access.entry.ingress__dispute_resolution_agent` (pdp_request, permit)
* `access.entry.ingress__front_office_router` (pdp_request, permit)
* `access.entry.ingress__loan_preapproval_agent` (pdp_request, permit)
* `access.entry.ingress__mid_office_router` (pdp_request, permit)
* `access.entry.ingress__sar_escalation_agent` (pdp_request, permit)
* `access.entry.ingress__user_proxy_agent` (pdp_request, permit)
* `access.input.ingress` (pdp_request, permit)
* `access.orchestrate.aml_investigation_workflow__aml_investigator` (pdp_request, permit)
* `access.orchestrate.aml_investigation_workflow__sar_drafting_agent` (pdp_request, permit)
* `access.orchestrate.back_office_eod_workflow__eod_processing_agent` (pdp_request, permit)
* `access.orchestrate.back_office_eod_workflow__exception_agent` (pdp_request, permit)
* `access.orchestrate.back_office_eod_workflow__ledger_update_agent` (pdp_request, permit)
* `access.orchestrate.back_office_eod_workflow__reconciliation_agent` (pdp_request, permit)
* `access.orchestrate.back_office_eod_workflow__report_writing_agent` (pdp_request, permit)
* `access.orchestrate.back_office_eod_workflow__validation_checkpoint_agent` (pdp_request, permit)
* `access.orchestrate.customer_service_chatbot_workflow__chatbot_intent_agent` (pdp_request, permit)
* `access.orchestrate.customer_service_chatbot_workflow__customer_service_agent` (pdp_request, permit)
* `access.orchestrate.customer_service_chatbot_workflow__knowledge_base_agent` (pdp_request, permit)
* `access.orchestrate.customer_service_chatbot_workflow__transaction_processing_agent` (pdp_request, permit)
* `access.orchestrate.front_office_transaction_workflow__compliance_agent` (pdp_request, permit)
* `access.orchestrate.front_office_transaction_workflow__decision_making_agent` (pdp_request, permit)
* `access.orchestrate.front_office_transaction_workflow__fraud_detection_agent` (pdp_request, permit)
* `access.orchestrate.front_office_transaction_workflow__transaction_monitoring_agent` (pdp_request, permit)
* `access.orchestrate.mid_office_planning_parallel__support_guidance_agent` (pdp_request, permit)
* `access.orchestrate.mid_office_planning_parallel__validation_agent` (pdp_request, permit)
* `access.orchestrate.mid_office_planning_workflow__data_analysis_agent` (pdp_request, permit)
* `access.orchestrate.mid_office_planning_workflow__forecasting_agent` (pdp_request, permit)
* `access.orchestrate.mid_office_planning_workflow__mid_office_planning_parallel` (pdp_request, permit)
* `access.orchestrate.mid_office_planning_workflow__planning_summary_agent` (pdp_request, permit)
* `access.orchestrate.mid_office_planning_workflow__staff_scheduling_agent` (pdp_request, permit)
* `access.orchestrate.representative_assist_parallel__financial_data_agent` (pdp_request, permit)
* `access.orchestrate.representative_assist_parallel__loan_agent` (pdp_request, permit)
* `access.orchestrate.representative_assist_parallel__recommender_agent` (pdp_request, permit)
* `access.orchestrate.representative_assist_parallel__risk_compliance_agent` (pdp_request, permit)
* `access.orchestrate.representative_assistant_workflow__representative_assist_parallel` (pdp_request, permit)
* `access.orchestrate.representative_assistant_workflow__representative_merge_agent` (pdp_request, permit)
* `access.output.aml_investigation_workflow` (pdp_request, permit)
* `access.output.aml_investigator` (pdp_request, permit)
* `access.output.aml_office_router` (pdp_request, permit)
* `access.output.back_office_eod_workflow` (pdp_request, permit)
* `access.output.back_office_router` (pdp_request, permit)
* `access.output.chatbot_intent_agent` (pdp_request, permit)
* `access.output.compliance_agent` (pdp_request, permit)
* `access.output.customer_service_agent` (pdp_request, permit)
* `access.output.customer_service_chatbot_workflow` (pdp_request, permit)
* `access.output.data_analysis_agent` (pdp_request, permit)
* `access.output.decision_making_agent` (pdp_request, permit)
* `access.output.dispute_resolution_agent` (pdp_request, permit)
* `access.output.eod_processing_agent` (pdp_request, permit)
* `access.output.exception_agent` (pdp_request, permit)
* `access.output.financial_data_agent` (pdp_request, permit)
* `access.output.forecasting_agent` (pdp_request, permit)
* `access.output.fraud_detection_agent` (pdp_request, permit)
* `access.output.front_office_router` (pdp_request, permit)
* `access.output.front_office_transaction_workflow` (pdp_request, permit)
* `access.output.knowledge_base_agent` (pdp_request, permit)
* `access.output.ledger_update_agent` (pdp_request, permit)
* `access.output.loan_agent` (pdp_request, permit)
* `access.output.loan_preapproval_agent` (pdp_request, permit)
* `access.output.mid_office_router` (pdp_request, permit)
* `access.output.planning_summary_agent` (pdp_request, permit)
* `access.output.recommender_agent` (pdp_request, permit)
* `access.output.reconciliation_agent` (pdp_request, permit)
* `access.output.report_writing_agent` (pdp_request, permit)
* `access.output.representative_merge_agent` (pdp_request, permit)
* `access.output.risk_compliance_agent` (pdp_request, permit)
* `access.output.sar_drafting_agent` (pdp_request, permit)
* `access.output.sar_escalation_agent` (pdp_request, permit)
* `access.output.staff_scheduling_agent` (pdp_request, permit)
* `access.output.support_guidance_agent` (pdp_request, permit)
* `access.output.transaction_monitoring_agent` (pdp_request, permit)
* `access.output.transaction_processing_agent` (pdp_request, permit)
* `access.output.user_proxy_agent` (pdp_request, permit)
* `access.output.validation_agent` (pdp_request, permit)
* `access.output.validation_checkpoint_agent` (pdp_request, permit)
* `access.tool.aml_investigator__check_threshold_anomaly` (pdp_request, permit)
* `access.tool.aml_investigator__detect_structuring` (pdp_request, permit)
* `access.tool.aml_investigator__find_mule_rings_for_customer` (pdp_request, permit)
* `access.tool.aml_investigator__get_aml_alert` (pdp_request, permit)
* `access.tool.aml_investigator__get_customer_context` (pdp_request, permit)
* `access.tool.aml_investigator__list_aml_alerts` (pdp_request, permit)
* `access.tool.aml_investigator__list_recent_transactions` (pdp_request, permit)
* `access.tool.aml_investigator__transition_aml_alert_status` (pdp_request, permit)
* `access.tool.aml_investigator__verify_identity_document` (pdp_request, permit)
* `access.tool.compliance_agent__get_customer_context` (pdp_request, permit)
* `access.tool.compliance_agent__get_transaction_context` (pdp_request, permit)
* `access.tool.compliance_agent__search_policies` (pdp_request, permit)
* `access.tool.data_analysis_agent__get_operations_snapshot` (pdp_request, permit)
* `access.tool.decision_making_agent__submit_manual_review` (pdp_request, permit)
* `access.tool.dispute_resolution_agent__file_dispute` (pdp_request, permit)
* `access.tool.dispute_resolution_agent__get_dispute_status` (pdp_request, permit)
* `access.tool.eod_processing_agent__get_eod_batch` (pdp_request, permit)
* `access.tool.exception_agent__create_exception_case` (pdp_request, permit)
* `access.tool.financial_data_agent__get_customer_financial_profile` (pdp_request, permit)
* `access.tool.forecasting_agent__get_operations_snapshot` (pdp_request, permit)
* `access.tool.fraud_detection_agent__get_customer_context` (pdp_request, permit)
* `access.tool.fraud_detection_agent__get_transaction_context` (pdp_request, permit)
* `access.tool.fraud_detection_agent__list_recent_transactions` (pdp_request, permit)
* `access.tool.knowledge_base_agent__search_faqs` (pdp_request, permit)
* `access.tool.ledger_update_agent__apply_ledger_updates` (pdp_request, permit)
* `access.tool.loan_agent__search_loan_playbooks` (pdp_request, permit)
* `access.tool.loan_preapproval_agent__get_loan_application_status` (pdp_request, permit)
* `access.tool.loan_preapproval_agent__submit_loan_application` (pdp_request, permit)
* `access.tool.recommender_agent__search_product_catalog` (pdp_request, permit)
* `access.tool.reconciliation_agent__get_reconciliation_data` (pdp_request, permit)
* `access.tool.report_writing_agent__store_report` (pdp_request, permit)
* `access.tool.risk_compliance_agent__search_policies` (pdp_request, permit)
* `access.tool.sar_escalation_agent__file_sar_report` (pdp_request, permit)
* `access.tool.sar_escalation_agent__get_exception_case` (pdp_request, permit)
* `access.tool.sar_escalation_agent__get_sar_status` (pdp_request, permit)
* `access.tool.support_guidance_agent__get_support_playbooks` (pdp_request, permit)
* `access.tool.transaction_monitoring_agent__get_customer_context` (pdp_request, permit)
* `access.tool.transaction_monitoring_agent__get_transaction_context` (pdp_request, permit)
* `access.tool.transaction_monitoring_agent__list_recent_transactions` (pdp_request, permit)
* `access.tool.transaction_processing_agent__execute_transfer` (pdp_request, permit)
* `access.tool.user_proxy_agent__get_branch_workload` (pdp_request, permit)
* `access.tool.user_proxy_agent__get_customer_product_affinity` (pdp_request, permit)
* `access.tool.user_proxy_agent__get_reconciliation_mismatches` (pdp_request, permit)
* `access.tool.user_proxy_agent__get_transaction` (pdp_request, permit)
* `access.tool.user_proxy_agent__propose_staffing_adjustment` (pdp_request, permit)
* `access.tool.user_proxy_agent__resolve_ledger_entry` (pdp_request, permit)
* `access.tool.user_proxy_agent__run_fraud_and_compliance_workflow` (pdp_request, permit)
* `access.tool.user_proxy_agent__trigger_eod_reconciliation` (pdp_request, permit)
* `access.tool.user_proxy_agent__update_transaction_status` (pdp_request, permit)
* `access.tool.validation_agent__persist_validated_schedule` (pdp_request, permit)
* `access.tool.validation_checkpoint_agent__validate_eod_readiness` (pdp_request, permit)
* `access.transfer.aml_office_router__aml_investigation_workflow` (pdp_request, permit)
* `access.transfer.aml_office_router__back_office_router` (pdp_request, permit)
* `access.transfer.aml_office_router__front_office_router` (pdp_request, permit)
* `access.transfer.aml_office_router__mid_office_router` (pdp_request, permit)
* `access.transfer.aml_office_router__user_proxy_agent` (pdp_request, permit)
* `access.transfer.back_office_router__aml_office_router` (pdp_request, permit)
* `access.transfer.back_office_router__back_office_eod_workflow` (pdp_request, permit)
* `access.transfer.back_office_router__front_office_router` (pdp_request, permit)
* `access.transfer.back_office_router__mid_office_router` (pdp_request, permit)
* `access.transfer.back_office_router__sar_escalation_agent` (pdp_request, permit)
* `access.transfer.back_office_router__user_proxy_agent` (pdp_request, permit)
* `access.transfer.dispute_resolution_agent__customer_service_chatbot_workflow` (pdp_request, permit)
* `access.transfer.dispute_resolution_agent__front_office_router` (pdp_request, permit)
* `access.transfer.dispute_resolution_agent__front_office_transaction_workflow` (pdp_request, permit)
* `access.transfer.front_office_router__aml_office_router` (pdp_request, permit)
* `access.transfer.front_office_router__back_office_router` (pdp_request, permit)
* `access.transfer.front_office_router__customer_service_chatbot_workflow` (pdp_request, permit)
* `access.transfer.front_office_router__dispute_resolution_agent` (pdp_request, permit)
* `access.transfer.front_office_router__front_office_transaction_workflow` (pdp_request, permit)
* `access.transfer.front_office_router__mid_office_router` (pdp_request, permit)
* `access.transfer.front_office_router__user_proxy_agent` (pdp_request, permit)
* `access.transfer.loan_preapproval_agent__mid_office_planning_workflow` (pdp_request, permit)
* `access.transfer.loan_preapproval_agent__mid_office_router` (pdp_request, permit)
* `access.transfer.loan_preapproval_agent__representative_assistant_workflow` (pdp_request, permit)
* `access.transfer.mid_office_router__aml_office_router` (pdp_request, permit)
* `access.transfer.mid_office_router__back_office_router` (pdp_request, permit)
* `access.transfer.mid_office_router__front_office_router` (pdp_request, permit)
* `access.transfer.mid_office_router__loan_preapproval_agent` (pdp_request, permit)
* `access.transfer.mid_office_router__mid_office_planning_workflow` (pdp_request, permit)
* `access.transfer.mid_office_router__representative_assistant_workflow` (pdp_request, permit)
* `access.transfer.mid_office_router__user_proxy_agent` (pdp_request, permit)
* `access.transfer.sar_escalation_agent__back_office_eod_workflow` (pdp_request, permit)
* `access.transfer.sar_escalation_agent__back_office_router` (pdp_request, permit)
* `access.transfer.user_proxy_agent__aml_office_router` (pdp_request, permit)
* `access.transfer.user_proxy_agent__back_office_router` (pdp_request, permit)
* `access.transfer.user_proxy_agent__front_office_router` (pdp_request, permit)
* `access.transfer.user_proxy_agent__mid_office_router` (pdp_request, permit)
* `identity.spiffe-b-agent-verified` (pdp_request, constraint, DENY)
* `identity.spiffe-b-service-io-only` (pdp_request, constraint, DENY)
* `identity.known-subject-kind` (pdp_request, constraint, DENY)
* `identity.plugin-agent-bound` (pdp_request, constraint, DENY)
* `identity.authenticated` (pdp_request, constraint, DENY)
* `content.input.prompt-injection` (input_message, constraint, DENY)
* `content.input.api_key` (input_message, constraint, FLAG)
* `content.input.private_key` (input_message, constraint, FLAG)
* `content.input.max-length` (input_message, constraint, DENY)
* `content.output.api_key` (output_message, constraint, DENY)
* `content.output.credit_card` (output_message, constraint, DENY)
* `content.output.email` (output_message, constraint, FLAG)
* `content.output.iban` (output_message, constraint, FLAG)
* `content.output.phone` (output_message, constraint, FLAG)
* `content.output.private_key` (output_message, constraint, DENY)
* `content.output.ssn` (output_message, constraint, DENY)
* `content.agent-message.prompt-injection` (agent_message, constraint, FLAG)
* `content.tool-result.prompt-injection` (tool_result, constraint, FLAG)
* `content.tool-result.api_key` (tool_result, constraint, FLAG)
* `content.tool-result.private_key` (tool_result, constraint, FLAG)
* `content.model.declared-functions` (model_request, constraint, DENY)
* `content.model.declared-builtins` (model_request, constraint, DENY)
* `workflow.order.mid_office_planning_workflow.2` (workflow_run, temporal)
* `workflow.order.mid_office_planning_workflow.3` (workflow_run, temporal)
* `workflow.order.mid_office_planning_workflow.4` (workflow_run, temporal)
* `workflow.order.mid_office_planning_workflow.5` (workflow_run, temporal)
* `workflow.order.representative_assistant_workflow.2` (workflow_run, temporal)
* `gateway.P1_identity` (request_attempt, temporal)
* `gateway.P1_authorization` (request_attempt, temporal)
* `gateway.P1_permit` (request_attempt, temporal)
* `gateway.P1_binding` (request_attempt, temporal)
* `gateway.P1_admission` (request_attempt, temporal)
* `gateway.P2_request` (request_attempt, temporal)
* `gateway.P5_live` (request_attempt, temporal)
* `gateway.P6_pre_audit` (request_attempt, temporal)
* `gateway.P6_post_audit` (request_attempt, temporal)
* `gateway.P6_outcome_after_start` (request_attempt, temporal)
* `gateway.P6_outcome_recorded` (request_attempt, temporal)
* `gateway.P6_single_outcome` (request_attempt, temporal)
* `gateway.P2_operation` (operation, temporal)
* `gateway.P3_at_most_once` (operation, temporal)
* `gateway.P4_participant` (workflow_participation, temporal)
* `gateway.P4_within_dispatch` (workflow_participation, temporal)

## Static cross-check

```json
{
  "agents_only_in_source": [],
  "agents_only_live": [],
  "available": true,
  "live_agents": 43,
  "note": "The live object graph is authoritative. Agents only in the source are not reachable from the application's root (dead code, or built for another app); agents only live are constructed dynamically (factories, loops, configuration).",
  "static_agents": 43,
  "static_coverage_percent": 100.0,
  "static_unresolved_findings": 0,
  "tools_only_live": [
    "get_branch_workload",
    "get_customer_product_affinity",
    "get_reconciliation_mismatches",
    "get_transaction",
    "propose_staffing_adjustment",
    "resolve_ledger_entry",
    "run_fraud_and_compliance_workflow",
    "trigger_eod_reconciliation",
    "update_transaction_status"
  ]
}
```
