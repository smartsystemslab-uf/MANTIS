# Zero Trust Backplane -- toggleable integration

A real, toggleable integration of the independently-developed
[`Citi_P3_Zero_Trust_Backplane`](https://github.com/smartsystemslab-uf/Citi_P3_Zero_Trust_Backplane)
project with MANTIS -- specifically its Task 4 signed Policy Decision Point
(PDP). Per a team decision, this now lives in the MANTIS repo (reversing an
earlier decision to keep it local-only; see `CHANGELOG.md`), but strictly as
an **opt-in extension**: a stock `pip install -e .` never installs or
imports anything here, and every existing config, test, and run behaves
exactly as it does without this folder.

## How the toggle works

Add `zero_trust_enforcement` to any config's `policies:` list and it is on
for that run; leave it out and it is off, with zero code-path difference
from a stock MANTIS run -- the same opt-in mechanism every other MANTIS
defense already uses. See `../../configs/extensions/zero_trust_demo.yaml`.

## What's real here, and what's ours

The actual authorization decision, request/response signing, signature
verification, replay protection, and audit trail are **the real project's
own code**, pip-installed from its repo and run as its own process (its
Task 4 PDP, `zt_backplane.pdp_service`) -- nothing here reimplements that
logic. What's new in this folder and in
`src/mantis/plugins/policies/zero_trust_enforcement.py` is the glue:

- `generate_policy.py` -- reads MANTIS's own live inventory
  (`DOMAIN_AGENTS`, `_DOMAIN_TOOL_NAMES`, `TOOL_SEMANTICS`) and writes
  `config/identities.yaml`, `config/resources.yaml`, and
  `policy_store/mantis_default_deny_by_domain.yaml` in the real project's
  own schema. The real project's own scanner (Tasks 1-2) targets an older,
  no-longer-present checkout layout, so this generates the policy *input*
  from MANTIS's current system instead of running that scanner.
- The generated policy is deliberately simple and auditable: an agent may
  act on a tool in its own domain; everything else -- cross-domain, or an
  unrecognized agent/tool -- is denied by the real PDP's own default
  (`default_deny_no_matching_policy`). This is the same guarantee an
  earlier local-only representative slice validated exhaustively (770
  agent/tool pairs, 100% correctly enforced) before this real integration
  replaced it.
- `bootstrap_keys.py` -- generates local Ed25519 dev signing keys (never
  committed) and signs the generated policy bundle, adapted from the real
  project's own `scripts/bootstrap_dev_crypto.py`.
- `run_pdp.sh` -- starts the real PDP service
  (`zt_backplane.pdp_service:app`) with `ZT_PROJECT_ROOT` pointed at this
  directory, so it reads MANTIS-generated identities/resources/policy
  instead of the real project's own sample data.
- `src/mantis/plugins/policies/zero_trust_enforcement.py` -- the MANTIS
  side: a `PolicyPlugin` that, at the `tool` control point, builds and
  signs a real authorization request using the real project's own
  `zt_backplane.dev_evidence.build_signed_request`, calls the real PDP's
  `/v1/challenge` then `/v1/authorize`, and maps its real decision onto a
  MANTIS `HookResult` (ALLOW/ALLOW_WITH_OBLIGATIONS -> continue; anything
  else, including an unreachable PDP -> deny -- fail closed).

`transfer_to_agent` (MANTIS's routing tool) is intentionally out of scope:
it isn't a domain-owned resource in this policy model, and MANTIS's own
`risk_aware_routing_guard` already covers routing decisions.

## Setup

```bash
cd /path/to/MANTIS
pip install -e ".[zero_trust]"            # pulls the real repo's Task 4 PDP package
python extensions/zero_trust/bootstrap_keys.py    # once; regenerate after a --force rotate
./extensions/zero_trust/run_pdp.sh                # leave running, in its own terminal (port 8600)
```

Then, in any config -- a dedicated toggle, so turning it on or off when configuring an attack is one clear switch rather than remembering the plugin name and its parameters by hand:

```yaml
zero_trust:
  enabled: true                         # flip to false (or delete the block) to run the same config without it
  pdp_url: http://127.0.0.1:8600        # default; override if you ran run_pdp.sh on a different port
```

(This is sugar over the generic `policies:` list every other defense uses -- `policies: [{plugin: zero_trust_enforcement, parameters: {pdp_url: ...}}]` works identically, if you prefer that form. The UI's Experiment Editor has the same toggle as a checkbox.)

`mantis --run configs/extensions/zero_trust_demo.yaml` runs a full,
undefended-equivalent legitimate workflow with the toggle on -- every real
tool call is checked by the real PDP, and the run completes identically to
the undefended baseline (`run_artifacts/front_office_monitoring`), which is
the point: a real, independent security layer that is a no-op for
legitimate traffic and fails closed for anything it doesn't recognize.

## Regenerating the policy

Re-run after MANTIS's agents, tools, or domains change:

```bash
python extensions/zero_trust/generate_policy.py
python extensions/zero_trust/bootstrap_keys.py   # re-signs the updated bundle
```

`config/identities.yaml`, `config/resources.yaml`, and
`policy_store/*.yaml` are committed (generated, reviewable, reproducible
from MANTIS's own inventory). `security/dev_keys/`, `runtime/` (audit log,
replay/nonce state), and `policy_store/*.sig.json` (signatures tied to the
local dev keys) are git-ignored and regenerated locally, the same as
`.env`.

## Known limits

- Dev signing keys only -- never meant to secure anything beyond a local
  demo (see the real project's own `trusted_issuers.yaml` TODO comment).
- The generated policy is a single default-deny-by-domain rule, not the
  real project's full workflow/risk-aware policy model it's capable of
  (see its own `policy_store/front_office.yaml` for an example of the
  richer kind of policy it supports) -- that would need per-agent domain
  knowledge well beyond this integration's current scope.
- Only the `tool` control point is enforced. The real project's own PEP
  placement (Task 3) covers input/output boundaries too; this integration
  doesn't yet.
