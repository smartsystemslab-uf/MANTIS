# Getting Started with MANTIS

Welcome to MANTIS (Modular Agent Network Testbed for Instrumentation and Security). This guide walks you through setup, running your first experiment, injecting adversarial attacks, and viewing evaluation results.

---

## 1. Prerequisites
- **Python:** 3.12 or higher
- **Virtual Environment:** Recommended (`venv` or `conda`)
- **Docker & Docker Compose:** (Optional) for containerized backend services

---

## 2. Installation

```bash
# Clone repository
git clone https://github.com/smartsystemslab-uf/MANTIS.git
cd MANTIS

# Set up virtual environment
python -m venv .venv
source .venv/bin/activate

# Install in editable mode with development dependencies
pip install -e ".[dev]"
```

Verify the CLI is installed:
```bash
mantis --help
```

---

## 3. Quick Start Validation

To verify that your installation, schemas, configurations, and evaluation metrics are properly configured without needing active LLM API credentials, run:

```bash
./scripts/quickstart.sh
```

This script:
1. Generates JSON schemas (`configs/experiment_schema.json`).
2. Validates baseline and attack configurations.
3. Inspects registered plugins and scenarios.
4. Generates the full banking system inventory.
5. Evaluates trace artifacts against ground-truth security criteria.

---

## 4. Running a Live Experiment

### Step 1: Start the Banking Backend
In a separate terminal:
```bash
cd citi_banking_backend
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

### Step 2: Validate the Experiment Config
```bash
mantis --validate configs/baselines/front_office_baseline.yaml
```

### Step 3: Run the Experiment
```bash
mantis --run configs/baselines/front_office_baseline.yaml
```

Artifacts are automatically recorded in `run_artifacts/front_office_monitoring/`:
- `run_manifest.json`: Configuration snapshot, SHA-256 hash, random seed.
- `traces.jsonl`: Complete, causal event stream linking agents, messages, and tools.
- `hook_coverage.json`: Verification of interception points executed.

---

## 5. Running an Adversarial Security Experiment

MANTIS allows you to inject attacks purely via YAML:

```bash
mantis --run configs/attacks/advanced_attack_test.yaml
```

Evaluate the resulting attack trace:
```bash
mantis --evaluate run_artifacts/advanced_attack_test
```

---

## 6. Running a Full Security Campaign

Run all attacks in a directory and generate a comparative Markdown report:

```bash
mantis --campaign configs/attacks/
mantis --report run_artifacts/campaign_run_<timestamp>
```
