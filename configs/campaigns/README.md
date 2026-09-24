# Starter campaigns

Four small, themed sets of experiments. Each is a folder you sweep with one command, then explore in the browser. Every run is a single trial, so a campaign takes a few minutes, not hours.

| Campaign | What you learn | Runs |
|---|---|---|
| `1_attack_tour` | The whole attack catalog: prompt injection, message spoofing, route confusion, tool mutation, a delay fault | 5 |
| `2_defenses` | The six defenses, each against the attack it is built to stop | 6 |
| `3_workloads` | The workflows added after the original paper, no attack: dispute, SAR, loan, a second institution | 4 |
| `4_new_attack_surfaces` | Extended-library attacks on the newer workflows, including data-level effects | 5 |

## Run one

```bash
source .venv/bin/activate
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000   # in a second terminal
mantis --campaign configs/campaigns/1_attack_tour
mantis --ui                                                    # then open http://127.0.0.1:8765
```

Needs a UF Navigator key in `.env` (copy `.env.example`); the mock model cannot reach past the first agent, so campaigns need a live model.

## Where the results go

- Each run: `run_artifacts/camp_<n>_<name>/` (manifest, trace, evaluation, hook coverage). These appear in the UI's run dropdown.
- The campaign report: `run_artifacts/campaign_run_<timestamp>/report.md`, also viewable with `mantis --report run_artifacts/campaign_run_<timestamp>`.

## Reading the report

The report table has a Status and an Attack Effect column. For an attack run, `FAIL` does not mean something broke: it means the attack's effect was detected against the scenario's baseline (for example route confusion, which diverts the workflow). `fired, no effect this trial` means the attack ran but the system's outcome did not change.

## Reading a result

- Attack runs: look for the `ATTACK_INJECTED` event in the trace, then `attack_ground_truth` (did it fire, did the outcome change) in the evaluation.
- Defense runs: the attack still fires, and a `POLICY_EVENT` shows the defense stepping in.
- Workload runs: `workflow_outcome` shows the terminal state reached (dispute filed, SAR filed, loan decision recorded).

These are copies of configs from `configs/attacks/`, `configs/extensions/` and `configs/extended/`, renamed `camp_*` so a campaign never overwrites the recorded paper evidence. For larger, scored campaigns (5 trials each), see `docs/extended_scenarios.md`.
