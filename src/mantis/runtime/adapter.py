from typing import Mapping, Any
from mantis.runtime.interfaces import (
    BankingRuntimeAdapter, BankingSystemInventory, WorkflowSpec, 
    ExperimentConfig, HookBus, RuntimeHandle
)

class LegacyBankingHandle:
    def __init__(self, mcp_session=None, mcp_tools=None, hooks: HookBus = None, config: ExperimentConfig = None):
        self.mcp_session = mcp_session
        self.mcp_tools = mcp_tools
        self.hooks = hooks
        self.config = config

    async def run_message(self, message: str) -> Any:
        # Wrap the legacy runner execution. For WP3 we pass the HookBus.
        from mantis.banking.runner import run_message
        from mantis.runtime.plugin import MantisHookPlugin
        plugin = MantisHookPlugin(
            self.hooks, 
            run_id=self.config.experiment.name if self.config else "default",
            workflow_id=self.config.experiment.workflow if self.config else "default"
        )
        return await run_message(
            message,
            mcp_session=self.mcp_session,
            mcp_tools=self.mcp_tools,
            compact=True,
            mantis_plugin=plugin
        )

class NativeBankingAdapter:
    def __init__(self, mcp_session=None, mcp_tools=None):
        self.mcp_session = mcp_session
        self.mcp_tools = mcp_tools

    def inventory(self) -> BankingSystemInventory:
        # In WP1, we just return a stub or parse the yaml.
        return BankingSystemInventory(
            agents=["user_proxy_agent", "front_office_router", "mid_office_router", "back_office_router"],
            tools=["execute_transfer", "submit_manual_review"],
            workflows=["front_office_monitoring", "mid_office_planning", "back_office_clean"]
        )

    def workflows(self) -> Mapping[str, WorkflowSpec]:
        return {
            "front_office_monitoring": WorkflowSpec(id="front_office_monitoring", description="Transaction review"),
            "mid_office_planning": WorkflowSpec(id="mid_office_planning", description="Ops planning"),
            "back_office_clean": WorkflowSpec(id="back_office_clean", description="EOD recon")
        }

    def build(self, config: ExperimentConfig, hooks: HookBus) -> RuntimeHandle:
        # Returns a handle that can execute the chosen workflow.
        return LegacyBankingHandle(mcp_session=self.mcp_session, mcp_tools=self.mcp_tools, hooks=hooks, config=config)

    def reset(self, seed: int) -> None:
        pass
