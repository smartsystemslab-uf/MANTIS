"""Zero Trust Backplane -- Post-Paper Extension (coding plan §11).

Deliberately lives outside src/mantis: MANTIS never imports this package,
so MANTIS has no dependency on Zero Trust to install, run, or test (see
README.md in this directory for the full extension-point contract this
package is built against). Importing *this* package does the opposite --
it reads MANTIS's already-public inventory() and HookBus interfaces and
self-registers a concrete enforcement plugin into MANTIS's existing,
process-global plugin_registry, the same registry attack and guardrail
plugins already use.
"""
