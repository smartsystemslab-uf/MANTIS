"""Deterministic, zero-network stand-in for the real model.

Exists to isolate instrumentation overhead from LLM sampling latency (the
plan's own suggested mitigation for that risk) -- opt-in via
MANTIS_MOCK_LLM, never the default.

Tool-calling: on the first call for a given agent turn (no function_response
yet in the conversation), if the agent declares any tools, the mock emits a
function call to one of them with a plausible dummy argument set, so the
tool control point -- and any tool-stage attack plugin -- is exercised the
same way a real model call would exercise it. Once a function_response is
present (the tool has already run), it returns a short final text response
instead. This is a heuristic, not a planner: it does not reason about which
tool is *appropriate*, only that *some* real tool call happens.
"""
from typing import AsyncGenerator
from google.adk.models import BaseLlm, LlmRequest, LlmResponse
from google.genai import types

MOCK_MODEL_NAME = "mantis-mock-llm"

# Plausible dummy arguments per real banking tool, so a mock-triggered call
# exercises the tool's normal code path instead of failing on a missing
# required argument. Anything not listed here is called with no arguments.
_DUMMY_ARGS = {
    # transfer_to_agent is deliberately absent: ADK only allows a transfer
    # between agents that are parent/child/sibling of each other (see
    # google.adk.workflow.utils._transfer_utils.resolve_and_derive_transfer_context),
    # and the valid destination set depends entirely on which agent is
    # calling -- something this table has no way to know (the mock picks
    # whichever tool is first in tools_dict, which is often the outermost
    # router, several relatedness hops above any leaf agent a route_confusion
    # config names). A static agent_name here is right for one calling
    # context and a hard crash ("unrelated agent") for every other one, so
    # transfer_to_agent falls through to the no-args path below; ADK treats
    # a missing agent_name as a no-op transfer request rather than an error.
    "get_customer_context": {"customer_id": "CUST-001"},
    "get_transaction_context": {"transaction_id": "TXN-1001"},
    "list_recent_transactions": {"customer_id": "CUST-001"},
    "submit_manual_review": {"case_type": "mock_review", "payload": "{}"},
    "execute_transfer": {"source_account": "CHK-001", "destination_account": "EXT-998", "amount": 100.0, "customer_id": "CUST-001"},
    "get_customer_financial_profile": {"customer_id": "CUST-001"},
    "search_product_catalog": {"query": "savings"},
    "search_loan_playbooks": {"query": "home equity"},
    "search_policies": {"query": "AML"},
    "search_faqs": {"query": "dispute"},
    "get_operations_snapshot": {"date": "2026-04-21"},
    "persist_validated_schedule": {"schedule_json": "{}"},
    "get_support_playbooks": {"query": "staffing"},
    "validate_eod_readiness": {"batch_id": "EOD-2026-04-21-CLEAN"},
    "get_eod_batch": {"batch_id": "EOD-2026-04-21-CLEAN"},
    "apply_ledger_updates": {"batch_id": "EOD-2026-04-21-CLEAN", "posting_instructions": "{}"},
    "get_reconciliation_data": {"batch_id": "EOD-2026-04-21-CLEAN"},
    "create_exception_case": {"batch_id": "EOD-2026-04-21-MISMATCH", "mismatch_summary": "mock mismatch"},
    "store_report": {"batch_id": "EOD-2026-04-21-CLEAN", "report_body": "mock report"},
}


def _already_has_tool_result(contents) -> bool:
    for content in contents or []:
        for part in getattr(content, "parts", None) or []:
            if getattr(part, "function_response", None) is not None:
                return True
    return False


class MockLlm(BaseLlm):
    model: str = MOCK_MODEL_NAME

    async def generate_content_async(
        self, llm_request: LlmRequest, stream: bool = False
    ) -> AsyncGenerator[LlmResponse, None]:
        tools_dict = getattr(llm_request, "tools_dict", None) or {}

        if tools_dict and not _already_has_tool_result(llm_request.contents):
            tool_name = next(iter(tools_dict.keys()))
            args = _DUMMY_ARGS.get(tool_name, {})
            yield LlmResponse(
                content=types.Content(
                    role="model",
                    parts=[types.Part(function_call=types.FunctionCall(name=tool_name, args=args))],
                ),
                turn_complete=True,
            )
            return

        yield LlmResponse(
            content=types.Content(
                role="model",
                parts=[types.Part(text="Mock response: benchmark mode, no real reasoning performed.")],
            ),
            turn_complete=True,
        )
