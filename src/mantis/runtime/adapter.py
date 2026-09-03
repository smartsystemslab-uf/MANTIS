import inspect
import random
from typing import Mapping, Any
from mantis.runtime.interfaces import (
    BankingRuntimeAdapter, BankingSystemInventory, WorkflowSpec,
    ExperimentConfig, HookBus, RuntimeHandle
)
from mantis.core.registry import domain_registry, scenario_registry

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
            workflow_id=self.config.experiment.workflow if self.config else "default",
            domain=self.config.experiment.domain if self.config else None,
            scenario=self.config.experiment.scenario if self.config else None,
        )
        return await run_message(
            message,
            mcp_session=self.mcp_session,
            mcp_tools=self.mcp_tools,
            compact=True,
            mantis_plugin=plugin
        )

# Tool modules that make up the real banking tool surface. Listed here (not
# discovered via package scanning) so inventory() has a stable, explicit set
# of modules to introspect -- adding a new tools/*.py file means adding one
# line here, not touching the CLI or the registries.
_TOOL_MODULE_PATHS = [
    "mantis.banking.tools.customer_tools",
    "mantis.banking.tools.csr_tools",
    "mantis.banking.tools.knowledge_tools",
    "mantis.banking.tools.ops_tools",
    "mantis.banking.tools.back_office_tools",
]

# Not a banking tool -- ADK auto-generates this on every agent that has
# sub_agents, to hand a request off to a specialist. It shows up in every
# trace and is a legitimate attack/inspection target (e.g. route confusion).
_ADK_BUILTIN_TOOLS = ["transfer_to_agent"]


def _discover_banking_tools() -> list[str]:
    """Introspect the real tool modules for public, module-local functions.

    Deliberately avoids importing google.adk: these tool modules only pull in
    the banking backend client, so this stays safe to call from lightweight
    CLI paths (--inventory, --validate) that must work without the full ADK
    stack installed.
    """
    import importlib
    tools: list[str] = []
    for module_path in _TOOL_MODULE_PATHS:
        module = importlib.import_module(module_path)
        for name, obj in inspect.getmembers(module, inspect.isfunction):
            if name.startswith("_"):
                continue
            if obj.__module__ != module_path:
                continue  # skip re-exported/imported helpers (e.g. rank_records)
            tools.append(name)
    return sorted(set(tools))


class NativeBankingAdapter:
    def __init__(self, mcp_session=None, mcp_tools=None):
        self.mcp_session = mcp_session
        self.mcp_tools = mcp_tools

    def inventory(self) -> BankingSystemInventory:
        tools = sorted(set(_discover_banking_tools()) | set(_ADK_BUILTIN_TOOLS))
        domains: dict[str, dict[str, list[str]]] = {}
        all_agents: list[str] = []
        for domain_name, entry in domain_registry.all().items():
            domain_agents = list(entry.get("agents", []))
            all_agents.extend(domain_agents)
            domains[domain_name] = {"agents": domain_agents, "tools": []}
        # Tools aren't domain-tagged individually (they're shared banking
        # backend calls); attach the full tool list under each domain too so
        # "inventory by domain" still surfaces what that domain can call.
        for domain_name in domains:
            domains[domain_name]["tools"] = tools

        return BankingSystemInventory(
            agents=sorted(set(all_agents)),
            tools=tools,
            workflows=sorted(scenario_registry.all().keys()),
            domains=domains,
        )

    def workflows(self) -> Mapping[str, WorkflowSpec]:
        return {
            scenario_id: WorkflowSpec(id=scenario_id, description=prompt)
            for scenario_id, prompt in scenario_registry.all().items()
        }

    def build(self, config: ExperimentConfig, hooks: HookBus) -> RuntimeHandle:
        # Returns a handle that can execute the chosen workflow.
        return LegacyBankingHandle(mcp_session=self.mcp_session, mcp_tools=self.mcp_tools, hooks=hooks, config=config)

    def reset(self, seed: int) -> None:
        random.seed(seed)
        # Lazy import: mantis.banking.llm pulls in google.adk.models.lite_llm,
        # which must stay out of lightweight CLI paths that call reset()
        # only as part of a full --run (never --validate/--inventory).
        from mantis.banking.llm import set_seed
        set_seed(seed)
