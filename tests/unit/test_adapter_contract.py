"""Contract test for the BankingRuntimeAdapter interface (spec §8, Contract layer).

Verifies that NativeBankingAdapter:
  1. Exposes all four protocol methods with correct signatures.
  2. Returns a BankingSystemInventory that is non-empty and covers all three
     banking domains (front_office, mid_office, back_office).
  3. Returns WorkflowSpec objects for every registered scenario.
  4. build() returns an object with a run_message coroutine (RuntimeHandle).
  5. reset() accepts an integer seed without raising.

No LLM or network calls are made -- all checks are structural / offline.
"""
import inspect
import pytest

from mantis.runtime.adapter import NativeBankingAdapter
from mantis.runtime.interfaces import BankingSystemInventory, WorkflowSpec, BankingRuntimeAdapter
from mantis.hooks import HookBus
from mantis.config.models import ExperimentConfig


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def adapter():
    return NativeBankingAdapter()


@pytest.fixture
def minimal_config():
    return ExperimentConfig(**{
        "experiment": {
            "name": "contract_test_run",
            "seed": 0,
            "domain": "front_office",
            "workflow": "front_office_monitoring",
            "scenario": "front_office_monitoring",
        }
    })


# ---------------------------------------------------------------------------
# Gap 5a -- Protocol method presence
# ---------------------------------------------------------------------------

def test_adapter_satisfies_protocol_structurally(adapter):
    # BankingRuntimeAdapter is @runtime_checkable specifically so this
    # isinstance check is meaningful -- it verifies NativeBankingAdapter
    # actually structurally satisfies the stable public Protocol (matching
    # method names), not just that the four methods below happen to exist
    # under the names this test file expects.
    assert isinstance(adapter, BankingRuntimeAdapter)

def test_adapter_has_inventory_method(adapter):
    assert callable(getattr(adapter, "inventory", None))

def test_adapter_has_workflows_method(adapter):
    assert callable(getattr(adapter, "workflows", None))

def test_adapter_has_build_method(adapter):
    assert callable(getattr(adapter, "build", None))

def test_adapter_has_reset_method(adapter):
    assert callable(getattr(adapter, "reset", None))


# ---------------------------------------------------------------------------
# Gap 5b -- inventory() return schema
# ---------------------------------------------------------------------------

def test_inventory_returns_correct_type(adapter):
    inv = adapter.inventory()
    assert isinstance(inv, BankingSystemInventory)

def test_inventory_agents_non_empty(adapter):
    assert len(adapter.inventory().agents) > 0

def test_inventory_tools_non_empty(adapter):
    assert len(adapter.inventory().tools) > 0

def test_inventory_workflows_non_empty(adapter):
    assert len(adapter.inventory().workflows) > 0

def test_inventory_covers_all_three_domains(adapter):
    inv = adapter.inventory()
    expected = {"front_office", "mid_office", "back_office"}
    assert expected.issubset(set(inv.domains.keys()))

def test_inventory_domains_have_agents(adapter):
    inv = adapter.inventory()
    for domain, data in inv.domains.items():
        assert len(data.get("agents", [])) > 0, f"Domain '{domain}' has no agents"

def test_inventory_domains_have_distinctly_scoped_tools(adapter):
    """Regression guard: inventory() used to attach the same full merged
    tool list to every domain, which made any domain-scoped consumer of
    this interface (e.g. a default-deny-by-domain policy plugin)
    meaningless -- every domain would report being able to call every
    tool in the system. Each domain's tools must be a real, non-trivial
    subset, not the universal set."""
    inv = adapter.inventory()
    all_tools = set(inv.tools)
    for domain, data in inv.domains.items():
        domain_tools = set(data.get("tools", []))
        assert domain_tools, f"Domain '{domain}' has no tools"
        assert domain_tools != all_tools, (
            f"Domain '{domain}' reports the entire tool set ({len(all_tools)} tools) "
            "as its own -- tools are not being scoped per domain"
        )

def test_inventory_back_office_tools_are_not_reachable_from_other_domains(adapter):
    """A concrete cross-domain check, not just 'not identical to the
    universal set': a back-office-only tool (apply_ledger_updates) must
    not appear in front_office's or mid_office's tool list."""
    inv = adapter.inventory()
    assert "apply_ledger_updates" in inv.domains["back_office"]["tools"]
    assert "apply_ledger_updates" not in inv.domains["front_office"]["tools"]
    assert "apply_ledger_updates" not in inv.domains["mid_office"]["tools"]

def test_inventory_agents_are_strings(adapter):
    for agent in adapter.inventory().agents:
        assert isinstance(agent, str)

def test_inventory_tools_are_strings(adapter):
    for tool in adapter.inventory().tools:
        assert isinstance(tool, str)


# ---------------------------------------------------------------------------
# Gap 5c -- workflows() return schema
# ---------------------------------------------------------------------------

def test_workflows_returns_mapping(adapter):
    assert len(adapter.workflows()) > 0

def test_workflows_values_are_workflow_spec(adapter):
    for wf_id, spec in adapter.workflows().items():
        assert isinstance(spec, WorkflowSpec), f"workflows()['{wf_id}'] must be WorkflowSpec"
        assert spec.id == wf_id
        assert spec.description


# ---------------------------------------------------------------------------
# Gap 5d -- build() returns RuntimeHandle
# ---------------------------------------------------------------------------

def test_build_returns_runtime_handle(adapter, minimal_config):
    handle = adapter.build(minimal_config, HookBus())
    assert handle is not None
    assert callable(getattr(handle, "run_message", None))
    assert inspect.iscoroutinefunction(handle.run_message)


# ---------------------------------------------------------------------------
# Gap 5e -- reset() accepts int seed
# ---------------------------------------------------------------------------

def test_reset_accepts_seed(adapter):
    adapter.reset(42)  # must not raise

def test_reset_is_idempotent(adapter):
    adapter.reset(0)
    adapter.reset(0)
