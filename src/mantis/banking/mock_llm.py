"""Deterministic, zero-network stand-in for the real model.

Exists to isolate instrumentation overhead from LLM sampling latency (the
plan's own suggested mitigation for that risk) -- opt-in via
MANTIS_MOCK_LLM, never the default. It always answers with a short, fixed
text response and never emits a function call, so it exercises the input,
agent, interaction, and output control points at effectively zero latency;
it does not exercise the tool control point, since faithfully mocking a
real tool call would require guessing per-tool argument schemas. Overhead
benchmarks that need tool-stage coverage should use the real model.
"""
from typing import AsyncGenerator
from google.adk.models import BaseLlm, LlmRequest, LlmResponse
from google.genai import types

MOCK_MODEL_NAME = "mantis-mock-llm"


class MockLlm(BaseLlm):
    model: str = MOCK_MODEL_NAME

    async def generate_content_async(
        self, llm_request: LlmRequest, stream: bool = False
    ) -> AsyncGenerator[LlmResponse, None]:
        yield LlmResponse(
            content=types.Content(
                role="model",
                parts=[types.Part(text="Mock response: no attack-relevant tool call, benchmark mode.")],
            ),
            turn_complete=True,
        )
