#!/usr/bin/env python3
"""Runs the exact `mantis` CLI, with Zero Trust enforcement available.

    python -m extensions.zero_trust.run_with_zero_trust --run configs/extensions/zero_trust_demo.yaml

Run as a module (-m), from the repo root, not as a script path -- `-m`
puts the repo root on sys.path so `import extensions...` resolves;
`python extensions/zero_trust/run_with_zero_trust.py` puts this file's
own directory on sys.path instead and fails with ModuleNotFoundError.

This accepts the exact same flags as `mantis` itself (--run, --validate,
--evaluate, ...) -- the only difference from calling `mantis` directly is
that this script imports enforcement_plugin first, which self-registers
"zero_trust_enforcement" into the plugin registry a config's `policies:`
list can then reference. That one import is the entire integration
surface: no change to MANTIS's own CLI, config schema, or HookBus.
"""
import extensions.zero_trust.enforcement_plugin  # noqa: F401  self-registers on import

from mantis.cli.main import main

if __name__ == "__main__":
    main()
