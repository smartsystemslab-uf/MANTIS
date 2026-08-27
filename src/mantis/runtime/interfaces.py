from typing import Protocol, Mapping, Any
from pydantic import BaseModel

class BankingSystemInventory(BaseModel):
    agents: list[str] = []
    tools: list[str] = []
    workflows: list[str] = []

class WorkflowSpec(BaseModel):
    id: str
    description: str

class ExperimentConfig(BaseModel):
    workflow: str
    seed: int = 42

class HookBus:
    pass

class RuntimeHandle(Protocol):
    async def run_message(self, message: str) -> Any: ...

class BankingRuntimeAdapter(Protocol):
    def inventory(self) -> BankingSystemInventory: ...
    def workflows(self) -> Mapping[str, WorkflowSpec]: ...
    def build(self, config: ExperimentConfig, hooks: HookBus) -> RuntimeHandle: ...
    def reset(self, seed: int) -> None: ...
