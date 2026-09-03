"""Banking-domain semantic metadata for tool calls, keyed by tool name.

Used by the observability layer to populate operation_type, risk_level,
data_sensitivity, and financial_side_effect on ToolEvent without the core
MANTIS observability module needing to know anything about banking tools.
"""
from typing import Any, Dict, Optional, TypedDict


class ToolSemantics(TypedDict, total=False):
    operation_type: str  # "read" | "write"
    risk_level: str  # "low" | "medium" | "high"
    data_sensitivity: str  # "low" | "medium" | "high"
    financial_side_effect: bool


TOOL_SEMANTICS: Dict[str, ToolSemantics] = {
    # front office / customer
    "get_customer_context": {"operation_type": "read", "risk_level": "low", "data_sensitivity": "high", "financial_side_effect": False},
    "get_transaction_context": {"operation_type": "read", "risk_level": "low", "data_sensitivity": "high", "financial_side_effect": False},
    "list_recent_transactions": {"operation_type": "read", "risk_level": "low", "data_sensitivity": "high", "financial_side_effect": False},
    "submit_manual_review": {"operation_type": "write", "risk_level": "medium", "data_sensitivity": "medium", "financial_side_effect": False},
    "execute_transfer": {"operation_type": "write", "risk_level": "high", "data_sensitivity": "high", "financial_side_effect": True},
    # front office / csr
    "get_customer_financial_profile": {"operation_type": "read", "risk_level": "low", "data_sensitivity": "high", "financial_side_effect": False},
    "search_product_catalog": {"operation_type": "read", "risk_level": "low", "data_sensitivity": "low", "financial_side_effect": False},
    "search_loan_playbooks": {"operation_type": "read", "risk_level": "low", "data_sensitivity": "low", "financial_side_effect": False},
    # knowledge
    "search_policies": {"operation_type": "read", "risk_level": "low", "data_sensitivity": "low", "financial_side_effect": False},
    "search_faqs": {"operation_type": "read", "risk_level": "low", "data_sensitivity": "low", "financial_side_effect": False},
    # mid office / ops
    "get_operations_snapshot": {"operation_type": "read", "risk_level": "low", "data_sensitivity": "medium", "financial_side_effect": False},
    "persist_validated_schedule": {"operation_type": "write", "risk_level": "low", "data_sensitivity": "low", "financial_side_effect": False},
    "get_support_playbooks": {"operation_type": "read", "risk_level": "low", "data_sensitivity": "low", "financial_side_effect": False},
    # back office
    "validate_eod_readiness": {"operation_type": "read", "risk_level": "low", "data_sensitivity": "low", "financial_side_effect": False},
    "get_eod_batch": {"operation_type": "read", "risk_level": "low", "data_sensitivity": "medium", "financial_side_effect": False},
    "apply_ledger_updates": {"operation_type": "write", "risk_level": "high", "data_sensitivity": "high", "financial_side_effect": True},
    "get_reconciliation_data": {"operation_type": "read", "risk_level": "low", "data_sensitivity": "medium", "financial_side_effect": False},
    "create_exception_case": {"operation_type": "write", "risk_level": "medium", "data_sensitivity": "medium", "financial_side_effect": False},
    "store_report": {"operation_type": "write", "risk_level": "low", "data_sensitivity": "medium", "financial_side_effect": False},
    # ADK routing tool (not a banking tool, but appears in every trace)
    "transfer_to_agent": {"operation_type": "read", "risk_level": "low", "data_sensitivity": "low", "financial_side_effect": False},
}

# Tools whose invocation marks a workflow's real terminal decision, mapped to
# the outcome string an evaluation config's expected_terminal_state can target.
TERMINAL_TOOL_OUTCOMES: Dict[str, str] = {
    "submit_manual_review": "manual_review",
    "execute_transfer": "executed",
    "apply_ledger_updates": "ledger_updated",
    "create_exception_case": "exception_case_created",
    "store_report": "report_filed",
    "persist_validated_schedule": "schedule_persisted",
}


def get_tool_semantics(tool_name: Optional[str]) -> ToolSemantics:
    if not tool_name:
        return {}
    return TOOL_SEMANTICS.get(tool_name, {})


def get_terminal_outcome(tool_names_in_order: Any) -> Optional[str]:
    """Given tool names in call order, return the outcome of the last terminal tool called, if any."""
    outcome = None
    for name in tool_names_in_order:
        if name in TERMINAL_TOOL_OUTCOMES:
            outcome = TERMINAL_TOOL_OUTCOMES[name]
    return outcome
