import asyncio
import os
import shutil
import subprocess
import time
from pathlib import Path
import yaml
from mantis.evaluation.evaluators import TraceEvaluator
from mantis.config.models import ExperimentConfig

class CampaignManager:
    def __init__(self, campaign_dir: str):
        self.campaign_dir = Path(campaign_dir)
        self.timestamp = int(time.time())
        self.output_dir = Path("run_artifacts") / f"campaign_run_{self.timestamp}"

    @staticmethod
    def _run_name_for(config_path: Path) -> str:
        # mantis --run writes to run_artifacts/<experiment.name>/, which is
        # not always the config's own filename stem (e.g. every file under
        # configs/baselines/ names its experiment after the workflow it
        # exercises, not after "<domain>_baseline") -- reading the real name
        # out of the parsed config is the only way to find that directory
        # again for aggregation. Falls back to the filename stem so one
        # malformed config can't stop the whole campaign from aggregating.
        try:
            with open(config_path, "r") as f:
                data = yaml.safe_load(f)
            return ExperimentConfig(**data).experiment.name
        except Exception:
            return config_path.stem

    async def execute_campaign(self):
        if not self.campaign_dir.exists() or not self.campaign_dir.is_dir():
            print(f"❌ Campaign directory not found: {self.campaign_dir}")
            return

        self.output_dir.mkdir(parents=True, exist_ok=True)
        configs = list(self.campaign_dir.glob("*.yaml")) + list(self.campaign_dir.glob("*.yml"))
        
        # Exclude benchmark configs to only run attacks in campaign
        configs = [c for c in configs if "benchmark" not in c.name]
        
        print(f"🚀 Starting Campaign Execution. Found {len(configs)} configs.")
        print(f"📁 Output Directory: {self.output_dir}")
        print("-" * 50)

        for idx, config_path in enumerate(configs, 1):
            print(f"[{idx}/{len(configs)}] Running {config_path.name}...")
            
            # Execute synchronously to ensure deterministic traces
            process = await asyncio.create_subprocess_exec(
                "mantis", "--run", str(config_path),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                print(f"❌ Error running {config_path.name}")
                print(stderr.decode())
            else:
                print(f"✅ Finished {config_path.name}")
                
        print("-" * 50)
        print("🎯 Campaign Execution Complete.")
        
        # We need to aggregate the artifacts that were dumped to
        # run_artifacts/<experiment.name> into our campaign output dir
        for config_path in configs:
            run_name = self._run_name_for(config_path)
            source_dir = Path("run_artifacts") / run_name
            if source_dir.exists() and source_dir.is_dir():
                dest_dir = self.output_dir / run_name
                shutil.copytree(source_dir, dest_dir, dirs_exist_ok=True)
            else:
                print(f"⚠️  Could not find output for {config_path.name} (expected run_artifacts/{run_name}/)")

        print(f"📊 Run `mantis --report {self.output_dir}` to view results.")

    def generate_report(self):
        if not self.output_dir.exists():
            print(f"❌ Campaign output directory not found: {self.output_dir}")
            return

        print("\n# 🛡️ MANTIS Security Campaign Report")
        print(f"**Directory**: `{self.output_dir}`\n")
        
        print("| Experiment | Completeness | Correctness | Status | Attack Effect |")
        print("|------------|--------------|-------------|--------|---------------|")

        for run_dir in self.output_dir.iterdir():
            if not run_dir.is_dir():
                continue

            evaluator = TraceEvaluator(str(run_dir))
            results = evaluator.evaluate_all()

            if "error" in results:
                print(f"| {run_dir.name} | N/A | N/A | ❌ ERR | N/A |")
                continue

            comp_score = results.get("trace_completeness", {}).get("score", 0.0)
            corr_score = results.get("tool_use_correctness", {}).get("score", 0.0)
            ground_truth = results.get("attack_ground_truth", {})

            # A low completeness/correctness score means something different
            # depending on whether this run has an attack configured: for a
            # baseline it means something broke; for an attack run whose
            # ground truth encodes the *undisturbed* baseline, it is often
            # the attack's intended effect being caught, not a defect. The
            # Status column alone conflated these -- Attack Effect makes the
            # distinction explicit rather than requiring a human to already
            # know which experiments in the sweep were attacks.
            if ground_truth.get("applicable"):
                fired = ground_truth.get("attack_fired")
                effect = ground_truth.get("effect_detected_vs_ground_truth")
                if fired and effect:
                    attack_effect = "⚔️ fired, effect detected"
                elif fired:
                    attack_effect = "⚔️ fired, no effect this trial"
                else:
                    attack_effect = "❌ did not fire"
            else:
                attack_effect = "n/a (baseline)"

            status = "✅ PASS" if (comp_score == 1.0 and corr_score == 1.0) else "⚠️ FAIL"

            print(f"| {run_dir.name} | {comp_score:.1f} | {corr_score:.1f} | {status} | {attack_effect} |")

        print("\n*Generated by the MANTIS CLI. For an attack-configured run, \"FAIL\" often means the attack's effect was correctly detected against the run's own ground truth, not that something broke -- see the Attack Effect column.*")
