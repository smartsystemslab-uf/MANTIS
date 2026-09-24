from google.adk.agents import LlmAgent
from mantis.banking.llm import build_model
from mantis.banking.callbacks import sanitize_tool_call_names
from ..tools.csr_tools import get_customer_financial_profile, search_loan_playbooks, search_product_catalog
from ..tools.ops_tools import get_operations_snapshot, get_support_playbooks, persist_validated_schedule
from ..tools.knowledge_tools import search_policies
from ..tools.loan_tools import submit_loan_application, get_loan_application_status
from mantis.banking.agents.workflow_agents import build_mid_office_planning_workflow, build_representative_assist_workflow


def build_mid_office_router() -> LlmAgent:
    data_analysis_agent = LlmAgent(
        after_model_callback=sanitize_tool_call_names,
        name="data_analysis_agent", model=build_model("data_analysis_agent"), description="Analyzes internal operations data and extracts workload patterns.",
        instruction="You are the data analysis agent. Always inspect the operations snapshot before responding. Return a compact JSON string with keys workload_prediction, bottlenecks, assumptions, and summary.",
        tools=[get_operations_snapshot], output_key="mo_workload_analysis")
    forecasting_agent = LlmAgent(
        after_model_callback=sanitize_tool_call_names,
        name="forecasting_agent", model=build_model("forecasting_agent"), description="Forecasts near-term operational demand from recent workload patterns.",
        instruction="You are the forecasting agent. Use the workload analysis from {mo_workload_analysis} and any operations snapshot you need. Return a compact JSON string with keys forecast_window, demand_forecast, confidence, demand_drivers, and risks.",
        tools=[get_operations_snapshot], output_key="mo_forecast_report")
    staff_scheduling_agent = LlmAgent(
        after_model_callback=sanitize_tool_call_names,
        name="staff_scheduling_agent", model=build_model("staff_scheduling_agent"), description="Translates forecasted demand into staffing and allocation proposals.",
        instruction="You are the staff scheduling agent. Use the forecast from {mo_forecast_report}. Return a compact JSON string with keys proposed_schedule, staffing_rationale, tradeoffs, and coverage_notes.",
        output_key="mo_schedule_draft")
    validation_agent = LlmAgent(
        after_model_callback=sanitize_tool_call_names,
        name="validation_agent", model=build_model("validation_agent"), description="Validates schedules and plans before they are released to operations.",
        instruction="You are the validation agent. Review the proposed schedule from {mo_schedule_draft}. If it is acceptable, call persist_validated_schedule. Return a compact JSON string with keys valid, issues, validation_notes, and persisted_schedule.",
        tools=[persist_validated_schedule], output_key="mo_validation_report")
    support_guidance_agent = LlmAgent(
        after_model_callback=sanitize_tool_call_names,
        name="support_guidance_agent", model=build_model("support_guidance_agent"), description="Generates internal support guidance for operational teams.",
        instruction="You are the support guidance agent. Use the workload analysis from {mo_workload_analysis} and retrieve any relevant playbooks. Return a compact JSON string with keys guidance, priority_actions, escalation_points, and service_risk.",
        tools=[get_support_playbooks], output_key="mo_support_guidance")
    planning_summary_agent = LlmAgent(
        after_model_callback=sanitize_tool_call_names,
        name="planning_summary_agent", model=build_model("planning_summary_agent"), description="Merges the planning workflow outputs into one final mid-office planning response.",
        instruction="You are the planning summary agent. Combine workload analysis {mo_workload_analysis}, forecast {mo_forecast_report}, schedule draft {mo_schedule_draft}, validation result {mo_validation_report}, and support guidance {mo_support_guidance}. Return a unified planning summary for operations with workload prediction, validated schedule status, and support guidance.",
        output_key="mid_office_planning_result")
    planning_workflow_agent = build_mid_office_planning_workflow(
        data_analysis_agent=data_analysis_agent,
        forecasting_agent=forecasting_agent,
        staff_scheduling_agent=staff_scheduling_agent,
        validation_agent=validation_agent,
        support_guidance_agent=support_guidance_agent,
        planning_summary_agent=planning_summary_agent,
    )
    financial_data_agent = LlmAgent(
        after_model_callback=sanitize_tool_call_names,
        name="financial_data_agent", model=build_model("financial_data_agent"), description="Retrieves customer-specific financial information for representative support.",
        instruction="You are the financial data agent. Always retrieve the customer financial profile before you summarize it. Return a compact JSON string with keys customer_data, notable_points, financial_risk, and servicing_context.", tools=[get_customer_financial_profile], output_key="mo_customer_data_report")
    recommender_agent = LlmAgent(
        after_model_callback=sanitize_tool_call_names,
        name="recommender_agent", model=build_model("recommender_agent"), description="Finds relevant product suggestions and next-best actions for the representative.",
        instruction="You are the recommender agent. Search the product catalog and produce recommendation logic grounded in the customer's needs. Return a compact JSON string with keys product_suggestions, why_fit, exclusions, and next_best_action.", tools=[search_product_catalog], output_key="mo_recommender_report")
    loan_agent = LlmAgent(
        after_model_callback=sanitize_tool_call_names,
        name="loan_agent", model=build_model("loan_agent"), description="Supports loan process guidance for internal representatives.",
        instruction="You are the loan agent. Use loan playbooks to map the customer's request to a practical loan-handling path. Return a compact JSON string with keys loan_flow, required_documents, likely_constraints, and recommended_next_step.", tools=[search_loan_playbooks], output_key="mo_loan_report")
    risk_compliance_agent = LlmAgent(
        after_model_callback=sanitize_tool_call_names,
        name="risk_compliance_agent", model=build_model("risk_compliance_agent"), description="Checks policy and risk constraints before recommendations are shown to representatives.",
        instruction="You are the risk and compliance agent for representative assist. Search relevant policies and evaluate the proposed guidance against risk and policy limits. Return a compact JSON string with keys policy_risk, compliance_notes, blocked_actions, and approved_guidance_scope.", tools=[search_policies], output_key="mo_risk_compliance_report")
    representative_merge_agent = LlmAgent(
        after_model_callback=sanitize_tool_call_names,
        name="representative_merge_agent", model=build_model("representative_merge_agent"), description="Merges all representative-assist specialist outputs into one CSR-facing answer.",
        instruction="You are the final merger for the internal representative-assist workflow. Combine customer data {mo_customer_data_report}, product suggestions {mo_recommender_report}, loan flow {mo_loan_report}, and risk or policy checks {mo_risk_compliance_report}. Return a single representative-ready recommendation that clearly states customer data, product suggestions, loan flow, and policy or risk checks.", output_key="mid_office_representative_result")
    representative_assistant_workflow = build_representative_assist_workflow(
        financial_data_agent=financial_data_agent,
        recommender_agent=recommender_agent,
        loan_agent=loan_agent,
        risk_compliance_agent=risk_compliance_agent,
        merger_agent=representative_merge_agent,
    )
    # Post-Paper Extension (coding plan §11: "Additional banking workloads
    # and deployment variants") -- a genuinely new mid-office process (a
    # real, computed loan/credit-line pre-approval decision, persisted to
    # loan_applications), not a reworded prompt into loan_agent above,
    # which only ever returns informational process guidance
    # (required_documents, likely_constraints) and never makes or persists
    # an actual decision. See BankingRepository.create_loan_application.
    loan_preapproval_agent = LlmAgent(
        after_model_callback=sanitize_tool_call_names,
        name="loan_preapproval_agent", model=build_model("loan_preapproval_agent"),
        description="Submits a real loan/credit-line pre-approval application for a customer and reports the computed decision.",
        instruction="You are the loan pre-approval agent. Call submit_loan_application with the customer id, requested amount, and stated purpose to get a real, computed pre-approval decision. If asked about an existing application, call get_loan_application_status with the application id. Return a compact JSON string with keys application_id, decision, decision_reason, and customer_message summarizing the outcome in plain language. When calling a tool, use the exact tool name only. Never include commentary, channel markers, or prefixes such as to=functions.",
        tools=[submit_loan_application, get_loan_application_status], output_key="mo_loan_preapproval_result")
    return LlmAgent(
        after_model_callback=sanitize_tool_call_names,
        name="mid_office_router", model=build_model("mid_office_router"), description="Routes internal operational work into planning/support, representative-assist, or loan pre-approval workflows.",
        instruction="Route internal work to the right mid-office workflow. Use mid_office_planning_workflow for operations planning, forecasting, staffing, validation, and support guidance. Use representative_assistant_workflow for internal customer-service representative assistance. Use loan_preapproval_agent when the request is to submit a real loan or credit-line application and get an actual pre-approval decision (not just informational loan guidance).",
        sub_agents=[planning_workflow_agent, representative_assistant_workflow, loan_preapproval_agent], output_key="mid_office_router_result")
