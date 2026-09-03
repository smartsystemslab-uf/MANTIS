import logging
from enum import Enum
from typing import Any, Optional, Literal, Set, Protocol, List, Dict
from pydantic import BaseModel, Field, ConfigDict

logger = logging.getLogger(__name__)

class HookAction(str, Enum):
    CONTINUE = "continue"
    MUTATE = "mutate"
    SKIP = "skip"
    DENY = "deny"
    ERROR = "error"

class HookContext(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    run_id: str
    trace_id: str
    workflow_id: str
    stage: Literal['input', 'agent', 'interaction', 'tool', 'output']
    source: Optional[str] = None
    target: Optional[str] = None
    payload: Dict[str, Any]
    metadata: Dict[str, Any] = Field(default_factory=dict)

class HookResult(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    action: HookAction = HookAction.CONTINUE
    payload: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None

class ExperimentPlugin(Protocol):
    name: str
    supported_stages: Set[str]
    
    def apply(self, ctx: HookContext) -> HookResult: ...

class HookBus:
    def __init__(self):
        self._plugins: List[ExperimentPlugin] = []
        # Track coverage: {stage: {plugin_name: count}}
        self.coverage_stats: Dict[str, Dict[str, int]] = {
            "input": {},
            "agent": {},
            "interaction": {},
            "tool": {},
            "output": {}
        }
        self.coverage_hit: Dict[str, int] = {
            "before_input": 0, "after_input": 0,
            "before_agent": 0, "after_agent": 0,
            "before_message": 0, "after_message": 0,
            "before_tool": 0, "after_tool": 0,
            "before_output": 0, "after_output": 0,
        }

    def register(self, plugin: ExperimentPlugin) -> None:
        self._plugins.append(plugin)
        logger.info(f"Registered plugin {plugin.name} supporting stages {plugin.supported_stages}")

    def _record_coverage(self, specific_hook: str, stage: str, plugins_applied: List[str]):
        self.coverage_hit[specific_hook] += 1
        for p in plugins_applied:
            if p not in self.coverage_stats[stage]:
                self.coverage_stats[stage][p] = 0
            self.coverage_stats[stage][p] += 1

    def dispatch(self, specific_hook: str, ctx: HookContext) -> HookResult:
        """
        Dispatches the event to all registered plugins that support the context stage.
        If a plugin mutates the payload, the mutated payload is passed to the next plugin.
        If a plugin returns SKIP, DENY, or ERROR, the chain is halted immediately.
        """
        plugins_applied = []
        current_payload = dict(ctx.payload)
        
        for plugin in self._plugins:
            if ctx.stage in plugin.supported_stages:
                # Update payload in case it was mutated by a previous plugin in the chain
                ctx_copy = ctx.model_copy(update={"payload": current_payload})
                if ctx_copy.metadata is None:
                    ctx_copy.metadata = {}
                ctx_copy.metadata["specific_hook"] = specific_hook
                try:
                    result = plugin.apply(ctx_copy)
                    plugins_applied.append(plugin.name)
                    
                    if result.action == HookAction.MUTATE and result.payload is not None:
                        current_payload = result.payload
                    elif result.action in [HookAction.SKIP, HookAction.DENY, HookAction.ERROR]:
                        self._record_coverage(specific_hook, ctx.stage, plugins_applied)
                        return result
                except Exception as e:
                    logger.error(f"Plugin {plugin.name} raised exception on stage {ctx.stage}: {e}")
                    self._record_coverage(specific_hook, ctx.stage, plugins_applied)
                    return HookResult(action=HookAction.ERROR, error_message=str(e))
        
        self._record_coverage(specific_hook, ctx.stage, plugins_applied)
        return HookResult(action=HookAction.CONTINUE, payload=current_payload)

    def write_coverage(self, filepath: str) -> None:
        import json
        with open(filepath, "w") as f:
            json.dump({
                "hits": self.coverage_hit,
                "plugin_stats": self.coverage_stats
            }, f, indent=2)
