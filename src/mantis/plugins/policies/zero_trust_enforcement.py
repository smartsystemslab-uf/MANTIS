"""Zero Trust Backplane enforcement (toggleable integration of the real,
independently-developed project github.com/smartsystemslab-uf/Citi_P3_Zero_Trust_Backplane,
specifically its Task 4 signed PDP service -- not a reimplementation).

Per team decision, this now lives in the MANTIS repo (reversing an earlier
decision to keep it local-only -- see CHANGELOG), but as an opt-in,
toggleable extension, not a required dependency: a stock `pip install -e .`
never imports this module, never talks to anything on the network for it,
and every existing config/test/run behaves exactly as it does today.

## How the toggle works

Exactly like every other MANTIS defense: list `zero_trust_enforcement`
under a config's `policies:` and it is on for that run; leave it out and
it is off, with zero code-path difference from a stock MANTIS run. Nothing
global, nothing always-on.

## What it actually does

At the `tool` control point, before a tool call reaches the real banking
backend, this plugin acts as the Backplane's PEP (Policy Enforcement
Point): it builds and cryptographically signs a real authorization
request using the real project's own signing code
(`zt_backplane.dev_evidence.build_signed_request`), sends it to a real,
separately-running PDP service (`extensions/zero_trust/run_pdp.sh`,
`zt_backplane.pdp_service`, the genuine Task 4 signed Policy Decision
Point), and enforces whatever it decides. No part of the authorization
decision, request signing, or response-signature verification is
reimplemented here -- all of that is the real project's own code.

The PDP's policy is generated from MANTIS's own live inventory
(`extensions/zero_trust/generate_policy.py`, run once, or after the
agent/tool inventory changes) rather than from the real project's own
scanner, which targets an older, no-longer-present checkout layout. The
generated policy is a simple, auditable default-deny-by-domain rule: an
agent may act on a tool in its own domain; anything else -- cross-domain,
or an unrecognized agent/tool -- is denied by the PDP's own default
(`default_deny_no_matching_policy`), the same guarantee the earlier local
representative slice validated exhaustively before this real integration
replaced it.

`transfer_to_agent` (the routing tool, not a domain-owned resource) is
intentionally out of scope for this plugin -- MANTIS's own
`risk_aware_routing_guard` already covers routing decisions, and this
plugin's domain-owned-tool policy model has no resource record for it
(every call would otherwise be incorrectly denied).

## Fail-closed

If the PDP is unreachable (not started, wrong port, network error) or
returns anything other than ALLOW/ALLOW_WITH_OBLIGATIONS, the call is
denied. A security layer that is down must not silently become "no
security layer."

## Setup

    pip install -e ".[zero_trust]"
    python extensions/zero_trust/bootstrap_keys.py   # once, local dev keys
    ./extensions/zero_trust/run_pdp.sh                # separate terminal, port 8600

Then add `zero_trust_enforcement` to any config's `policies:` list.
"""
from pathlib import Path
from typing import Any

from mantis.hooks import HookContext, HookAction, HookResult

_REPO_ROOT = Path(__file__).resolve().parents[4]
_ZT_ROOT = _REPO_ROOT / "extensions" / "zero_trust"

# Tools the policy model doesn't cover on purpose -- see module docstring.
_OUT_OF_SCOPE_TARGETS = {"transfer_to_agent"}

# Deliberately NOT wrapped in try/except here: this import must fail loudly
# when the optional dependency isn't installed, so that core/registry.py's
# own try/except (around importing *this module*) is the single place that
# decides whether zero_trust_enforcement exists at all -- not registered,
# not in mantis --inventory, not in the UI's plugin dropdowns, rather than
# registered-but-broken. See core/registry.py's comment on this import.
import httpx
import zt_backplane.dev_evidence as _dev_evidence

# The real project's dev_evidence module (and pdp_service) compute their own
# file paths relative to their own package location, assuming the original
# source-checkout layout. Pointing that ROOT at our generated
# extensions/zero_trust/ directory is the entire adaptation needed -- the
# signing logic itself is untouched.
_dev_evidence.ROOT = _ZT_ROOT


class ZeroTrustEnforcementPlugin:
    name = "zero_trust_enforcement"
    supported_stages = {"tool"}

    def __init__(self, pdp_url: str = "http://127.0.0.1:8600", timeout_seconds: float = 2.0, **kwargs: Any):
        self.pdp_url = pdp_url.rstrip("/")
        self.timeout_seconds = timeout_seconds

    def _agent_domain(self, agent_name: str) -> str | None:
        from mantis.banking.domains import DOMAIN_AGENTS
        for domain, agents in DOMAIN_AGENTS.items():
            if agent_name in agents:
                return domain
        return None

    def _deny(self, reason: str) -> HookResult:
        return HookResult(action=HookAction.DENY, payload={"error": f"denied by zero_trust_enforcement: {reason}"})

    def apply(self, ctx: HookContext) -> HookResult:
        if ctx.metadata.get("specific_hook") != "before_tool" or ctx.target in _OUT_OF_SCOPE_TARGETS:
            return HookResult(action=HookAction.CONTINUE)

        agent_name, tool_name = ctx.source, ctx.target
        domain = self._agent_domain(agent_name) if agent_name else None
        if domain is None:
            # An agent not in MANTIS's own live inventory at all -- can't even
            # form a canonical id to ask the PDP about. Fail closed.
            return self._deny(f"caller '{agent_name}' is not a known MANTIS agent")

        from mantis.banking.tool_semantics import TOOL_SEMANTICS
        action = TOOL_SEMANTICS.get(tool_name, {}).get("operation_type", "read")
        subject_canonical, subject_runtime = f"agent.{domain}.{agent_name}", agent_name
        resource_canonical = f"resource.{domain}.{tool_name}"
        resource_runtime = f"{domain}.{tool_name}"  # see generate_policy.py's comment on why this is qualified

        try:
            challenge = httpx.post(
                f"{self.pdp_url}/v1/challenge",
                json={"subject_canonical_id": subject_canonical, "subject_runtime_id": subject_runtime},
                timeout=self.timeout_seconds,
            )
            if challenge.status_code == 404:
                return self._deny(f"PDP does not recognize subject {subject_canonical}")
            challenge.raise_for_status()
            nonce = challenge.json()["nonce"]

            request = _dev_evidence.build_signed_request(
                nonce=nonce,
                subject_canonical_id=subject_canonical,
                subject_runtime_id=subject_runtime,
                resource_canonical_id=resource_canonical,
                resource_runtime_id=resource_runtime,
                action=action,
                workflow_id=f"workflow.{domain}.{ctx.workflow_id}",
                workflow_instance_id=ctx.run_id,
                risk_score=300,
                auth_factors={"workload_identity": True},
            )
            response = httpx.post(
                f"{self.pdp_url}/v1/authorize",
                json=request.model_dump(mode="json"),
                timeout=self.timeout_seconds,
            )
            response.raise_for_status()
            body = response.json()
        except httpx.HTTPError as exc:
            # PDP unreachable, timed out, or returned an error status --
            # a down security layer must deny, not silently allow.
            return self._deny(f"PDP unavailable ({exc.__class__.__name__}): {exc}")

        decision = body.get("decision")
        if decision in ("ALLOW", "ALLOW_WITH_OBLIGATIONS"):
            return HookResult(action=HookAction.CONTINUE)
        return self._deny(f"PDP decision={decision} reason={body.get('reason')}")
