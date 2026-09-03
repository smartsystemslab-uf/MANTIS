# MANTIS — Modular Agent Network Testbed for Instrumentation and Security

MANTIS is a modular, observable multi-agent security testbed for configuring agents, workflows, tools, attacks, and failures, with end-to-end tracing, evaluation, and reproducible benchmarking.

Currently, MANTIS focuses on banking multi-agent architectures (spanning Front, Mid, and Back-Office workflows) as the primary application domain for security evaluation. The ultimate goal of this platform is to provide a robust **testbed to conduct mock attacks (e.g., prompt injections), capture outputs, and evaluate AI agent failures under adversarial conditions.**

---

## Repository Structure

Following WP1 and WP2, the codebase is modularized and entirely configuration-driven:

```text
MANTIS/
├── README.md
├── MIGRATION.md                       # Details of the legacy-to-MANTIS transition
├── pyproject.toml                     # MANTIS package definition
├── src/mantis/                        # Core MANTIS Framework
│   ├── banking/                       # Domain logic (Front/Mid/Back Office)
│   ├── runtime/                       # Interfaces and ADK Adapter
│   ├── config/                        # Pydantic Configuration Models (WP2)
│   ├── core/                          # Dynamic Component Registries (WP2)
│   └── cli/                           # CLI entrypoint (`mantis`)
├── citi_banking_backend/              # Local Banking API Backend
├── citi_banking_mcp_server/           # MCP Server for Banking Tools
├── configs/                           # Experiment Configurations (Baselines, Attacks, Invalid)
├── scripts/                           # Production-ready Validation Scripts
├── docs/                              # Documentation
├── extensions/                        # Custom plugins
├── tests/                             # Future framework tests
├── golden_runs/                       # WP0: Immutable Frozen LLM execution traces
├── banking_baseline_inventory.yaml    # WP0: Full system inventory
├── baseline_metrics.json              # WP0: Performance and behavioral metrics
└── refactor_guard_tests/              # WP0: Regression test suite (49 tests)
```

---

## Current Status: WP1 & WP2 Complete (Modular Architecture & Configuration)

We have successfully migrated the legacy banking code into the formal MANTIS package structure (**WP1**) and replaced all hardcoded execution logic with a declarative YAML configuration engine and dynamic registries (**WP2**).

This completes the foundational platform. MANTIS is now fully prepared to act as an adversarial testbed. The configuration engine is ready to accept complex `attack` YAML blocks, which will be physically executed once we implement the **Hook Bus (WP3)** and **Attack Plugins (WP5)**.

### The Role of WP0 (Regression Guardrails)
**WP0 establishes our invariant baseline.** The 49-test regression suite (`refactor_guard_tests/`) ensures that the core banking business logic and agent behaviors never change or hallucinate while we build out the adversarial testing capabilities. We use these tests constantly to ensure our testbed remains a valid representation of a real-world banking system.

### Platform Artifacts

| # | Deliverable | Path | Description |
|---|-------------|------|-------------|
| 1 | Baseline Inventory | `banking_baseline_inventory.yaml` | Maps all packages, agents, MCP tools, internal ADK tools, workflows, and data stores |
| 2 | Golden Runs | `golden_runs/` | Immutable end-to-end LLM execution traces for baseline scenarios |
| 3 | Baseline Metrics | `baseline_metrics.json` | Records agents involved, tools called, latency, and semantics |
| 4 | Regression Guard Tests | `refactor_guard_tests/` | 49-test pytest suite cross-validating traces against golden runs |
| 5 | Experiment Configs | `configs/` | Declarative YAML files defining workflows and attack injections (WP2) |
| 6 | Run Manifests | `run_artifacts/` | Cryptographically hashed logs proving reproducibility (WP2) |

---

## Validating the Platform (WP1 & WP2)

We provide production-ready verification scripts in the `scripts/` directory to automatically validate the integrity of the testbed.

### 1. Verify WP1 (Baseline Regression)
This script tests that the MANTIS refactor strictly preserves legacy banking logic. It dynamically generates fresh traces into a temporary sandbox and runs the 49 pytest assertions without polluting the `golden_runs` folder.
```bash
./scripts/verify_baseline_regression.sh
```

### 2. Verify WP2 (Configuration Engine)
This script validates the YAML engine, asserting that invalid configs fail gracefully and attack configs are parsed and securely injected into the runtime manifest.
```bash
./scripts/verify_wp2_config.sh
```

---

## Running MANTIS for Mock Attacks (WP3+)

If you are a security researcher or developer setting up a mock attack, you drive the MANTIS system entirely via YAML files.

### Step-by-step Execution:

1. **Start the Banking Backend** (in a separate terminal)
   ```bash
   cd citi_banking_backend
   source scripts/run_server.sh
   # (Or: python -m uvicorn app.main:app --host 127.0.0.1 --port 8000)
   ```

2. **Execute an Experiment Configuration**
   ```bash
   # Run a standard baseline
   mantis --run configs/baselines/front_office_baseline.yaml

   # Or, run an adversarial injection test (Requires WP3/WP5 completion)
   mantis --run configs/attacks/advanced_attack_test.yaml
   ```

3. **Analyze the Results**
   MANTIS will output the live LLM trace to stdout, and securely dump a `run_manifest.json` into the `run_artifacts/` directory containing the random seed and a cryptographic SHA256 hash of your configuration.

---

## What the 49 Regression Tests Cover

The regression suite (`refactor_guard_tests/`) is deliberately designed to balance **strict structural enforcement** with **flexible semantic parsing** to handle natural LLM non-determinism.

| Test Class | Tests | What It Validates |
|---|---|---|
| `TestBaselineFilesExist` | 5 | All WP0 deliverable files are present |
| `TestBaselineMetricsStructure` | 12 | Schema correctness: required fields, semantics fields per workflow |
| `TestFrontOfficeTrace` / `MidOffice` / `BackOffice` | 12 | Traces are parseable. Tool/agent matches use resilient logic to gracefully handle valid LLM alternative paths. |
| `TestInventoryConsistency` | 3 | Inventory covers all tools from metrics, all workflows listed |
| `TestFrontOfficeBehavior` / `MidOffice` / `BackOffice` | 17 | **Advanced:** Agent execution order, routing paths, tool usage, and business outcomes. *Evaluated flexibly to avoid false alarms.* |

---

## Environment Information

### Source Repository:
- **Citi_P3 (Legacy Source):** https://github.com/smartsystemslab-uf/Citi_P3

### Environment:
- **Python:** 3.12.7
- **LLM:** UF Navigator API (`https://api.ai.it.ufl.edu`), model `gpt-oss-20b`
- **Backend:** FastAPI + SQLite (`citi_banking_backend`)
- **Agent framework:** Google ADK with LiteLLM adapter (`src/mantis/runtime`)
- **Tool server:** FastMCP (stdio transport, `citi_banking_mcp_server`)

---

## Developer Guidelines
1. **Unit Testing:** Ensure 100% unit test coverage for new scripts. It's REQUIRED to post unit test code here.
2. **Integration Testing:** Every `.py` or executable file must have corresponding integration tests included. All integration tests must pass before submission.
3. **AI Assistance:** The use of AI tools is encouraged. Please use whichever tools work best for your workflow.
4. **Commits:** Include a brief description of what was changed and why the change was necessary when pushing.
