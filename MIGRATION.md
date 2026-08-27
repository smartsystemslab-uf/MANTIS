# WP1 Migration Notes

This document describes the architectural changes made during Work Package 1 (WP1) to transform the legacy `Citi_P3` codebase into the modular `mantis` testbed.

## Package Structure
The monolithic `citi_banking_adk` scripts have been restructured into a standard Python package under `src/mantis`.
- **`mantis.core` and `mantis.config`**: Reserved for shared experiment lifecycle and configuration schemas.
- **`mantis.runtime`**: Contains the `BankingRuntimeAdapter`, the new standardized entry point for launching experiments without hardcoding workflow logic.
- **`mantis.banking`**: The legacy banking logic (front office, mid office, back office, agents, tools) has been extracted here as first-class domain modules.

## Removed Global State
- Legacy relative imports (e.g. `from ..agents`) were updated to explicit module paths (`from mantis.banking.agents`).
- `run_scenarios.py` was replaced by the `mantis` CLI. Use `mantis --scenario <name>` to execute a workflow and `mantis --inventory` to view the available banking topology.

## Regression Guard Validation
The migration successfully preserves the exact semantic architecture established in WP0. The `refactor_guard_tests/` suite (50 tests) continues to pass 100% cleanly against the WP0 golden runs, proving that the structural refactoring did not break the intended banking behavior.
