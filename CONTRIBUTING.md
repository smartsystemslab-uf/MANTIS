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
   pip install -e ".[dev]"
   ```

3. Run the unit and regression test suites:
   ```bash
   pytest tests/unit/
   pytest refactor_guard_tests/
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
