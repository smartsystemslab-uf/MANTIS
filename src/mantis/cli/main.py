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
from mantis.core.registry import scenario_registry, plugin_registry, domain_registry, workflow_registry

VALID_CONTROL_POINTS = {"input", "agent", "interaction", "tool", "output"}

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
                adapter.reset(config.experiment.seed)

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

def validate_config(config_path: str) -> bool:
    path = Path(config_path)
    if not path.exists():
        print(f"❌ Configuration file not found: {config_path}", file=sys.stderr)
        return False
    try:
        with open(path, "r") as f:
            data = yaml.safe_load(f)
        cfg = ExperimentConfig(**data)
        if cfg.experiment.domain not in domain_registry.all():
            print(f"❌ Unknown domain '{cfg.experiment.domain}'. Available: {list(domain_registry.all().keys())}", file=sys.stderr)
            return False
        if cfg.experiment.workflow not in workflow_registry.all():
            print(f"❌ Unknown workflow '{cfg.experiment.workflow}'. Available: {list(workflow_registry.all().keys())}", file=sys.stderr)
            return False
        if cfg.experiment.scenario not in scenario_registry.all():
            print(f"❌ Unknown scenario '{cfg.experiment.scenario}' in registry.", file=sys.stderr)
            return False
        if cfg.attack:
            if cfg.attack.plugin not in plugin_registry.all():
                print(f"❌ Unknown attack plugin '{cfg.attack.plugin}' in registry.", file=sys.stderr)
                return False
            if cfg.attack.control_point not in VALID_CONTROL_POINTS:
                print(f"❌ Unknown control_point '{cfg.attack.control_point}'. Must be one of: {sorted(VALID_CONTROL_POINTS)}", file=sys.stderr)
                return False
            from mantis.runtime.adapter import NativeBankingAdapter
            inv = NativeBankingAdapter().inventory()
            valid_targets = set(inv.agents) | set(inv.tools)
            if cfg.attack.target not in valid_targets:
                print(f"❌ Unknown attack target '{cfg.attack.target}'. Must be a known agent or tool.", file=sys.stderr)
                return False
        print(f"✅ Configuration '{config_path}' is valid (Experiment: {cfg.experiment.name}, Scenario: {cfg.experiment.scenario}).")
        return True
    except Exception as e:
        print(f"❌ Validation failed for '{config_path}': {e}", file=sys.stderr)
        return False

def inspect_target(target: str):
    p = Path(target)
    if p.exists() and p.is_file():
        with open(p, "r") as f:
            data = yaml.safe_load(f)
        cfg = ExperimentConfig(**data)
        out = {
            "type": "configuration",
            "name": cfg.experiment.name,
            "domain": cfg.experiment.domain,
            "workflow": cfg.experiment.workflow,
            "scenario": cfg.experiment.scenario,
            "seed": cfg.experiment.seed,
            "attack": cfg.attack.model_dump() if cfg.attack else None,
            "observability": cfg.observability.model_dump() if cfg.observability else None,
            "modifications": cfg.modifications.model_dump() if cfg.modifications else None
        }
        print(json.dumps(out, indent=2))
        return

    scenarios = scenario_registry.all()
    if target in scenarios:
        out = {
            "type": "registered_scenario",
            "scenario_id": target,
            "prompt": scenarios[target]
        }
        print(json.dumps(out, indent=2))
        return

    plugins = plugin_registry.all()
    if target in plugins:
        cls = plugins[target]
        out = {
            "type": "registered_plugin",
            "plugin_id": target,
            "class": cls.__name__,
            "supported_stages": list(getattr(cls, "supported_stages", []))
        }
        print(json.dumps(out, indent=2, default=str))
        return

    print(f"❌ Target '{target}' is not a valid file, registered scenario, or registered plugin.", file=sys.stderr)
    sys.exit(1)

def init_workspace(target_dir: str):
    p = Path(target_dir)
    p.mkdir(parents=True, exist_ok=True)
    configs_dir = p / "configs"
    configs_dir.mkdir(exist_ok=True)
    (p / "run_artifacts").mkdir(exist_ok=True)
    sample_cfg = configs_dir / "sample_experiment.yaml"
    with open(sample_cfg, "w") as f:
        f.write("""experiment:
  name: sample_front_office_run
  seed: 42
  domain: front_office
  workflow: front_office_monitoring
  scenario: front_office_monitoring

observability:
  mode: full
  export:
    - jsonl
""")
    print(f"✅ MANTIS workspace initialized at '{target_dir}' with template config: {sample_cfg}")

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
    ap.add_argument('--validate', type=str, help='Validate experiment YAML configuration file against schema')
    ap.add_argument('--inspect', type=str, help='Inspect a YAML config, registered scenario, or plugin')
    ap.add_argument('--init', type=str, help='Initialize a new MANTIS workspace with sample templates')
    ap.add_argument('--generate-schemas', action='store_true', help='Generate JSON schemas for the configuration models')
    ap.add_argument('--inventory', action='store_true', help='Print system inventory')
    ap.add_argument('--evaluate', type=str, help='Evaluate a completed run artifact directory')
    ap.add_argument('--benchmark', type=str, help='Run benchmark on a config file')
    ap.add_argument('--campaign', type=str, help='Run a campaign on a directory of configs')
    ap.add_argument('--report', type=str, help='Generate a markdown report for a campaign directory')
    args = ap.parse_args()

    if args.validate:
        valid = validate_config(args.validate)
        sys.exit(0 if valid else 1)

    if args.inspect:
        inspect_target(args.inspect)
        return

    if args.init:
        init_workspace(args.init)
        return
    
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
        from mantis.observability.events import EventType, EvaluationEvent
        from mantis.observability.artifacts import append_trace_events
        evaluator = TraceEvaluator(args.evaluate)
        results = evaluator.evaluate_all()
        print(json.dumps(results, indent=2))

        # Save evaluation results in the same directory
        with open(Path(args.evaluate) / "evaluation_results.json", "w") as f:
            json.dump(results, f, indent=2)

        if "error" not in results:
            run_id = Path(args.evaluate).name
            eval_events = [
                EvaluationEvent(
                    event_type=EventType.EVALUATION_RESULT,
                    run_id=run_id,
                    evaluator="TraceEvaluator",
                    metric=metric_name,
                    score=metric_result.get("score", 0.0),
                    evidence_ref="evaluation_results.json",
                )
                for metric_name, metric_result in results.items()
                if isinstance(metric_result, dict) and "score" in metric_result
            ]
            append_trace_events(args.evaluate, eval_events)
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
