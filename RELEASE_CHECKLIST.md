# MANTIS Release Checklist (v0.1.0 Research Release)

This checklist verifies that the repository meets all acceptance criteria defined in WP8:

## 1. Quality & Test Assurance
- [x] All unit tests pass (`pytest tests/unit/`).
- [x] All 49 WP0 regression guard tests pass against golden runs (`pytest refactor_guard_tests/`).
- [x] Master release validation script completes cleanly (`./scripts/release_validation.sh`).
- [x] Code passes flake8 linter with zero syntax/undefined name errors.

## 2. Configuration & Schema Integrity
- [x] JSON schema generated and up-to-date (`mantis --generate-schemas`).
- [x] All sample configurations in `configs/` validate cleanly against schema.
- [x] System inventory generation succeeds (`mantis --inventory`).

## 3. Adversarial Security Plugins
- [x] Prompt Injection plugin verified (`configs/attacks/wp5_prompt_injection.yaml`).
- [x] Message Spoofing plugin verified (`configs/attacks/wp5_message_spoofing.yaml`).
- [x] Route Confusion plugin verified (`configs/attacks/wp5_route_confusion.yaml`).
- [x] Tool Parameter Mutation plugin verified (`configs/attacks/wp5_tool_mutation.yaml`).
- [x] Reliability failure controls verified (`tests/unit/test_plugins.py`).

## 4. Observability & Evaluation
- [x] Trace artifacts conform to JSONL schema (`traces.jsonl`).
- [x] Run manifest records SHA-256 config hash and seed (`run_manifest.json`).
- [x] Hook coverage report generated and validated (`hook_coverage.json`).
- [x] Automated evaluator produces completeness and correctness scores (`mantis --evaluate`).

## 5. Open Source Hygiene & Sanitization
- [x] No private API keys or hardcoded passwords committed.
- [x] Apache 2.0 LICENSE file present.
- [x] CONTRIBUTING.md, SECURITY.md, and CITATION.cff present.
- [x] Documentation complete in `docs/` covering architecture, workflows, scenarios, plugins, observability, and reproducibility.
- [x] Docker Compose provided for containerized bootstrap.

## 6. Post-Paper Extensions (added after v0.1.0; Paper 1 and its evidence are unchanged)
- [x] Exporters: Jaeger, Grafana Tempo, Langfuse, Phoenix (`configs/extensions/*_export_demo.yaml`).
- [x] Workloads: dispute filing, SAR escalation, loan pre-approval, and a second institution profile.
- [x] Six security-mechanism plugins covering all five categories, each live-verified (`configs/extensions/`).
- [x] Minimal UI (`mantis --ui`) with trace, evaluation, hook-coverage and campaign views.
- [x] Extended scenario library: 19 baselines and 26 attack/fault variants (`configs/extended/`, `results/extended_*.json`).
- [x] Starter campaigns (`configs/campaigns/`) and the platform guide (`GUIDE/`, rebuilt on every push via `scripts/publish.sh`).
- [x] 770 offline tests passing (165 skip by design without a live backend or model).

