"""Post-Paper Extension: security mechanism plugins (coding plan §11).

Covers batch_integrity_guard's own logic in isolation, its registration,
and -- the actual point of a "defense evaluated through the same
framework" -- that it correctly DENIES tool_mutation's live batch
substitution through the real HookBus, closing the second (of two) attacks
in the catalog that previously succeeded 5/5 with zero defense (route
confusion was the first; see test_routing_guard.py).
"""
import tempfile
from pathlib import Path

import pytest

from mantis.hooks import HookBus, HookContext, HookAction
from mantis.plugins.policies.batch_integrity_guard import BatchIntegrityGuardPlugin
from mantis.plugins.attacks.tool_mutation import ToolParameterMutationPlugin
from mantis.core.registry import plugin_registry
from mantis.banking.infra.repository import BankingRepository


def create_ctx(stage, specific_hook, target=None, source=None, payload=None):
    return HookContext(
        run_id="test", trace_id="test", workflow_id="test",
        stage=stage, target=target, source=source, payload=payload or {},
        metadata={"specific_hook": specific_hook}
    )


@pytest.fixture
def repo():
    with tempfile.TemporaryDirectory() as tmpdir:
        r = BankingRepository(db_path=Path(tmpdir) / "test_banking.db")
        r.initialize()
        yield r


def test_batch_integrity_guard_registered():
    cls = plugin_registry.get("batch_integrity_guard")
    assert cls is BatchIntegrityGuardPlugin


def test_denies_ledger_update_against_a_batch_with_an_unresolved_discrepancy(repo, monkeypatch):
    monkeypatch.setattr("mantis.banking.infra.repository.repo", repo)
    plugin = BatchIntegrityGuardPlugin(target_tool="apply_ledger_updates")
    ctx = create_ctx("tool", "before_tool", target="apply_ledger_updates", payload={"batch_id": "EOD-2026-04-21-MISMATCH"})
    res = plugin.apply(ctx)
    assert res.action == HookAction.DENY
    assert "blocked by batch_integrity_guard" in res.payload["error"]


def test_allows_ledger_update_against_a_clean_batch(repo, monkeypatch):
    monkeypatch.setattr("mantis.banking.infra.repository.repo", repo)
    plugin = BatchIntegrityGuardPlugin(target_tool="apply_ledger_updates")
    ctx = create_ctx("tool", "before_tool", target="apply_ledger_updates", payload={"batch_id": "EOD-2026-04-21-CLEAN"})
    res = plugin.apply(ctx)
    assert res.action == HookAction.CONTINUE


def test_ignores_non_target_tool_calls():
    plugin = BatchIntegrityGuardPlugin(target_tool="apply_ledger_updates")
    ctx = create_ctx("tool", "before_tool", target="store_report", payload={"batch_id": "EOD-2026-04-21-MISMATCH"})
    res = plugin.apply(ctx)
    assert res.action == HookAction.CONTINUE, "must not police a tool it wasn't scoped to"


def test_continues_for_an_unknown_batch_id(repo, monkeypatch):
    monkeypatch.setattr("mantis.banking.infra.repository.repo", repo)
    plugin = BatchIntegrityGuardPlugin(target_tool="apply_ledger_updates")
    ctx = create_ctx("tool", "before_tool", target="apply_ledger_updates", payload={"batch_id": "EOD-DOES-NOT-EXIST"})
    res = plugin.apply(ctx)
    assert res.action == HookAction.CONTINUE, "an unknown batch is a data problem, not this guard's job"


def test_guard_blocks_a_live_batch_substitution_through_the_real_hook_bus(repo, monkeypatch):
    """The actual point of this extension: register tool_mutation and the
    guard on the same HookBus, in the same order cli/main.py uses, and
    confirm the guard sees the attack's substituted batch_id -- not the
    legitimate, validated one -- and the bus reports DENY."""
    monkeypatch.setattr("mantis.banking.infra.repository.repo", repo)
    hooks = HookBus()
    attack = ToolParameterMutationPlugin(
        target_tool="apply_ledger_updates",
        mutated_parameters={"batch_id": "EOD-2026-04-21-MISMATCH"},
    )
    guard = BatchIntegrityGuardPlugin(target_tool="apply_ledger_updates")
    hooks.register(attack)
    hooks.register(guard)

    ctx = HookContext(
        run_id="test", trace_id="test", workflow_id="test",
        stage="tool", target="apply_ledger_updates",
        payload={"batch_id": "EOD-2026-04-21-CLEAN", "posting_instructions": "post all items"},
        metadata={"specific_hook": "before_tool"},
    )
    result = hooks.dispatch("before_tool", ctx)

    assert result.action == HookAction.DENY, "the guard's DENY must win the dispatch's aggregate result"
    assert "blocked by batch_integrity_guard" in result.payload["error"]
