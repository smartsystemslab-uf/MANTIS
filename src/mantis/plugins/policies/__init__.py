"""Policy/behavior-modification plugin interface.

Interface only for Paper 1 (see coding plan section 3.2, Explicitly
Deferred: "a complete defense suite or a claim that the testbed prevents
attacks"). PolicyPlugin has the same shape as ExperimentPlugin -- it exists
as its own protocol so a future guardrail/policy-check implementation isn't
forced to masquerade as an attack plugin, without MANTIS shipping a concrete
policy engine in this release.
"""
from typing import Protocol, Set
from mantis.hooks import HookContext, HookResult


class PolicyPlugin(Protocol):
    name: str
    supported_stages: Set[str]

    def apply(self, ctx: HookContext) -> HookResult: ...
