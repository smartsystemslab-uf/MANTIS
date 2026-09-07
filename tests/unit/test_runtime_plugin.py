import asyncio
from typing import List, Set

from mantis.hooks import HookBus, HookContext, HookResult, HookAction
from mantis.runtime.plugin import MantisHookPlugin


class RecordingPlugin:
    """Records every HookContext dispatched to it, so tests can inspect
    exactly what MantisHookPlugin's ADK callbacks handed to the HookBus."""

    name = "recorder"
    supported_stages: Set[str] = {"input", "agent", "interaction", "tool", "output"}

    def __init__(self):
        self.contexts: List[HookContext] = []

    def apply(self, ctx: HookContext) -> HookResult:
        self.contexts.append(ctx)
        return HookResult(action=HookAction.CONTINUE)


class FakeTool:
    def __init__(self, name):
        self.name = name


class FakeToolContext:
    """Stands in for ADK's Context/ToolContext, which exposes agent_name
    (ReadonlyContext) and function_call_id (Context) as real attributes."""

    def __init__(self, agent_name, function_call_id):
        self.agent_name = agent_name
        self.function_call_id = function_call_id


class FakeCallbackContext:
    def __init__(self, agent_name, invocation_id):
        self.agent_name = agent_name
        self.invocation_id = invocation_id


class FakeLlmRequest:
    contents: list = []


class FakeLlmResponse:
    content = "hi"


def _plugin_with_recorder():
    bus = HookBus()
    recorder = RecordingPlugin()
    bus.register(recorder)
    plugin = MantisHookPlugin(bus, run_id="run-1", workflow_id="wf-1", domain="front_office", scenario="s")
    return plugin, recorder


def test_before_tool_callback_sets_calling_agent_as_source_and_tool_call_id():
    plugin, recorder = _plugin_with_recorder()
    tool = FakeTool("get_customer_context")
    tool_context = FakeToolContext(agent_name="teller_agent", function_call_id="fc-1")

    asyncio.run(plugin.before_tool_callback(
        tool=tool, tool_args={"customer_id": "CUST-001"}, tool_context=tool_context,
    ))

    ctx = recorder.contexts[-1]
    assert ctx.source == "teller_agent"
    assert ctx.target == "get_customer_context"
    assert ctx.metadata["tool_call_id"] == "fc-1"


def test_after_tool_callback_sets_calling_agent_as_target_and_tool_call_id():
    plugin, recorder = _plugin_with_recorder()
    tool = FakeTool("get_customer_context")
    tool_context = FakeToolContext(agent_name="teller_agent", function_call_id="fc-1")

    asyncio.run(plugin.after_tool_callback(
        tool=tool, tool_args={}, tool_context=tool_context, result={"ok": True},
    ))

    ctx = recorder.contexts[-1]
    assert ctx.source == "get_customer_context"
    assert ctx.target == "teller_agent"
    assert ctx.metadata["tool_call_id"] == "fc-1"


def test_on_tool_error_callback_sets_calling_agent_as_target_and_tool_call_id():
    plugin, recorder = _plugin_with_recorder()
    tool = FakeTool("get_customer_context")
    tool_context = FakeToolContext(agent_name="teller_agent", function_call_id="fc-1")

    asyncio.run(plugin.on_tool_error_callback(
        tool=tool, tool_args={}, tool_context=tool_context, error=RuntimeError("boom"),
    ))

    ctx = recorder.contexts[-1]
    assert ctx.source == "get_customer_context"
    assert ctx.target == "teller_agent"
    assert ctx.metadata["tool_call_id"] == "fc-1"
    assert ctx.metadata["error"] is True


def test_before_model_callback_carries_invocation_id():
    plugin, recorder = _plugin_with_recorder()
    callback_context = FakeCallbackContext(agent_name="teller_agent", invocation_id="inv-1")

    asyncio.run(plugin.before_model_callback(callback_context=callback_context, llm_request=FakeLlmRequest()))

    ctx = recorder.contexts[-1]
    assert ctx.source == "teller_agent"
    assert ctx.metadata["invocation_id"] == "inv-1"


def test_after_model_callback_carries_invocation_id():
    plugin, recorder = _plugin_with_recorder()
    callback_context = FakeCallbackContext(agent_name="teller_agent", invocation_id="inv-1")

    asyncio.run(plugin.after_model_callback(callback_context=callback_context, llm_response=FakeLlmResponse()))

    ctx = recorder.contexts[-1]
    assert ctx.target == "teller_agent"
    assert ctx.metadata["invocation_id"] == "inv-1"
