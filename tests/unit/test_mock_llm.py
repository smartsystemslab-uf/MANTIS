import asyncio
import os
from mantis.banking.mock_llm import MockLlm, MOCK_MODEL_NAME


def test_mock_llm_yields_a_complete_text_response():
    from google.adk.models import LlmRequest

    model = MockLlm()
    req = LlmRequest(model=model.model, contents=[])

    async def collect():
        responses = []
        async for resp in model.generate_content_async(req):
            responses.append(resp)
        return responses

    responses = asyncio.run(collect())
    assert len(responses) == 1
    assert responses[0].turn_complete is True
    assert responses[0].content.parts[0].text


def test_mock_llm_calls_a_declared_tool_with_plausible_args():
    from google.adk.models import LlmRequest
    from google.adk.tools import FunctionTool

    def get_customer_context(customer_id: str) -> str:
        return "{}"

    model = MockLlm()
    tool = FunctionTool(get_customer_context)
    req = LlmRequest(model=model.model, contents=[], tools_dict={"get_customer_context": tool})

    async def collect():
        return [r async for r in model.generate_content_async(req)]

    responses = asyncio.run(collect())
    assert len(responses) == 1
    fc = responses[0].content.parts[0].function_call
    assert fc is not None
    assert fc.name == "get_customer_context"
    assert fc.args == {"customer_id": "CUST-001"}


def test_mock_llm_calls_transfer_to_agent_with_no_args():
    from google.adk.models import LlmRequest
    from google.adk.tools import FunctionTool

    def transfer_to_agent(agent_name: str) -> None:
        return None

    model = MockLlm()
    tool = FunctionTool(transfer_to_agent)
    req = LlmRequest(model=model.model, contents=[], tools_dict={"transfer_to_agent": tool})

    async def collect():
        return [r async for r in model.generate_content_async(req)]

    responses = asyncio.run(collect())
    fc = responses[0].content.parts[0].function_call
    assert fc.name == "transfer_to_agent"
    # No entry in _DUMMY_ARGS on purpose -- see the comment above the table.
    # ADK treats a missing agent_name as a no-op transfer rather than an
    # error, whereas any static name here is only valid for one caller's
    # position in the agent tree and a hard crash for every other one.
    assert fc.args == {}


def test_mock_llm_returns_text_after_a_tool_result_is_present():
    from google.adk.models import LlmRequest
    from google.adk.tools import FunctionTool
    from google.genai import types

    def get_customer_context(customer_id: str) -> str:
        return "{}"

    model = MockLlm()
    tool = FunctionTool(get_customer_context)
    tool_result_content = types.Content(
        role="user",
        parts=[types.Part(function_response=types.FunctionResponse(name="get_customer_context", response={"result": "{}"}))],
    )
    req = LlmRequest(model=model.model, contents=[tool_result_content], tools_dict={"get_customer_context": tool})

    async def collect():
        return [r async for r in model.generate_content_async(req)]

    responses = asyncio.run(collect())
    assert responses[0].content.parts[0].function_call is None
    assert responses[0].content.parts[0].text


def test_build_model_switches_on_env_var(monkeypatch):
    from mantis.banking import llm as llm_module

    monkeypatch.setenv("MANTIS_MOCK_LLM", "1")
    model = llm_module.build_model()
    assert isinstance(model, MockLlm)
    assert model.model == MOCK_MODEL_NAME

    monkeypatch.delenv("MANTIS_MOCK_LLM", raising=False)
    model = llm_module.build_model()
    assert not isinstance(model, MockLlm)


def test_model_override_applies_only_to_named_agent(monkeypatch):
    from mantis.banking import llm as llm_module

    monkeypatch.delenv("MANTIS_MOCK_LLM", raising=False)
    llm_module.set_model_overrides({"fraud_detection_agent": "gpt-4-turbo"})
    try:
        overridden = llm_module.build_model("fraud_detection_agent")
        default = llm_module.build_model("compliance_agent")
        no_name = llm_module.build_model()
        assert overridden.model == "openai/gpt-4-turbo"
        assert default.model == f"openai/{llm_module.settings.model_name}"
        assert no_name.model == f"openai/{llm_module.settings.model_name}"
    finally:
        llm_module.set_model_overrides(None)


def test_model_override_of_literal_default_is_a_noop(monkeypatch):
    from mantis.banking import llm as llm_module

    monkeypatch.delenv("MANTIS_MOCK_LLM", raising=False)
    llm_module.set_model_overrides({"fraud_detection_agent": "default"})
    try:
        model = llm_module.build_model("fraud_detection_agent")
        assert model.model == f"openai/{llm_module.settings.model_name}"
    finally:
        llm_module.set_model_overrides(None)
