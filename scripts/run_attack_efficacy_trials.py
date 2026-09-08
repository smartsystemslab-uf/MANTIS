#!/usr/bin/env python3
"""run_attack_efficacy_trials.py

Closes the "repeated-trial attack efficacy" gap: previous evidence for each
attack/failure plugin was exactly one live-model trial (see the paper's
Table on live-verified evidence). This script re-runs each configuration
N times against a real model, evaluates each run, and reports the
fired-rate and effect-detected-rate as a real distribution (mean + how many
of N), rather than a single anecdote.

Requires the banking backend running on 127.0.0.1:8000 and a real
UF_NAVIGATOR_API_KEY in the environment (no MANTIS_MOCK_LLM here --
a deterministic mock cannot characterize live-model variance, which is
the whole point of this measurement; see docs/reproducibility.md).

Usage:
    python scripts/run_attack_efficacy_trials.py --trials 5
"""
import argparse
import json
import statistics
import subprocess
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
MANTIS = [sys.executable, "-m", "mantis.cli.main"]

CONFIGS = [
    "configs/attacks/wp5_prompt_injection.yaml",
    "configs/attacks/wp5_message_spoofing.yaml",
    "configs/attacks/wp5_route_confusion.yaml",
    "configs/attacks/wp5_tool_mutation.yaml",
    "configs/attacks/wp5_back_office_tool_mutation.yaml",
    "configs/attacks/wp5_failure_malformed.yaml",
]


def run_one_trial(config_path: str) -> dict:
    run_result = subprocess.run(
        MANTIS + ["--run", config_path],
        cwd=str(REPO_ROOT), capture_output=True, text=True, timeout=180,
    )
    if run_result.returncode != 0:
        return {"run_ok": False, "error": run_result.stderr[-800:]}

    # experiment.name == run_artifacts dir name for every config in CONFIGS
    import yaml
    with open(REPO_ROOT / config_path) as f:
        run_name = yaml.safe_load(f)["experiment"]["name"]
    run_dir = REPO_ROOT / "run_artifacts" / run_name

    eval_result = subprocess.run(
        MANTIS + ["--evaluate", str(run_dir)],
        cwd=str(REPO_ROOT), capture_output=True, text=True, timeout=60,
    )
    if eval_result.returncode != 0:
        return {"run_ok": True, "eval_ok": False, "error": eval_result.stderr[-800:]}

    results = json.loads(eval_result.stdout)
    gt = results.get("attack_ground_truth", {})
    return {
        "run_ok": True,
        "eval_ok": True,
        "attack_fired": gt.get("attack_fired"),
        "effect_detected": gt.get("effect_detected_vs_ground_truth"),
        "trace_completeness": results.get("trace_completeness", {}).get("score"),
        "workflow_outcome_score": results.get("workflow_outcome", {}).get("score"),
        "actual_outcome": results.get("workflow_outcome", {}).get("actual_outcome"),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--trials", type=int, default=5)
    parser.add_argument("--configs", nargs="*", default=CONFIGS)
    args = parser.parse_args()

    summary = {}
    for config_path in args.configs:
        name = Path(config_path).stem
        print(f"\n=== {name} ({args.trials} trials) ===")
        trials = []
        for i in range(args.trials):
            t0 = time.time()
            trial = run_one_trial(config_path)
            trial["latency_s"] = round(time.time() - t0, 2)
            trials.append(trial)
            status = "fired" if trial.get("attack_fired") else "NOT FIRED"
            effect = "effect" if trial.get("effect_detected") else "no effect"
            print(f"  trial {i+1}: {status}, {effect}, {trial['latency_s']}s")

        fired = [t.get("attack_fired") for t in trials if t.get("eval_ok")]
        effect = [t.get("effect_detected") for t in trials if t.get("eval_ok")]
        latencies = [t["latency_s"] for t in trials]
        summary[name] = {
            "trials": trials,
            "n": len(trials),
            "n_ok": len(fired),
            "fired_rate": sum(bool(f) for f in fired) / len(fired) if fired else None,
            "effect_rate": sum(bool(e) for e in effect) / len(effect) if effect else None,
            "mean_latency_s": round(statistics.mean(latencies), 2),
            "stdev_latency_s": round(statistics.stdev(latencies), 2) if len(latencies) >= 2 else 0.0,
        }

    out_path = REPO_ROOT / "results" / "attack_efficacy_trials.json"
    out_path.write_text(json.dumps(summary, indent=2))

    print("\n\n=== SUMMARY ===")
    for name, s in summary.items():
        print(f"{name}: fired {s['fired_rate']*100:.0f}% ({s['n_ok']}/{s['n']}), "
              f"effect detected {s['effect_rate']*100:.0f}% of trials, "
              f"latency {s['mean_latency_s']}s (sigma {s['stdev_latency_s']}s)")
    print(f"\nWritten to {out_path}")


if __name__ == "__main__":
    main()
