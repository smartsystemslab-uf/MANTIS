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


def test_build_model_switches_on_env_var(monkeypatch):
    from mantis.banking import llm as llm_module

    monkeypatch.setenv("MANTIS_MOCK_LLM", "1")
    model = llm_module.build_model()
    assert isinstance(model, MockLlm)
    assert model.model == MOCK_MODEL_NAME

    monkeypatch.delenv("MANTIS_MOCK_LLM", raising=False)
    model = llm_module.build_model()
    assert not isinstance(model, MockLlm)
