import argparse
import asyncio
import json
import os
import sys
from pathlib import Path
import yaml

# --------------------------------------------------------------------------
# Lightweight imports only. Heavy dependencies (google.adk, mcp, mlflow,
# banking runtime) are lazy-imported inside the functions that need them so
# that purely structural CLI commands (--help, --inventory, --generate-schemas,
# --evaluate) work even when the full ADK stack is not installed (e.g. CI).
# --------------------------------------------------------------------------
from mantis.config.models import ExperimentConfig, ObservabilityConfig
from mantis.core.registry import scenario_registry, plugin_registry

def _ser(obj):
    try:
        return json.loads(json.dumps(obj, default=str))
    except Exception:
        return str(obj)

async def run_experiment(config_path: str):
    # Lazy imports — these pull in google.adk, mcp, mlflow etc.
    from dotenv import load_dotenv
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client
    from mantis.runtime.adapter import NativeBankingAdapter
    from mantis.runtime.interfaces import HookBus
    from mantis.observability.artifacts import create_run_manifest, TraceArtifactWriter
    from mantis.observability.plugin import ObservabilityPlugin
    from mantis.observability.otel import setup_otel
    from mantis.observability.mlflow_exporter import MLflowExporter

    load_dotenv()

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
                
                obs_config = config.observability or ObservabilityConfig()
                if obs_config.mode != "off":
                    trace_writer = TraceArtifactWriter(str(output_dir))
                    obs_plugin = ObservabilityPlugin(trace_writer)
                    hooks.register(obs_plugin)
                    
                    if "mlflow" in obs_config.export:
                        mlflow_exporter = MLflowExporter()
                        # Use directory name as config_hash for now, since manifest path is generated
                        mlflow_exporter.start_run(
                            run_name=config.experiment.name,
                            config_hash=output_dir.name,
                            seed=config.experiment.seed
                        )
                    else:
                        mlflow_exporter = None
                        
                    if "otel" in obs_config.export:
                        setup_otel(service_name=f"mantis-{config.experiment.name}")

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
                
                if obs_config.mode != "off" and "mlflow" in obs_config.export and mlflow_exporter:
                    mlflow_exporter.log_artifact(str(output_dir / "traces.jsonl"))
                    mlflow_exporter.end_run()
                
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
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass  # dotenv is optional for CI

    ap = argparse.ArgumentParser(prog="mantis", description="MANTIS - Multi-Agent Network Testbed for Instrumentation and Security")
    ap.add_argument('--run', type=str, help='Run experiment from YAML configuration file')
    ap.add_argument('--generate-schemas', action='store_true', help='Generate JSON schemas for the configuration models')
    ap.add_argument('--inventory', action='store_true', help='Print system inventory')
    ap.add_argument('--evaluate', type=str, help='Evaluate a completed run artifact directory')
    ap.add_argument('--benchmark', type=str, help='Run benchmark on a config file')
    ap.add_argument('--campaign', type=str, help='Run a campaign on a directory of configs')
    ap.add_argument('--report', type=str, help='Generate a markdown report for a campaign directory')
    args = ap.parse_args()
    
    if args.inventory:
        from mantis.runtime.adapter import NativeBankingAdapter
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

    if args.evaluate:
        if not Path(args.evaluate).exists():
            print(f"❌ Run directory not found: {args.evaluate}", file=sys.stderr)
            sys.exit(1)
        from mantis.evaluation.evaluators import TraceEvaluator
        evaluator = TraceEvaluator(args.evaluate)
        results = evaluator.evaluate_all()
        print(json.dumps(results, indent=2))
        
        # Save evaluation results in the same directory
        with open(Path(args.evaluate) / "evaluation_results.json", "w") as f:
            json.dump(results, f, indent=2)
        return

    if args.benchmark:
        if not Path(args.benchmark).exists():
            print(f"❌ Configuration file not found: {args.benchmark}", file=sys.stderr)
            sys.exit(1)
        from mantis.benchmark.runner import BenchmarkRunner
        runner = BenchmarkRunner(args.benchmark)
        results = runner.execute()
        print(json.dumps(results, indent=2))
        
        # Save benchmark results
        out_dir = Path("results")
        out_dir.mkdir(exist_ok=True)
        out_file = out_dir / f"benchmark_{Path(args.benchmark).stem}.json"
        with open(out_file, "w") as f:
            json.dump(results, f, indent=2)
        print(f"Benchmark results saved to {out_file}")
        return

    if args.campaign:
        if not Path(args.campaign).exists():
            print(f"❌ Campaign directory not found: {args.campaign}", file=sys.stderr)
            sys.exit(1)
        from mantis.cli.campaign import CampaignManager
        manager = CampaignManager(args.campaign)
        asyncio.run(manager.execute_campaign())
        return
        
    if args.report:
        if not Path(args.report).exists():
            print(f"❌ Report directory not found: {args.report}", file=sys.stderr)
            sys.exit(1)
        from mantis.cli.campaign import CampaignManager
        manager = CampaignManager("")
        manager.output_dir = Path(args.report)
        manager.generate_report()
        return
        
    ap.print_help()

if __name__ == '__main__':
    main()
