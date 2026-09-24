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
import os
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


# Tables a workflow can write to (plus the two whose *status* a workflow
# updates). Snapshotting them after a trial run against a freshly re-seeded
# database (--reset-db) shows exactly what state the run changed -- the
# data-level effect that tool-use and terminal-state scoring cannot see (a
# loan filed against the wrong customer still "called submit_loan_application").
_WRITE_TABLES = [
    "loan_applications", "sar_reports", "disputes", "manual_reviews",
    "saved_schedules", "reports", "exceptions", "eod_batches",
]
_VOLATILE_COLUMNS = {"created_at", "notes_json"}


def _db_snapshot(runtime_dir: str) -> dict:
    import sqlite3
    snapshot = {}
    for db in sorted(Path(runtime_dir).glob("banking*.db")):
        conn = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
        conn.row_factory = sqlite3.Row
        try:
            for table in _WRITE_TABLES:
                try:
                    rows = [dict(r) for r in conn.execute(f"SELECT * FROM {table}")]
                except sqlite3.Error:
                    continue
                # Seeded reference rows are constant across trials, so drop the
                # volatile columns and keep only what identifies each row.
                snapshot[table] = [
                    {k: (v[:120] if isinstance(v, str) else v) for k, v in row.items() if k not in _VOLATILE_COLUMNS}
                    for row in rows
                ]
        finally:
            conn.close()
    return snapshot


def _policy_events(run_dir: Path) -> dict:
    """How many times each defense plugin acted in this run: {plugin: {action: n}}.
    Read from the trace's POLICY_EVENT records, so a defense's effect is
    counted from evidence rather than inferred from the run's outcome."""
    counts = {}
    trace = run_dir / "traces.jsonl"
    if not trace.exists():
        return counts
    for line in trace.read_text().splitlines():
        try:
            e = json.loads(line)
        except ValueError:
            continue
        if e.get("event_type") == "POLICY_EVENT":
            by_action = counts.setdefault(e.get("plugin", "unknown"), {})
            by_action[e.get("observed_impact")] = by_action.get(e.get("observed_impact"), 0) + 1
    return counts


