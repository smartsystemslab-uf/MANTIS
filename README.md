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
## Current Status: WP1, WP2, & WP3 Complete

We have successfully migrated the legacy banking code (**WP1**), replaced hardcoded logic with a declarative YAML engine (**WP2**), and implemented the **Hook Bus (WP3)** to allow for dynamic runtime interception.

### The Hook Bus (WP3)
The Hook Bus is the core of MANTIS's adversarial testing capabilities. It provides a non-invasive middleware layer that registers callback functions at five strategic lifecycle events:
1. **Input**: Intercepting raw user prompts before they reach the agent.
2. **Agent**: Monitoring internal reasoning processes.
3. **Interaction**: Modifying communication between the agent and the environment.
4. **Tool**: Intercepting function calls (e.g., to the banking backend) to perform parameter mutation or injection.
5. **Output**: Filtering or auditing the final response provided to the user.

### Project Roadmap

- [x] **WP1: Modularize the Banking Multi-Agent Testbed**: Restructured the project from an application to a reusable research framework.
- [x] **WP2: Configuration, Schemas, and Registries**: Implemented a YAML-driven experiment configuration engine (`mantis --run`).
- [x] **WP3: Experiment Control Points and Hook Bus**: Built the `HookBus` allowing dynamic interception and mutation of the multi-agent graph at 5 strategic lifecycles (`input`, `agent`, `interaction`, `tool`, `output`).
- [ ] **WP4: Standard Observability Pipeline**: Emit MLflow, OpenTelemetry, and structured JSONL traces containing security assertions.
- [ ] **WP5: Initial Attack and Failure Plugins**: Implement Prompt Injection, Message Spoofing, Route Confusion, and Parameter Mutation plugins.
- [ ] **WP6: Evaluation and Benchmarking**: Scripts to aggregate and grade attack success vs system reliability.
- [ ] **WP7: CLI and Reproducible User Workflow**: High-level execution of full test campaigns.
- [ ] **WP8: Tests, Documentation, and Research Release**: Ensure CI/CD stability and reproducibility.

---

## Validating the Platform

We provide production-ready verification scripts in the `scripts/` directory to automatically validate the integrity of the testbed.

1. **WP0 / WP1 Baseline Regression:** 
   ```bash
   ./scripts/verify_baseline_regression.sh
   ```
   *Automatically starts a background backend, traces the LLM front/mid/back office baseline models, asserts semantic behavior matches `baseline_metrics.json`, and shuts down gracefully.*

2. **WP2 Configuration Engine Demo:** 
   ```bash
   ./scripts/verify_wp2_config.sh
   ```
   *Demonstrates the execution of robust YAML experiment generation, configuration hashing, seed reproducibility, and strict validation error propagation.*

3. **WP3 Hook Bus Injection Demo:** 
   ```bash
   ./scripts/demo_wp3_hooks.sh
   ```
   *Highlights the invisible integration of the HookBus by deploying a Mock Attack plugin that intercepts a live ADK tool call, maliciously mutates the `customer_id` parameter, and records coverage stats—without altering core business logic.*

---

## Running MANTIS for Mock Attacks

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
