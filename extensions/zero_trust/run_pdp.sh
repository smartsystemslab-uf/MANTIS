#!/usr/bin/env bash
# Starts the real Zero Trust Backplane PDP (zt_backplane.pdp_service), fed
# by the MANTIS-generated identities/resources/policy in this directory.
# Needs the `zero_trust` optional dependency installed:
#   pip install -e ".[zero_trust]"
# and dev keys bootstrapped once:
#   python extensions/zero_trust/bootstrap_keys.py
#
#   ./extensions/zero_trust/run_pdp.sh [port]   # default port 8600
set -euo pipefail
cd "$(dirname "$0")"
PORT="${1:-8600}"
export ZT_PROJECT_ROOT="$(pwd)"
if [ ! -f security/dev_keys/pdp_signing_private.pem ]; then
  echo "No dev keys yet -- bootstrapping..."
  python bootstrap_keys.py
fi
echo "Zero Trust PDP: ZT_PROJECT_ROOT=$ZT_PROJECT_ROOT, port $PORT"
exec python -m uvicorn zt_backplane.pdp_service:app --host 127.0.0.1 --port "$PORT"