def run_one_trial(config_path: str, runtime_dir: str = None, reset_db: bool = False) -> dict:
    env = os.environ.copy()
    if runtime_dir:
        # An isolated SQLite location for this worker (BANKING_ADK_RUNTIME_DIR
        # is read by mantis.banking.settings), so parallel workers never share
        # local state and a reset never touches another worker's database.
        env["BANKING_ADK_RUNTIME_DIR"] = runtime_dir
        Path(runtime_dir).mkdir(parents=True, exist_ok=True)
    if reset_db and runtime_dir:
        # Trials in a campaign otherwise inherit the previous trial's local
        # state (batch statuses, filed cases); a fresh, re-seeded database per
        # trial makes each one independent.
        for db in Path(runtime_dir).glob("banking*.db"):
            db.unlink()
    run_result = subprocess.run(
        MANTIS + ["--run", config_path],
        cwd=str(REPO_ROOT), capture_output=True, text=True, timeout=240, env=env,
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
    tool_use = results.get("tool_use_correctness", {})
    return {
        "run_ok": True,
        "eval_ok": True,
        # Baseline (no-attack) configs report attack_ground_truth as not
        # applicable rather than as a score -- keep that distinct from
        # "applicable but the attack did not fire".
        "attack_applicable": gt.get("applicable", False),
        "attack_fired": gt.get("attack_fired"),
        "effect_detected": gt.get("effect_detected_vs_ground_truth"),
        "trace_completeness": results.get("trace_completeness", {}).get("score"),
        "workflow_outcome_score": results.get("workflow_outcome", {}).get("score"),
        "actual_outcome": results.get("workflow_outcome", {}).get("actual_outcome"),
        "tool_use_score": tool_use.get("score"),
        "actual_tools": sorted(tool_use.get("actual_tools") or []),
        "missing_expected": tool_use.get("missing_expected"),
        "used_forbidden": tool_use.get("used_forbidden"),
        "policy_events": _policy_events(run_dir),
        "db_snapshot": _db_snapshot(runtime_dir) if (runtime_dir and reset_db) else None,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--trials", type=int, default=5)
    parser.add_argument("--configs", nargs="*", default=CONFIGS)
    parser.add_argument(
        "--output", default="results/attack_efficacy_trials.json",
        help="Where to write the summary (relative to the repo root). Defaults to the file "
             "Paper 1's Table cites -- pass a different path for any other campaign so that "
             "evidence is not overwritten.",
    )
    parser.add_argument("--retries", type=int, default=0,
                        help="Re-run a trial whose *process* failed (crash before any evaluation) up to N more times. "
                             "Every attempt is recorded (attempts / failed_attempts) so infrastructure failures stay visible "
                             "instead of silently disappearing; a trial that ran and simply did the wrong thing is never retried.")
    parser.add_argument("--runtime-dir", default=None, help="Isolated local-database directory for this worker.")
    parser.add_argument("--reset-db", action="store_true", help="Delete and re-seed the local database before every trial (needs --runtime-dir).")
    args = parser.parse_args()
    if args.reset_db and not args.runtime_dir:
        parser.error("--reset-db requires --runtime-dir so it can never delete the shared default database")

    summary = {}
    for config_path in args.configs:
        name = Path(config_path).stem
        print(f"\n=== {name} ({args.trials} trials) ===")
        trials = []
        for i in range(args.trials):
            t0 = time.time()
            trial = run_one_trial(config_path, args.runtime_dir, args.reset_db)
            failed_attempts = []
            while not trial.get("run_ok") and len(failed_attempts) < args.retries:
                failed_attempts.append((trial.get("error") or "")[-300:])
                trial = run_one_trial(config_path, args.runtime_dir, args.reset_db)
            trial["attempts"] = 1 + len(failed_attempts)
            if failed_attempts:
                trial["failed_attempts"] = failed_attempts
            trial["latency_s"] = round(time.time() - t0, 2)
            trials.append(trial)
            if not trial.get("eval_ok"):
                print(f"  trial {i+1}: RUN/EVAL FAILED, {trial['latency_s']}s")
                continue
            if trial.get("attack_applicable"):
                status = "fired" if trial.get("attack_fired") else "NOT FIRED"
                effect = "effect" if trial.get("effect_detected") else "no effect"
                print(f"  trial {i+1}: {status}, {effect}, {trial['latency_s']}s")
            else:
                print(f"  trial {i+1}: baseline (no attack), outcome={trial.get('actual_outcome')}, "
                      f"tools={trial.get('actual_tools')}, {trial['latency_s']}s")

        ok = [t for t in trials if t.get("eval_ok")]
        applicable = [t for t in ok if t.get("attack_applicable")]
        fired = [t.get("attack_fired") for t in applicable]
        effect = [t.get("effect_detected") for t in applicable]
        latencies = [t["latency_s"] for t in trials]
        tool_counts = {}
        outcome_counts = {}
        for t in ok:
            for tool in t.get("actual_tools") or []:
                tool_counts[tool] = tool_counts.get(tool, 0) + 1
            outcome_counts[t.get("actual_outcome")] = outcome_counts.get(t.get("actual_outcome"), 0) + 1
        summary[name] = {
            "trials": trials,
            "n": len(trials),
            "n_ok": len(ok),
            "process_failures": sum(len(t.get("failed_attempts", [])) + (0 if t.get("run_ok") else 1) for t in trials),
            "fired_rate": sum(bool(f) for f in fired) / len(fired) if fired else None,
            "effect_rate": sum(bool(e) for e in effect) / len(effect) if effect else None,
            "tool_use_pass_rate": (sum(t.get("tool_use_score") == 1.0 for t in ok) / len(ok)) if ok else None,
            "tool_frequency": dict(sorted(tool_counts.items())),
            "outcome_counts": outcome_counts,
            "mean_latency_s": round(statistics.mean(latencies), 2),
            "stdev_latency_s": round(statistics.stdev(latencies), 2) if len(latencies) >= 2 else 0.0,
        }

    out_path = REPO_ROOT / args.output
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(summary, indent=2))

    def _pct(x):
        return "n/a" if x is None else f"{x*100:.0f}%"

    print("\n\n=== SUMMARY ===")
    for name, s in summary.items():
        print(f"{name}: fired {_pct(s['fired_rate'])} ({s['n_ok']}/{s['n']} ok), "
              f"effect detected {_pct(s['effect_rate'])}, tool-use pass {_pct(s['tool_use_pass_rate'])}, "
              f"outcomes {s['outcome_counts']}, latency {s['mean_latency_s']}s (sigma {s['stdev_latency_s']}s)")
    print(f"\nWritten to {out_path}")


if __name__ == "__main__":
    main()
