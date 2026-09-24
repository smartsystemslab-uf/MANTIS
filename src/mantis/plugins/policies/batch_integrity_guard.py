"""Batch integrity guard (Post-Paper Extension, coding plan §11: "Security
mechanism plugins -- guardrails, policy checks, isolation, rate limits, and
response filters evaluated through the same experiment framework").

Targets the back-office counterpart of route confusion: tool-parameter
mutation against apply_ledger_updates
(configs/attacks/wp5_back_office_tool_mutation.yaml), which silently
redirects a ledger post from a genuinely clean, validated batch
(EOD-2026-04-21-CLEAN) onto a second, real batch that already carries an
unresolved reconciliation discrepancy (EOD-2026-04-21-MISMATCH) -- the
second attack in the whole catalog that succeeds 5/5 with zero defense
anywhere in the repo, after route confusion.

A generic "is this batch_id a real batch" check cannot catch this: both
batches are real, both are seeded with ready_flag=1 and status="ready" --
the attack's whole trick is substituting one *valid-looking* batch for
another, not routing to something that doesn't exist. So, the same way
risk_aware_routing_guard re-checks a transaction's real risk score instead
of checking destination validity, this plugin independently re-checks the
target batch's own real expected-vs-posted totals (the same numbers
get_reconciliation_data exposes) and denies the ledger update if that
batch already shows an unresolved discrepancy -- regardless of which
batch_id the tool call actually names.
"""
from mantis.hooks import HookContext, HookAction, HookResult


class BatchIntegrityGuardPlugin:
    name = "batch_integrity_guard"
    supported_stages = {"tool"}

    def __init__(self, target_tool: str = "apply_ledger_updates", **kwargs):
        self.target_tool = target_tool
        self.kwargs = kwargs

    def apply(self, ctx: HookContext) -> HookResult:
        if ctx.metadata.get("specific_hook") != "before_tool" or ctx.target != self.target_tool:
            return HookResult(action=HookAction.CONTINUE)

        batch_id = (ctx.payload or {}).get("batch_id")
        if not batch_id:
            return HookResult(action=HookAction.CONTINUE)

        # Lazy import: mantis.banking.infra.repository pulls in
        # mantis.banking.settings, whose module-level `settings` singleton
        # reads environment variables at *import* time -- the same
        # import-order pitfall documented on risk_aware_routing_guard's own
        # lazy import, and the reason this one is lazy too.
        from mantis.banking.infra.repository import repo

        batch = repo.get_eod_batch(batch_id)
        if not batch:
            # Unknown batch is a data problem, not this guard's job to police.
            return HookResult(action=HookAction.CONTINUE)

        expected = batch.get("expected_total")
        posted = batch.get("ledger_posted_total")
        if expected is not None and posted is not None and expected != posted:
            return HookResult(
                action=HookAction.DENY,
                payload={
                    "error": (
                        f"blocked by batch_integrity_guard: batch {batch_id} has an unresolved "
                        f"discrepancy (expected {expected}, currently posted {posted}); ledger "
                        f"updates cannot proceed until this batch is reconciled"
                    )
                },
            )
        return HookResult(action=HookAction.CONTINUE)
