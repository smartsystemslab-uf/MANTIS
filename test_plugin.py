import asyncio
import os
from mantis.config.models import ExperimentConfig
from mantis.core.registry import scenario_registry
from mantis.runtime.adapter import NativeBankingAdapter
from mantis.core.hooks import HookBus

async def main():
    os.environ["OPENAI_API_KEY"] = "mock"
    config = ExperimentConfig(**{
        "experiment": {
            "name": "test",
            "domain": "test",
            "workflow": "test",
            "scenario": "front_office_monitoring"
        }
    })
    
    # Do not start MCP tools, just pure ADK
    adapter = NativeBankingAdapter(mcp_session=None, mcp_tools=None)
    hooks = HookBus()
    handle = adapter.build(config, hooks)
    
    prompt = scenario_registry.get("front_office_monitoring")
    print("Running...")
    res = await handle.run_message(prompt)
    print("Success")

if __name__ == "__main__":
    asyncio.run(main())
