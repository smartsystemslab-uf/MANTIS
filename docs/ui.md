# Minimal UI *(Post-Paper Extension, coding plan §11)*

A schema-driven experiment editor and trace viewer, invoking the same CLI/API MANTIS already ships — no separate business logic.

```bash
pip install -e ".[ui]"
mantis --ui
# open http://127.0.0.1:8765
```

## Seeing an attack in the browser

After any run, open the page and pick the run in the Trace Viewer dropdown (`Refresh` reloads the list; runs marked ✓evaluated have a scorecard). **Load trace** shows every event (look for `ATTACK_INJECTED`, `POLICY_EVENT`, `ANOMALY`), **View evaluation** shows the scored dimensions (see `attack_ground_truth` and `workflow_outcome`), and **View hook coverage** shows which checkpoints fired. **Evaluate** scores a run from the browser, the same as `mantis --evaluate`.

## What "no separate business logic" means here concretely

- **Validate / Run** shell out to the exact same `mantis` console-script entrypoint a terminal user would type — `python -m mantis.cli.main --validate <file>` / `--run <file>` — as a real subprocess. There is no second, UI-side config-validation or experiment-execution code path that could drift from the real CLI's behavior.
- **Schema, registries, and inventory** (`/api/schema`, `/api/registries`, `/api/inventory`) call `ExperimentConfig.model_json_schema()`, the same `domain_registry`/`scenario_registry`/`workflow_registry`/`plugin_registry`/`evaluator_registry` objects, and `NativeBankingAdapter().inventory()` directly — the identical objects `mantis --generate-schemas`/`--validate`/`--inventory` already read from, not a UI-maintained copy.
- **Trace viewer** (`/api/runs/<name>/trace`) reads `run_artifacts/<name>/traces.jsonl` directly — the same portable JSONL file every other MANTIS consumer (the evaluator, the campaign report, `docs/observability.md`) reads.
- **Evaluate** (`/api/runs/<name>/evaluate`) shells out to `mantis --evaluate <dir>`.
- **Hook coverage** (`/api/runs/<name>/hook-coverage`) reads `run_artifacts/<name>/hook_coverage.json` directly, symmetric with the trace/evaluation endpoints above.
- **Campaign** (`/api/campaign`) shells out to `mantis --campaign <dir>`, then chains a second, real CLI invocation (`mantis --report <output_dir>`) against the directory that command printed — two existing CLI commands run in sequence, not new aggregation logic. **Campaign report** (`/api/campaign/<name>/report`) then reads the resulting `report.md` directly.

## Editor form fields are schema-driven, not hardcoded

Domain, workflow, scenario, and attack/policy plugin dropdowns are populated at page load from `/api/registries` and `/api/inventory` — live data, not a hand-maintained list baked into `index.html`. Submitting the form validates the assembled dict against the real `ExperimentConfig` Pydantic model server-side (`_write_config` in `src/mantis/ui/server.py`) before it's ever written to disk as the YAML file the CLI subprocess reads.

## What this is not

Not a replacement for the CLI, and not a second implementation of anything — a thinner surface over it. Not authenticated or hardened for anything beyond local, single-user use (it binds to `127.0.0.1` only). Building out a fuller editor (nested observability/benchmark sub-forms, multi-policy lists, live-updating trace tail while a run is in progress) is future work; this slice covers the fields most experiments actually use.
