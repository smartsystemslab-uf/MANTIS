#!/usr/bin/env python3
"""run_enforcement_trials.py -- deeper Zero Trust evidence (Post-Paper
Extension, coding plan §11).

zero_trust_demo.yaml (this directory's original evidence) is exactly one
live run showing zero DENYs on legitimate traffic -- a transparency
anecdote, not a statistic, and it never exercises the DENY path at all
(the shipped attack plugins mutate a tool call's *arguments*, never the
*tool name itself*; see enforcement_plugin.py -- an LLM agent structurally
cannot ask to call a tool outside its own ADK-declared tool list, so no
shipped attack can make a real agent attempt a genuine cross-domain call).
This script closes that gap two ways, both against real data:

1. Exhaustive enforcement matrix: every (agent, tool) pair implied by the
   live inventory (`generate_default_deny_policy()`, the same function
   `ZeroTrustEnforcementPlugin` itself uses) is fed through the *real*
   plugin's `apply()` -- not a mock -- and checked against the ground
   truth the policy's own domain scoping implies (allow iff the tool is
   in the agent's domain's allowed_tools or in always_allowed_tools).
   This is real repeated-trial evidence for the lateral-movement threat
   model the policy generator's own docstring names explicitly, at every
   combination the current live system actually has -- not a handful of
   hand-picked examples.
2. Live legitimate-traffic reliability: zero_trust_demo.yaml is run N
   times against a real model (through the Zero Trust wrapper, so
   enforcement is actually active), extending the original single-run
   transparency claim into an N-trial statistic: legitimate traffic
   produces zero DENYs in every trial, not just the one already recorded.

Usage:
    python -m extensions.zero_trust.run_enforcement_trials --trials 5
    python -m extensions.zero_trust.run_enforcement_trials --matrix-only
"""
import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

from mantis.hooks import HookContext, HookAction  # noqa: E402
from extensions.zero_trust.policy_generator import generate_default_deny_policy  # noqa: E402
from extensions.zero_trust.enforcement_plugin import ZeroTrustEnforcementPlugin  # noqa: E402


def run_enforcement_matrix(policy: dict = None) -> dict:
    """Exercise the real plugin against every (agent, tool) pair the live
    policy implies, plus a synthetic unrecognized-agent case per domain
    (an impersonator/compromised identity the generated policy has never
    seen), and check every decision against ground truth."""
    policy = policy or generate_default_deny_policy()
    plugin = ZeroTrustEnforcementPlugin(policy=policy)

    all_tools = sorted({t for d in policy["domains"].values() for t in d["allowed_tools"]})
    always_allowed = set(policy.get("always_allowed_tools", []))

    trials = []
    for domain, data in policy["domains"].items():
        domain_allowed = set(data["allowed_tools"])
        for agent in data["agents"]:
            for tool in all_tools:
                expected_allow = tool in domain_allowed or tool in always_allowed
                ctx = HookContext(
                    run_id="zt_enforcement_matrix", trace_id="t", workflow_id="w",
                    stage="tool", source=agent, target=tool, payload={},
                    metadata={"specific_hook": "before_tool"},
                )
                result = plugin.apply(ctx)
                actual_allow = result.action == HookAction.CONTINUE
                trials.append({
                    "agent": agent, "domain": domain, "tool": tool,
                    "expected_allow": expected_allow, "actual_allow": actual_allow,
                    "correct": expected_allow == actual_allow,
                })
        # Unrecognized/impersonator identity -- not in any domain's agent
        # list at all. Must be denied regardless of the tool requested.
        for tool in all_tools:
            ctx = HookContext(
                run_id="zt_enforcement_matrix", trace_id="t", workflow_id="w",
                stage="tool", source=f"impersonator_of_{domain}", target=tool, payload={},
                metadata={"specific_hook": "before_tool"},
            )
            result = plugin.apply(ctx)
            trials.append({
                "agent": f"impersonator_of_{domain}", "domain": None, "tool": tool,
                "expected_allow": tool in always_allowed, "actual_allow": result.action == HookAction.CONTINUE,
                "correct": (tool in always_allowed) == (result.action == HookAction.CONTINUE),
            })

    n = len(trials)
    n_correct = sum(t["correct"] for t in trials)
    cross_domain = [t for t in trials if not t["expected_allow"]]
    in_domain = [t for t in trials if t["expected_allow"]]
    return {
        "n_pairs_tested": n,
        "accuracy": n_correct / n if n else None,
        "n_correct": n_correct,
        "n_incorrect": n - n_correct,
        "cross_domain_deny_rate": (
            sum(not t["actual_allow"] for t in cross_domain) / len(cross_domain) if cross_domain else None
        ),
        "n_cross_domain_pairs": len(cross_domain),
        "in_domain_allow_rate": (
            sum(t["actual_allow"] for t in in_domain) / len(in_domain) if in_domain else None
        ),
        "n_in_domain_pairs": len(in_domain),
        "misclassified": [t for t in trials if not t["correct"]],
    }


