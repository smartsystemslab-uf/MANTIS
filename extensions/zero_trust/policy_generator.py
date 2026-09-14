"""PEP/PDP policy generator (Post-Paper Extension, coding plan §11: "Zero
Trust Backplane -- consume application inventory and control-point
metadata to generate or insert protection mechanisms").

Reads MANTIS's live BankingSystemInventory -- the same inventory `mantis
--inventory` prints -- and produces a default-deny policy scoping which
tools each banking domain's agents may call. This is the "PEP/PDP
generator reading inventory() to scope permits per agent/tool/domain"
the extension-point README (README.md, this directory) describes; it is
intentionally domain-level, not per-agent, because per-agent tool
assignment isn't part of the public BankingSystemInventory contract today
(see the docstring on generate_default_deny_policy for why that's the
honest scope rather than something finer this slice doesn't actually do).
"""
import json
import sys

from mantis.runtime.adapter import NativeBankingAdapter
from mantis.runtime.interfaces import BankingSystemInventory


def generate_default_deny_policy(inventory: BankingSystemInventory = None) -> dict:
    """Default-deny: a tool call is permitted only if the calling agent's
    domain declares that tool in its inventory. Everything else -- most
    importantly, a domain's agent calling a *different* domain's tool,
    the lateral-movement case a compromised or misrouted agent would
    attempt -- is denied unless explicitly allowed.

    Scoped per-domain rather than per-agent: BankingSystemInventory
    reports domains -> {agents, tools}, not which of a domain's tools each
    of its individual agents actually calls. A real PDP with access to
    each agent's own declared `tools=[...]` (LlmAgent's own attribute,
    not currently surfaced through the public inventory interface) could
    scope tighter; this generator is honest about working from the
    interface that exists today, not one that would require a MANTIS
    core change to support.
    """
    inventory = inventory or NativeBankingAdapter().inventory()
    policy = {
        "default": "deny",
        "domains": {},
        # transfer_to_agent is the framework's own routing tool, needed by
        # every domain to reach its own agents at all -- denying it would
        # break routing itself, not enforce a security boundary.
        "always_allowed_tools": ["transfer_to_agent"],
    }
    for domain, data in inventory.domains.items():
        policy["domains"][domain] = {
            "agents": sorted(data.get("agents", [])),
            "allowed_tools": sorted(data.get("tools", [])),
        }
    return policy


def to_zt_manifest_subjects(inventory: BankingSystemInventory = None, environment: str = "mantis") -> list:
    """Maps MANTIS's live inventory onto the canonical/runtime-binding shape
    used by the independently-developed Citi Zero Trust Backplane
    (github.com/smartsystemslab-uf/Citi_P3_Zero_Trust_Backplane)'s Unified
    Interface Standard -- e.g. its example manifest's
    `agent.front_office.fraud` subject, bound via
    `bindings.<environment>.runtime_id: fraud_agent`.

    That project's Tasks 1-2 discover this same agent/tool/domain
    information by *scanning Citi's source code*; MANTIS already reports
    it structurally and live via `inventory()`, so for a MANTIS-based
    system this function is a substitute data source for that scan, not a
    reimplementation of the Backplane itself. A real integration would use
    this to seed (part of) a `zt_manifest.yaml`, then let that project's
    real Task 3 (PEP generation) and Task 4 (signed PDP) make the actual
    authorization decision -- MANTIS's `PolicyPlugin.apply()` is exactly
    the seam where a call to that real PDP would replace this file's own
    (much simpler) default-deny-by-domain logic; see
    enforcement_plugin.py's docstring.
    """
    inventory = inventory or NativeBankingAdapter().inventory()
    subjects = []
    for domain, data in inventory.domains.items():
        for agent in sorted(data.get("agents", [])):
            subjects.append({
                "id": f"agent.{domain}.{agent}",
                "type": "agent",
                "domain": domain,
                "bindings": {environment: {"runtime_id": agent}},
            })
    return subjects


def write_policy(output_path: str) -> dict:
    policy = generate_default_deny_policy()
    with open(output_path, "w") as f:
        json.dump(policy, f, indent=2)
    return policy


if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else "zero_trust_policy.json"
    policy = write_policy(out)
    print(f"Zero Trust policy written to {out}")
    print(json.dumps(policy, indent=2))
