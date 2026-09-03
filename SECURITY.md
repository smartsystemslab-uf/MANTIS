# Security Policy

## Reporting Security Vulnerabilities

MANTIS is an adversarial research testbed designed to simulate and evaluate multi-agent threats in controlled banking environments.

If you discover a security vulnerability in the MANTIS framework itself (such as unintended remote code execution, unhandled credential leakage, or unsafe deserialization in test harnesses), please report it responsibly.

### How to Report

Do **not** report security vulnerabilities via public GitHub issues.

Instead, please send a detailed description to:
- **Email:** `brohithkum@gmail.com`
- **Subject:** `[SECURITY] MANTIS Framework Vulnerability Report`

Include in your report:
- A description of the vulnerability
- Steps to reproduce or proof-of-concept configuration
- Potential impact and affected components
- Any suggested mitigations or patches

### Scope

- **In Scope:** Vulnerabilities in the core MANTIS runtime, Hook Bus, telemetry pipelines, MCP tool proxying, and CLI runners.
- **Out of Scope:** The simulated mock attacks (e.g., prompt injection, route confusion) located under `src/mantis/plugins/attacks/`, as these are intentionally designed adversarial plugins for research and benchmarking purposes.
