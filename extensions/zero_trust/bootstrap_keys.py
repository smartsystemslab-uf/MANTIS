"""Generates (if missing) the local dev signing keys under security/dev_keys/
and (re)signs every extensions/zero_trust/policy_store/*.yaml bundle --
adapted from the real zt_backplane repo's own
zero_trust_pdp_task4_secure/scripts/bootstrap_dev_crypto.py, pointed at
this directory instead of that repo's checkout. Needs the `zero_trust`
optional dependency installed (`pip install -e ".[zero_trust]"`).

Dev keys only -- never committed (see .gitignore) and never meant to secure
anything beyond a local demo. Idempotent: re-run any time the policy
changes; use --force to rotate every key.
"""
import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent
KEY_NAMES = ["pep", "risk", "idp", "workflow", "approval", "secondary", "policy", "pdp_signing"]


def main():
    try:
        from zt_backplane.canonical import sha256_hex
        from zt_backplane.crypto import generate_keypair, load_private_key, sign_mapping
    except ImportError as e:
        raise SystemExit(
            "The zero_trust optional dependency isn't installed. Run:\n"
            '  pip install -e ".[zero_trust]"\n'
            f"(import failed: {e})"
        )

    parser = argparse.ArgumentParser()
    parser.add_argument("--force", action="store_true", help="replace existing development keys")
    args = parser.parse_args()

    key_dir = ROOT / "security" / "dev_keys"
    key_dir.mkdir(parents=True, exist_ok=True)
    for name in KEY_NAMES:
        private_path, public_path = key_dir / f"{name}_private.pem", key_dir / f"{name}_public.pem"
        if args.force or not private_path.exists() or not public_path.exists():
            generate_keypair(private_path, public_path)

    policy_key = load_private_key(key_dir / "policy_private.pem")
    (ROOT / "runtime").mkdir(exist_ok=True)
    signed = 0
    for path in sorted((ROOT / "policy_store").glob("*.yaml")):
        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
        sidecar = {
            "schema_version": "1.0",
            "issuer": "policy.prototype",
            "key_id": "policy-1",
            "algorithm": "Ed25519",
            "signed_at": datetime.now(timezone.utc).isoformat(),
            "bundle_digest": sha256_hex(raw),
            "signature": sign_mapping(policy_key, raw),
        }
        path.with_suffix(".sig.json").write_text(json.dumps(sidecar, indent=2, sort_keys=True) + "\n")
        signed += 1
    print(f"Development keys ready in {key_dir}; {signed} policy bundle(s) signed.")


if __name__ == "__main__":
    main()
