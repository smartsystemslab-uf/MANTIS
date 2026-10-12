"""Generates extensions/zero_trust/config/{identities,resources}.yaml and
extensions/zero_trust/policy_store/mantis_default_deny_by_domain.yaml from
MANTIS's own live system -- DOMAIN_AGENTS (src/mantis/banking/domains.py)
and _DOMAIN_TOOL_NAMES (src/mantis/runtime/adapter.py) -- rather than from
the real Zero Trust Backplane's own scanner, which was built against an
older, now-gone checkout of the banking system.

The generated policy is deliberately simple and auditable: an agent may act
on a tool/resource in its own domain; everything else is an implicit deny
(the real zt_backplane PDP's own default when no policy matches --
"default_deny_no_matching_policy"). This is the same guarantee the local
representative slice validated exhaustively (770 agent/tool pairs, 100%
correctly enforced) before this integration, just now expressed in the real
PolicyBundle schema and evaluated by the real signed PDP engine instead of
a stand-in.

Run after any change to MANTIS's agents, tools, or domains, then re-sign
with bootstrap_keys.py (which also (re)signs every policy_store/*.yaml):

    python extensions/zero_trust/generate_policy.py
    python extensions/zero_trust/bootstrap_keys.py
"""
import sys
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from mantis.banking.domains import DOMAIN_AGENTS  # noqa: E402
from mantis.runtime.adapter import _DOMAIN_TOOL_NAMES  # noqa: E402
from mantis.banking.tool_semantics import TOOL_SEMANTICS  # noqa: E402

OUT = Path(__file__).resolve().parent
_CLASSIFICATION = {"low": "internal", "medium": "confidential", "high": "restricted"}


def _agent_id(domain: str, agent: str) -> str:
    return f"agent.{domain}.{agent}"


def _resource_id(domain: str, tool: str) -> str:
    return f"resource.{domain}.{tool}"


def build_identities() -> dict:
    identities = []
    for domain, agents in sorted(DOMAIN_AGENTS.items()):
        for agent in sorted(agents):
            identities.append({
                "id": agent,
                "canonical_id": _agent_id(domain, agent),
                "type": "agent",
                "roles": [agent],
                "domain": domain,
                "enabled": True,
                "attributes": {"source": "mantis_live_inventory"},
            })
    return {"identities": identities}


def build_resources() -> dict:
    resources = []
    for domain, tools in sorted(_DOMAIN_TOOL_NAMES.items()):
        for tool in sorted(tools):
            sem = TOOL_SEMANTICS.get(tool, {})
            op = sem.get("operation_type", "read")
            resources.append({
                # Domain-qualified, not the bare tool name: a tool used by more than one
                # domain (search_policies: front + mid office) would otherwise collide --
                # ResourceCatalog requires every record's own `id` to be unique. The
                # caller (ZeroTrustEnforcementPlugin) passes this same qualified string
                # as resource_runtime_id.
                "id": f"{domain}.{tool}",
                "canonical_id": _resource_id(domain, tool),
                "actions": [op],
                "domain": domain,
                "classification": _CLASSIFICATION.get(sem.get("data_sensitivity", "medium"), "confidential"),
                "critical": bool(sem.get("financial_side_effect", False)),
                "attributes": {"source": "mantis_live_inventory", "risk_level": sem.get("risk_level", "medium")},
            })
    return {"resources": resources}


def build_policy() -> dict:
    policies = []
    for domain, agents in sorted(DOMAIN_AGENTS.items()):
        subjects = sorted(_agent_id(domain, a) for a in agents)
        tools = _DOMAIN_TOOL_NAMES.get(domain, [])
        resources = sorted(_resource_id(domain, t) for t in tools)
        actions = sorted({TOOL_SEMANTICS.get(t, {}).get("operation_type", "read") for t in tools})
        if not subjects or not resources:
            continue
        policies.append({
            "id": f"policy.mantis.{domain}_same_domain_access",
            "description": f"MANTIS default-deny-by-domain: a {domain} agent may call a {domain} tool. "
                            "Anything not matched here (cross-domain, or an unknown subject/resource) "
                            "is denied by the PDP's own default (default_deny_no_matching_policy).",
            "priority": 100,
            "effect": "ALLOW",
            "match": {"subjects": subjects, "resources": resources, "actions": actions},
            "obligations": [],
            "enabled": True,
        })
    return {
        "apiVersion": "ztb/v1alpha1",
        "kind": "PolicyBundle",
        "metadata": {"id": "bundle.mantis_default_deny_by_domain", "version": "1.0.0",
                     "domain": "mantis", "status": "confirmed"},
        "policies": policies,
    }


def main():
    (OUT / "config").mkdir(parents=True, exist_ok=True)
    (OUT / "policy_store").mkdir(parents=True, exist_ok=True)
    identities, resources, policy = build_identities(), build_resources(), build_policy()
    (OUT / "config" / "identities.yaml").write_text(yaml.safe_dump(identities, sort_keys=False))
    (OUT / "config" / "resources.yaml").write_text(yaml.safe_dump(resources, sort_keys=False))
    (OUT / "policy_store" / "mantis_default_deny_by_domain.yaml").write_text(yaml.safe_dump(policy, sort_keys=False))
    print(f"{len(identities['identities'])} identities, {len(resources['resources'])} resources, "
          f"{len(policy['policies'])} domain policies written to {OUT}")
    print("Run extensions/zero_trust/bootstrap_keys.py next to (re)sign the policy bundle.")


if __name__ == "__main__":
    main()
