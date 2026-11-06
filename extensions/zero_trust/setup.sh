#!/usr/bin/env bash
# One-time setup for the Zero Trust Backplane toggle (extensions/zero_trust/).
#
# The Backplane's own packages locate their data files (schemas, policy
# templates, dev keys) with `Path(__file__).resolve()` relative to a real
# source checkout -- a plain `pip install` of a built wheel leaves those
# files behind entirely. Every one of the 7 packages needed for in-process
# enforcement must be installed editable, from the real checkout, exactly
# as the upstream project's own README documents. That checkout is pinned
# here as a git submodule (extensions/zero_trust/backplane, tag v1.0.1) so
# "which commit" is reproducible the same way every other dependency in
# this repo is pinned.
set -euo pipefail
cd "$(dirname "$0")/.."/..
git submodule update --init extensions/zero_trust/backplane
cd extensions/zero_trust/backplane
python -m pip install --upgrade pip
python -m pip install \
    -e packages/zt-interface -e packages/zt-scanner -e packages/zt-psl \
    -e packages/zt-pdp -e packages/zt-pep -e packages/zt-lease -e packages/zt-adk
echo "Zero Trust Backplane packages installed (editable, from extensions/zero_trust/backplane @ $(git rev-parse --short HEAD))."
echo "Next: zt-adk keys init --approver ops_lead --secondary risk_officer  (from extensions/zero_trust/, once)"
echo "Then: zt-adk build   (regenerate the committed bundle after any agent/tool change)"
