from typing import Any, Optional, Dict
from google.adk.plugins import BasePlugin
from google.adk.agents import BaseAgent
from google.adk.tools import BaseTool

from mantis.core.hooks import HookBus, HookContext, HookAction

class MantisHookPlugin(BasePlugin):
    name = "mantis_hook_plugin"
    
    def __init__(self, hook_bus: HookBus, run_id: str = "default-run", workflow_id: str = "default-workflow"):
        self.hook_bus = hook_bus
        self.run_id = run_id
        self.workflow_id = workflow_id
        # In a real trace, we would track trace_id dynamically.
        self.trace_id = run_id

    def _create_ctx(self, stage: str, source: Optional[str] = None, target: Optional[str] = None, payload: Dict[str, Any] = None) -> HookContext:
        return HookContext(
            run_id=self.run_id,
            trace_id=self.trace_id,
            workflow_id=self.workflow_id,
            stage=stage,
            source=source,
            target=target,
            payload=payload or {}
        )

    # 1. Input (before_run / after_run)
    async def before_run_callback(self, *, invocation_context: Any) -> Any:
        ctx = self._create_ctx("input", target="run", payload={"input": getattr(invocation_context, 'invocation_id', 'unknown')})
        res = self.hook_bus.dispatch("before_input", ctx)
        if res.action in [HookAction.SKIP, HookAction.DENY]:
            # To deny early, we'd need to return a Content object. We'll return a mock dict.
            return {"parts": []} 
        return None

    # 2. Agent (before_agent / after_agent)
    async def before_agent_callback(self, *, agent: BaseAgent, callback_context: Any) -> Any:
        ctx = self._create_ctx("agent", target=agent.name, payload={"context": callback_context.model_dump() if hasattr(callback_context, 'model_dump') else {}})
        res = self.hook_bus.dispatch("before_agent", ctx)
        if res.action in [HookAction.SKIP, HookAction.DENY]:
            return {"parts": []}
        return None

    # 3. Interaction (before_model / after_model maps to messages)
    async def before_model_callback(self, *, callback_context: Any, llm_request: Any) -> Any:
        contents = getattr(llm_request, 'contents', [])
        ctx = self._create_ctx("interaction", source="agent", target="model", payload={"messages": contents})
        res = self.hook_bus.dispatch("before_message", ctx)
        if res.action == HookAction.MUTATE and res.payload:
            if hasattr(llm_request, 'contents'):
                llm_request.contents = res.payload.get("messages", contents)
        elif res.action in [HookAction.SKIP, HookAction.DENY]:
            # Return a mock response
            class MockResponse:
                content = "denied"
            return MockResponse()
        return None

    # 4. Tool/API (before_tool / after_tool)
    async def before_tool_callback(self, *, tool: BaseTool, tool_args: dict[str, Any], tool_context: Any) -> Optional[dict[str, Any]]:
        ctx = self._create_ctx("tool", target=tool.name, payload=tool_args)
        res = self.hook_bus.dispatch("before_tool", ctx)
        
        if res.action == HookAction.MUTATE and res.payload is not None:
            # We must return a dict to replace the arguments to the tool!
            return res.payload
        elif res.action in [HookAction.SKIP, HookAction.DENY]:
            # Return an empty dict or error dict to simulate block
            return {"error": "tool blocked by hook"}
        return None

    async def after_tool_callback(self, *, tool: BaseTool, tool_args: dict[str, Any], tool_context: Any, result: Any) -> Optional[dict[str, Any]]:
        payload = result if isinstance(result, dict) else {"result": result}
        ctx = self._create_ctx("tool", source=tool.name, payload=payload)
        res = self.hook_bus.dispatch("after_tool", ctx)
        
        if res.action == HookAction.MUTATE and res.payload is not None:
            return res.payload
        elif res.action in [HookAction.SKIP, HookAction.DENY]:
            return {"error": "result blocked by hook"}
        return None

    # 5. Output (after_run maps to output check)
    async def after_run_callback(self, *, invocation_context: Any) -> None:
        ctx = self._create_ctx("output", source="run", payload={"status": "completed"})
        self.hook_bus.dispatch("after_output", ctx)