def run_live_legitimate_traffic_trials(trials: int) -> dict:
    """Run zero_trust_demo.yaml `trials` times through the real Zero Trust
    wrapper against a live model, counting real ATTACK_INJECTED/DENY
    events (the observability plugin's ANOMALY records for a DENY) in each
    trial's trace -- extending the original single-run "zero DENYs on
    legitimate traffic" claim into an N-trial statistic."""
    config_path = REPO_ROOT / "configs" / "extensions" / "zero_trust_demo.yaml"
    run_dir = REPO_ROOT / "run_artifacts" / "zero_trust_demo"
    cmd = [sys.executable, "-m", "extensions.zero_trust.run_with_zero_trust", "--run", str(config_path)]

    results = []
    for i in range(trials):
        t0 = time.time()
        proc = subprocess.run(cmd, cwd=str(REPO_ROOT), capture_output=True, text=True, timeout=180)
        latency = round(time.time() - t0, 2)
        if proc.returncode != 0:
            results.append({"run_ok": False, "error": proc.stderr[-800:], "latency_s": latency})
            continue

        trace_file = run_dir / "traces.jsonl"
        events = [json.loads(ln) for ln in trace_file.read_text().splitlines() if ln.strip()]
        # zero_trust_enforcement is a PolicyPlugin, not a failure/attack
        # plugin -- its DENY is recorded as POLICY_EVENT (observed_impact
        # "deny"), never ANOMALY/ATTACK_INJECTED; see
        # mantis.observability.plugin._POLICY_PLUGIN_NAMES.
        denies = [
            e for e in events
            if e.get("event_type") == "POLICY_EVENT"
            and e.get("plugin") == "zero_trust_enforcement"
            and e.get("observed_impact") == "deny"
        ]
        tool_calls = [e for e in events if e.get("event_type") == "TOOL_CALL"]
        results.append({
            "run_ok": True,
            "n_tool_calls": len(tool_calls),
            "n_denies": len(denies),
            "latency_s": latency,
        })
        print(f"  trial {i+1}: {len(tool_calls)} tool calls, {len(denies)} denies, {latency}s")

    ok_results = [r for r in results if r.get("run_ok")]
    return {
        "trials": results,
        "n": len(results),
        "n_ok": len(ok_results),
        "total_denies_across_all_trials": sum(r["n_denies"] for r in ok_results),
        "clean_trial_rate": (
            sum(r["n_denies"] == 0 for r in ok_results) / len(ok_results) if ok_results else None
        ),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--trials", type=int, default=5, help="live legitimate-traffic trials")
    parser.add_argument("--matrix-only", action="store_true", help="skip the live-model trials")
    args = parser.parse_args()

    print("=== Exhaustive enforcement matrix (real live inventory) ===")
    matrix = run_enforcement_matrix()
    print(f"  {matrix['n_pairs_tested']} (agent, tool) pairs tested, accuracy {matrix['accuracy']*100:.1f}%")
    print(f"  cross-domain deny rate: {matrix['cross_domain_deny_rate']*100:.1f}% ({matrix['n_cross_domain_pairs']} pairs)")
    print(f"  in-domain allow rate:   {matrix['in_domain_allow_rate']*100:.1f}% ({matrix['n_in_domain_pairs']} pairs)")

    summary = {"enforcement_matrix": matrix}

    if not args.matrix_only:
        print(f"\n=== Live legitimate-traffic trials (zero_trust_demo.yaml x{args.trials}) ===")
        live = run_live_legitimate_traffic_trials(args.trials)
        print(f"  clean-trial rate: {live['clean_trial_rate']*100:.0f}% ({live['n_ok']}/{live['n']} runs ok)")
        summary["live_legitimate_traffic_trials"] = live

    out_path = REPO_ROOT / "results" / "zero_trust_enforcement_trials.json"
    out_path.write_text(json.dumps(summary, indent=2, default=str))
    print(f"\nWritten to {out_path}")


if __name__ == "__main__":
    main()
