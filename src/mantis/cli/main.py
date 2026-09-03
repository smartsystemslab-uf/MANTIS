import argparse
import asyncio
import json
import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
import yaml

from mantis.runtime.adapter import NativeBankingAdapter
from mantis.runtime.interfaces import HookBus
from mantis.config.models import ExperimentConfig
from mantis.core.registry import scenario_registry, plugin_registry
from mantis.observability.artifacts import create_run_manifest

def _ser(obj):
    try:
        return json.loads(json.dumps(obj, default=str))
    except Exception:
        return str(obj)

async def run_experiment(config_path: str):
    with open(config_path, "r") as f:
        config_data = yaml.safe_load(f)
    
    config = ExperimentConfig(**config_data)
    scenario_id = config.experiment.scenario
    
    try:
        prompt = scenario_registry.get(scenario_id)
    except KeyError:
        print(f"❌ Unknown scenario '{scenario_id}'. Available: {list(scenario_registry.all().keys())}", file=sys.stderr)
        sys.exit(1)

    output_dir = Path("run_artifacts") / config.experiment.name
    manifest_path = create_run_manifest(config, output_dir)
    print(f"Run manifest saved to {manifest_path}", file=sys.stderr)

    server_path = Path.cwd() / "citi_banking_mcp_server" / "mcp_server.py"
    if not server_path.exists():
        server_path = Path.cwd().parent / "citi_banking_mcp_server" / "mcp_server.py"
        if not server_path.exists():
             server_path = Path.cwd() / "legacy_code" / "citi_banking_mcp_server" / "mcp_server.py"

    server_params = StdioServerParameters(
        command=sys.executable,
        args=[str(server_path)],
        env=os.environ.copy()
    )

    try:
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                tools_response = await session.list_tools()
                
                adapter = NativeBankingAdapter(mcp_session=session, mcp_tools=tools_response.tools)
                
                # Setup HookBus and register plugins
                hooks = HookBus()
                if config.attack and config.attack.plugin:
                    try:
                        plugin_cls = plugin_registry.get(config.attack.plugin)
                        plugin_instance = plugin_cls(**config.attack.parameters)
                        hooks.register(plugin_instance)
                    except Exception as e:
                        print(f"❌ Failed to load plugin {config.attack.plugin}: {e}", file=sys.stderr)
                        sys.exit(1)

                handle = adapter.build(config, hooks)
                
                res = await handle.run_message(prompt)
                
                # Write coverage report
                hooks.write_coverage(str(output_dir / "hook_coverage.json"))
                
                print(json.dumps({scenario_id: _ser(res)}, indent=2, ensure_ascii=False))

    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"❌ Failed to connect to MCP Server: {e}", file=sys.stderr)
        sys.exit(1)

def generate_schemas():
    schema = ExperimentConfig.model_json_schema()
    out_dir = Path("configs")
    out_dir.mkdir(exist_ok=True)
    out_file = out_dir / "experiment_schema.json"
    with open(out_file, "w") as f:
        json.dump(schema, f, indent=2)
    print(f"Schema successfully generated at {out_file}")

def main():
    load_dotenv()
    ap = argparse.ArgumentParser()
    ap.add_argument('--run', type=str, help='Run experiment from YAML configuration file')
    ap.add_argument('--generate-schemas', action='store_true', help='Generate JSON schemas for the configuration models')
    ap.add_argument('--inventory', action='store_true', help='Print system inventory')
    args = ap.parse_args()
    
    if args.inventory:
        adapter = NativeBankingAdapter()
        inv = adapter.inventory()
        print(json.dumps(inv.model_dump(), indent=2))
        return

    if args.generate_schemas:
        generate_schemas()
        return

    if args.run:
        if not Path(args.run).exists():
            print(f"❌ Configuration file not found: {args.run}", file=sys.stderr)
            sys.exit(1)
        asyncio.run(run_experiment(args.run))
        return
        
    ap.print_help()

if __name__ == '__main__':
    main()
