# MANTIS — Modular Agent Network Testbed for Instrumentation and Security

MANTIS is a modular, observable multi-agent security testbed for configuring agents, workflows, tools, attacks, and failures, with end-to-end tracing, evaluation, and reproducible benchmarking.

Currently, MANTIS focuses on banking multi-agent architectures (spanning Front, Mid, and Back-Office workflows) as the primary application domain for security evaluation.

---

## Repository Structure

Following WP1, the codebase has been modularized:

```
MANTIS/
├── README.md
├── MIGRATION.md                       # Details of the legacy-to-MANTIS transition
├── pyproject.toml                     # MANTIS package definition
├── src/mantis/                        # Core MANTIS Framework
│   ├── banking/                       # Domain logic (Front/Mid/Back Office)
│   ├── runtime/                       # Interfaces and ADK Adapter
│   └── cli/                           # CLI entrypoint (`mantis`)
├── citi_banking_backend/              # Local Banking API Backend
├── citi_banking_mcp_server/           # MCP Server for Banking Tools
├── configs/                           # System Configurations
├── docs/                              # Documentation
├── extensions/                        # Custom plugins
├── tests/                             # Future framework tests
├── golden_runs/                       # WP0: Frozen LLM execution traces
├── banking_baseline_inventory.yaml    # WP0: Full system inventory
├── baseline_metrics.json              # WP0: Performance and behavioral metrics
└── refactor_guard_tests/              # WP0: Regression test suite (49 tests)
```

---

## Current Status: WP1 (Modular Architecture) — Complete

We have completed WP1, successfully migrating the legacy banking code into the formal MANTIS package structure. 
The legacy codebase has been refactored to separate the **Banking Domain** (`src/mantis/banking`) from the **Agent Runtime** (`src/mantis/runtime`), and a unified `mantis` CLI has been introduced.

Before this transition, WP0 established a verified baseline. The 49-test regression suite (`refactor_guard_tests/`) continues to assert that the exact behavioral footprint of the original system is perfectly preserved in the new MANTIS architecture.

### WP0/WP1 Artifacts

| # | Deliverable | Path | Description |
|---|-------------|------|-------------|
| 1 | Baseline Inventory | `banking_baseline_inventory.yaml` | Maps all packages, agents, MCP tools, internal ADK tools, workflows, and data stores |
| 2 | Golden Runs | `golden_runs/` | Real end-to-end LLM execution traces for Front, Mid, and Back Office scenarios |
| 3 | Baseline Metrics | `baseline_metrics.json` | Records agents involved, tools called, latency, and banking semantics per workflow |
| 4 | Regression Guard Tests | `refactor_guard_tests/` | 49-test pytest suite cross-validating traces, metrics, and inventory against the golden runs |

### Running the Regression Tests

```bash
# Ensure you are in your virtual environment
python -m pytest refactor_guard_tests/ -v
```

**Latest run (2026-08-27):** 49 passed, 0 failed in 0.17s

### What the 49 Tests Cover

The test suite is deliberately designed to balance **strict structural enforcement** with **flexible semantic parsing** to handle natural LLM non-determinism. It is organized into 5 test classes:

| Test Class | Tests | What It Validates |
|---|---|---|
| `TestBaselineFilesExist` | 5 | All WP0 deliverable files are present |
| `TestBaselineMetricsStructure` | 12 | Schema correctness: required fields, semantics fields per workflow |
| `TestFrontOfficeTrace` / `MidOffice` / `BackOffice` | 12 | Golden run traces are parseable. Tool and agent matches use resilient logic to gracefully handle or skip valid alternative LLM decision paths. |
| `TestInventoryConsistency` | 3 | Inventory covers all tools from metrics, all workflows listed |
| `TestFrontOfficeBehavior` / `MidOffice` / `BackOffice` | 18 | **Advanced:** Agent execution order, routing paths, tool usage, and business outcomes. *Note: Semantic outputs and tool arguments (like customer IDs) are evaluated flexibly using regex/types. Tests explicitly assert alternate decision logic (e.g., handling invalid schedules) rather than triggering false alarms.* |

---

## Generating Traces in MANTIS (WP1+)

> **Important:** The regression tests currently validate the frozen `.out` files. When you modify the codebase, you must regenerate traces from the MANTIS system and verify they pass the same behavioral contract.

### Step-by-step workflow:

1. **Before modifying:** Run the existing tests to confirm the baseline is intact.
   ```bash
   python -m pytest refactor_guard_tests/ -v
   ```

2. **After modifying:** Regenerate traces from the MANTIS CLI.
   ```bash
   # 1. Start your refactored backend (in a separate terminal)
   cd citi_banking_backend
   source scripts/run_server.sh
   # (Or: python -m uvicorn app.main:app --host 127.0.0.1 --port 8000)
   
   # 2. Run each scenario and capture output using the MANTIS CLI
   mantis --scenario front_office_monitoring > golden_runs/front_office_monitoring.out 2>&1
   mantis --scenario mid_office_planning > golden_runs/mid_office_planning.out 2>&1
   mantis --scenario back_office_clean > golden_runs/back_office_clean.out 2>&1
   ```

3. **Verify:** Run the tests again. If your modified system produces missing tools, wrong arguments, or different business outcomes without a valid decision path, the tests will fail and tell you exactly what broke.
   ```bash
   python -m pytest refactor_guard_tests/ -v
   ```

### What will fail if you break something:

| If you break... | These tests fail... |
|---|---|
| Agent routing (e.g., skip the router) | `test_routing_path` |
| Agent execution order | `test_agent_execution_order` |
| Invalid or missing tool arguments (e.g. malformed customer/batch IDs) | `test_customer_context_fetched_for_correct_customer`, `test_batch_id_consistent_across_all_tool_calls`, etc. |
| Missing mandatory tool calls (e.g., skip compliance check) | `test_compliance_agent_searches_policies` |
| Missing or empty output traces | `test_trace_parseable`, `test_trace_contains_events` |
| Inventory doesn't match metrics | `test_adk_tools_cover_metrics_tools` |

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
1. **Unit Testing:** For every script you add here, please make sure you ensure there is 100% unit test coverage. It's REQUIRED to post your unit test code here, since our project is large enough as an open-source project.
2. **Integration Testing:** Every `.py` file or other executable file added to this project must also have corresponding integration tests codes included in the repository. All integration tests must pass before submission.
3. **AI Assistance:** The use of AI tools and other unit testing tools is encouraged. Please use whichever tools work best for your workflow.
4. **Commits:** When pushing changes to the repository, please include a brief description of what was changed and why the change was necessary.
