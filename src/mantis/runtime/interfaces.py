from typing import Protocol, Mapping, Any
from pydantic import BaseModel

class BankingSystemInventory(BaseModel):
    agents: list[str] = []
    tools: list[str] = []
    workflows: list[str] = []
    # Domain -> {"agents": [...], "tools": [...]} breakdown, so an inventory
    # can be produced by banking domain as well as flat lists.
    domains: dict[str, dict[str, list[str]]] = {}

class WorkflowSpec(BaseModel):
    id: str
    description: str

from mantis.config.models import ExperimentConfig
from mantis.hooks import HookBus

class RuntimeHandle(Protocol):
    async def run_message(self, message: str) -> Any: ...

class BankingRuntimeAdapter(Protocol):
    def inventory(self) -> BankingSystemInventory: ...
    def workflows(self) -> Mapping[str, WorkflowSpec]: ...
    def build(self, config: ExperimentConfig, hooks: HookBus) -> RuntimeHandle: ...
    def reset(self, seed: int) -> None: ...
