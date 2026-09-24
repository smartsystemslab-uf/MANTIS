# Contributing to MANTIS

Thank you for your interest in contributing to MANTIS (Modular Agent Network Testbed for Instrumentation and Security)!

## Development Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/smartsystemslab-uf/MANTIS.git
   cd MANTIS
   ```

2. Set up virtual environment (Python 3.12+):
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -e ".[dev,exporters]"
   pip install -r citi_banking_backend/requirements.txt
   pip install -r citi_banking_mcp_server/requirements.txt
   ```

3. Run the test suites:
   ```bash
   pytest tests/unit/
   pytest refactor_guard_tests/
   (cd citi_banking_backend && pytest tests/)
   (cd citi_banking_mcp_server && pytest tests/)
   ```

## Contribution Workflow

1. Fork the repo and create a feature branch (`feature/my-plugin` or `fix/issue-description`).
2. Adhere to code style:
   - Run `flake8 src tests`
   - Use type annotations wherever applicable
   - Maintain docstrings and comments
3. Add corresponding unit tests in `tests/unit/` for any new plugins, evaluators, or CLI options.
4. Ensure all baseline regression guard tests pass (`refactor_guard_tests/`).
5. Open a Pull Request with a clear description of the modifications and verification results.

## Security Contributions

If you are contributing new security attack plugins or failure modes:
- Place them under `src/mantis/plugins/attacks/` or `src/mantis/plugins/failures/`.
- Register the plugin in `src/mantis/core/registry.py`.
- Include a reproducible configuration in `configs/attacks/`.
- Provide machine-readable ground truth and unit tests validating interception.

## Adding an experiment, plugin or defense

The platform guide (`GUIDE/MANTIS_Platform_Guide.pdf`, sections 9.1 to 9.3) has a from-scratch walkthrough, a table of where every new artifact lives, and a checklist. In short:
- Give each experiment a unique `experiment.name`; reusing a shipped name overwrites that run folder, and the `wp5_*`, `wp6_*` and baseline runs are recorded paper evidence.
- Defenses go under `src/mantis/plugins/policies/` and their name must be added to `_POLICY_PLUGIN_NAMES` in `src/mantis/observability/plugin.py`.
- New config folders should be added to `CONFIG_DIRS` in `tests/unit/test_config_library.py` so they are validated automatically.
- The offline tests and `scripts/release_validation.sh` rewrite a few tracked run folders; run `git status` and `git checkout --` those before committing.
- Never commit an API key. Keys live in `.env`, which is git-ignored. Pushing through `./scripts/publish.sh` also refreshes the guide PDF.
