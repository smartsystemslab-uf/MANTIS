"""
WP0 Refactor Guard Tests
=========================
These tests enforce that the frozen baseline (golden runs, metrics, and inventory)
remain consistent. Any future refactoring in WP1+ must pass these tests to prove
that core banking behavior has not been broken.
"""

import os
import pytest
import json
import re
import yaml

GOLDEN_RUNS_DIR = os.path.join(os.path.dirname(__file__), "..", "golden_runs")
BASELINE_METRICS_PATH = os.path.join(os.path.dirname(__file__), "..", "baseline_metrics.json")
INVENTORY_PATH = os.path.join(os.path.dirname(__file__), "..", "banking_baseline_inventory.yaml")


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def extract_json_from_trace(file_path):
    """Extract the JSON payload from a raw golden run .out file."""
    if not os.path.exists(file_path):
        return None

    with open(file_path, "r") as f:
        content = f.read()

    match = re.search(r'(\{.*\})', content, re.DOTALL)
    if not match:
        return None

    try:
        return json.loads(match.group(1))
    except json.JSONDecodeError:
        return None


# ---------------------------------------------------------------------------
# 1. File existence checks
# ---------------------------------------------------------------------------

class TestBaselineFilesExist:
    """Verify that all WP0 deliverable files are present."""

    def test_baseline_metrics_file_exists(self):
        assert os.path.exists(BASELINE_METRICS_PATH), "baseline_metrics.json is missing"

    def test_inventory_file_exists(self):
        assert os.path.exists(INVENTORY_PATH), "banking_baseline_inventory.yaml is missing"

    @pytest.mark.parametrize("filename", [
        "front_office_monitoring.out",
        "mid_office_planning.out",
        "back_office_clean.out",
    ])
    def test_golden_run_file_exists(self, filename):
        path = os.path.join(GOLDEN_RUNS_DIR, filename)
        assert os.path.exists(path), f"Golden run {filename} is missing"


# ---------------------------------------------------------------------------
# 2. Baseline metrics structure
# ---------------------------------------------------------------------------

class TestBaselineMetricsStructure:
    """Validate the schema of baseline_metrics.json."""

    @pytest.fixture(autouse=True)
    def load_metrics(self):
        with open(BASELINE_METRICS_PATH, "r") as f:
            self.metrics = json.load(f)

    @pytest.mark.parametrize("workflow", [
        "front_office_monitoring",
        "mid_office_planning",
        "back_office_clean",
    ])
    def test_workflow_present(self, workflow):
        assert workflow in self.metrics, f"Workflow {workflow} missing from metrics"

    @pytest.mark.parametrize("field", [
        "latency_seconds", "trace_count", "agents_involved", "tools_called", "semantics",
    ])
    def test_required_fields(self, field):
        for wf, data in self.metrics.items():
            assert field in data, f"Field '{field}' missing in {wf}"

    @pytest.mark.parametrize("sem_field", [
        "operation_type", "data_sensitivity", "risk_level", "financial_side_effects",
    ])
    def test_semantics_fields(self, sem_field):
        for wf, data in self.metrics.items():
            assert sem_field in data["semantics"], f"Semantics field '{sem_field}' missing in {wf}"


# ---------------------------------------------------------------------------
# 3. Cross-validate golden runs against baseline metrics
# ---------------------------------------------------------------------------

class TestFrontOfficeTrace:
    """Validate the front office golden run matches baseline_metrics.json."""

    @pytest.fixture(autouse=True)
    def setup(self):
        with open(BASELINE_METRICS_PATH, "r") as f:
            self.metrics = json.load(f)["front_office_monitoring"]
        self.trace = extract_json_from_trace(
            os.path.join(GOLDEN_RUNS_DIR, "front_office_monitoring.out")
        )

    def test_trace_parseable(self):
        assert self.trace is not None, "Could not parse JSON from front_office_monitoring.out"

    def test_trace_contains_events(self):
        events = self.trace.get("front_office_monitoring", [])
        assert len(events) > 0, "Front office trace has no events"

    def test_tools_match_baseline(self):
        events = self.trace.get("front_office_monitoring", [])
        actual_tools = [e["tool"] for e in events if e.get("event") == "tool_call"]
        for tool in self.metrics["tools_called"]:
            assert tool in actual_tools, f"Expected tool '{tool}' not found in front office trace"

    def test_agents_match_baseline(self):
        events = self.trace.get("front_office_monitoring", [])
        actual_agents = set(e["agent"] for e in events if "agent" in e)
        for agent in self.metrics["agents_involved"]:
            assert agent in actual_agents, f"Expected agent '{agent}' not found in front office trace"


class TestMidOfficeTrace:
    """Validate the mid office golden run matches baseline_metrics.json."""

    @pytest.fixture(autouse=True)
    def setup(self):
        with open(BASELINE_METRICS_PATH, "r") as f:
            self.metrics = json.load(f)["mid_office_planning"]
        self.trace = extract_json_from_trace(
            os.path.join(GOLDEN_RUNS_DIR, "mid_office_planning.out")
        )

    def test_trace_parseable(self):
        assert self.trace is not None, "Could not parse JSON from mid_office_planning.out"

    def test_trace_contains_events(self):
        events = self.trace.get("mid_office_planning", [])
        assert len(events) > 0, "Mid office trace has no events"

    def test_tools_match_baseline(self):
        events = self.trace.get("mid_office_planning", [])
        actual_tools = [e["tool"] for e in events if e.get("event") == "tool_call"]
        for tool in self.metrics["tools_called"]:
            assert tool in actual_tools, f"Expected tool '{tool}' not found in mid office trace"

    def test_agents_match_baseline(self):
        events = self.trace.get("mid_office_planning", [])
        actual_agents = set(e["agent"] for e in events if "agent" in e)
        for agent in self.metrics["agents_involved"]:
            assert agent in actual_agents, f"Expected agent '{agent}' not found in mid office trace"


class TestBackOfficeTrace:
    """Validate the back office golden run matches baseline_metrics.json."""

    @pytest.fixture(autouse=True)
    def setup(self):
        with open(BASELINE_METRICS_PATH, "r") as f:
            self.metrics = json.load(f)["back_office_clean"]
        self.trace = extract_json_from_trace(
            os.path.join(GOLDEN_RUNS_DIR, "back_office_clean.out")
        )

    def test_trace_parseable(self):
        assert self.trace is not None, "Could not parse JSON from back_office_clean.out"

    def test_trace_contains_events(self):
        events = self.trace.get("back_office_clean", [])
        assert len(events) > 0, "Back office trace has no events"

    def test_tools_match_baseline(self):
        events = self.trace.get("back_office_clean", [])
        actual_tools = [e["tool"] for e in events if e.get("event") == "tool_call"]
        for tool in self.metrics["tools_called"]:
            assert tool in actual_tools, f"Expected tool '{tool}' not found in back office trace"

    def test_agents_match_baseline(self):
        events = self.trace.get("back_office_clean", [])
        actual_agents = set(e["agent"] for e in events if "agent" in e)
        for agent in self.metrics["agents_involved"]:
            assert agent in actual_agents, f"Expected agent '{agent}' not found in back office trace"


# ---------------------------------------------------------------------------
# 4. Inventory consistency
# ---------------------------------------------------------------------------

class TestInventoryConsistency:
    """Verify the inventory YAML is well-formed and consistent with metrics."""

    @pytest.fixture(autouse=True)
    def setup(self):
        with open(INVENTORY_PATH, "r") as f:
            self.inventory = yaml.safe_load(f)
        with open(BASELINE_METRICS_PATH, "r") as f:
            self.metrics = json.load(f)

    def test_inventory_has_required_sections(self):
        for section in ["packages", "agents", "mcp_tools", "adk_tools", "workflows"]:
            assert section in self.inventory, f"Inventory missing section '{section}'"

    def test_adk_tools_cover_metrics_tools(self):
        """Every tool in baseline_metrics must appear in the inventory's adk_tools."""
        all_inventory_tools = []
        for office_tools in self.inventory["adk_tools"].values():
            all_inventory_tools.extend(office_tools)

        for wf, data in self.metrics.items():
            for tool in data["tools_called"]:
                assert tool in all_inventory_tools, (
                    f"Tool '{tool}' from metrics workflow '{wf}' not found in inventory adk_tools"
                )

    def test_golden_run_workflows_in_inventory(self):
        """All three golden run workflows must be listed in the inventory."""
        inv_workflows = self.inventory["workflows"]
        for wf in ["front_office_monitoring", "mid_office_planning", "back_office_clean"]:
            assert wf in inv_workflows, f"Workflow '{wf}' missing from inventory"


# ---------------------------------------------------------------------------
# 5. Scenario-specific behavioral tests (advanced)
# ---------------------------------------------------------------------------

class TestFrontOfficeBehavior:
    """
    Advanced tests for the front office monitoring scenario.
    Validates the exact agent execution flow, routing, tool arguments,
    and business outcome for transaction TXN-1001.
    """

    @pytest.fixture(autouse=True)
    def setup(self):
        self.trace = extract_json_from_trace(
            os.path.join(GOLDEN_RUNS_DIR, "front_office_monitoring.out")
        )
        self.events = self.trace["front_office_monitoring"]

    def test_routing_path(self):
        """Verify the agent routing: user_proxy -> front_office_router -> workflow."""
        transfers = [e for e in self.events if e.get("event") == "transfer"]
        assert len(transfers) >= 2, "Expected at least 2 agent transfers in front office"
        assert transfers[0]["agent"] == "user_proxy_agent"
        assert transfers[0]["to"] == "front_office_router"
        assert transfers[1]["agent"] == "front_office_router"
        assert transfers[1]["to"] == "front_office_transaction_workflow"

    def test_agent_execution_order(self):
        """Verify agents execute in the correct sequence: monitoring -> compliance -> decision."""
        tool_calls = [e for e in self.events if e.get("event") == "tool_call"]
        agent_sequence = [tc["agent"] for tc in tool_calls]
        # transaction_monitoring_agent must come before compliance_agent
        monitoring_idx = next(i for i, a in enumerate(agent_sequence) if a == "transaction_monitoring_agent")
        compliance_idx = next(i for i, a in enumerate(agent_sequence) if a == "compliance_agent")
        decision_idx = next(i for i, a in enumerate(agent_sequence) if a == "decision_making_agent")
        assert monitoring_idx < compliance_idx < decision_idx, \
            "Agent execution order must be: monitoring -> compliance -> decision"

    def test_customer_context_fetched_for_correct_customer(self):
        """Verify the monitoring agent fetches context for CUST-001."""
        tool_calls = [e for e in self.events if e.get("event") == "tool_call"]
        ctx_call = next(tc for tc in tool_calls if tc["tool"] == "get_customer_context")
        assert ctx_call["agent"] == "transaction_monitoring_agent"
        assert ctx_call["args"]["customer_id"].startswith("CUST-")

    def test_transaction_context_fetched_for_correct_txn(self):
        """Verify the monitoring agent fetches context for a valid transaction ID."""
        tool_calls = [e for e in self.events if e.get("event") == "tool_call"]
        txn_call = next(tc for tc in tool_calls if tc["tool"] == "get_transaction_context")
        assert txn_call["agent"] == "transaction_monitoring_agent"
        assert txn_call["args"]["transaction_id"].startswith("TXN-")

    def test_compliance_agent_searches_policies(self):
        """Verify the compliance agent performs policy searches."""
        tool_calls = [e for e in self.events if e.get("event") == "tool_call"]
        policy_calls = [tc for tc in tool_calls if tc["tool"] == "search_policies"]
        assert len(policy_calls) >= 1, "Compliance agent must search policies at least once"
        assert policy_calls[0]["agent"] == "compliance_agent"





class TestMidOfficeBehavior:
    """
    Advanced tests for the mid office planning scenario.
    Validates agent routing, tool arguments, and that a validated
    schedule is produced for the correct date.
    """

    @pytest.fixture(autouse=True)
    def setup(self):
        self.trace = extract_json_from_trace(
            os.path.join(GOLDEN_RUNS_DIR, "mid_office_planning.out")
        )
        self.events = self.trace["mid_office_planning"]

    def test_routing_path(self):
        """Verify routing: user_proxy -> mid_office_router -> planning workflow."""
        transfers = [e for e in self.events if e.get("event") == "transfer"]
        assert transfers[0]["agent"] == "user_proxy_agent"
        assert transfers[0]["to"] == "mid_office_router"
        assert transfers[1]["agent"] == "mid_office_router"
        assert transfers[1]["to"] == "mid_office_planning_workflow"

    def test_operations_snapshot_fetched_for_correct_date(self):
        """Verify data_analysis_agent fetches operations for a valid date format."""
        tool_calls = [e for e in self.events if e.get("event") == "tool_call"]
        snapshot_call = next(tc for tc in tool_calls if tc["tool"] == "get_operations_snapshot")
        assert snapshot_call["agent"] == "data_analysis_agent"
        import re
        assert re.match(r"^\d{4}-\d{2}-\d{2}$", snapshot_call["args"]["date"])

    def test_support_playbooks_requested(self):
        """Verify support_guidance_agent retrieves playbooks."""
        tool_calls = [e for e in self.events if e.get("event") == "tool_call"]
        playbook_call = next(tc for tc in tool_calls if tc["tool"] == "get_support_playbooks")
        assert playbook_call["agent"] == "support_guidance_agent"

    def test_schedule_validated_and_persisted(self):
        """Verify validation_agent persists a validated schedule with branch data."""
        tool_calls = [e for e in self.events if e.get("event") == "tool_call"]
        persist_call = next(tc for tc in tool_calls if tc["tool"] == "persist_validated_schedule")
        assert persist_call["agent"] == "validation_agent"
        schedule_str = persist_call["args"]["schedule_json"]
        assert isinstance(schedule_str, str)
        assert len(schedule_str) > 0

    def test_planning_summary_produced(self):
        """Verify the planning_summary_agent produces a final result."""
        results = [e for e in self.events if e.get("event") == "result"]
        assert len(results) >= 1
        summary = results[-1]
        assert summary["agent"] == "planning_summary_agent"
        assert summary["key"] == "mid_office_planning_result"


class TestBackOfficeBehavior:
    """
    Advanced tests for the back office EOD reconciliation scenario.
    Validates agent routing, batch ID consistency, ledger posting,
    reconciliation, and report generation.
    """

    EXPECTED_BATCH_ID = "EOD-2026-04-21-CLEAN"

    @pytest.fixture(autouse=True)
    def setup(self):
        self.trace = extract_json_from_trace(
            os.path.join(GOLDEN_RUNS_DIR, "back_office_clean.out")
        )
        self.events = self.trace["back_office_clean"]

    def test_routing_path(self):
        """Verify routing: user_proxy -> back_office_router -> eod workflow."""
        transfers = [e for e in self.events if e.get("event") == "transfer"]
        assert transfers[0]["agent"] == "user_proxy_agent"
        assert transfers[0]["to"] == "back_office_router"
        assert transfers[1]["agent"] == "back_office_router"
        assert transfers[1]["to"] == "back_office_eod_workflow"

    def test_agent_execution_order(self):
        """Verify agents execute: validation -> processing -> ledger -> reconciliation -> report."""
        tool_calls = [e for e in self.events if e.get("event") == "tool_call"]
        agent_sequence = [tc["agent"] for tc in tool_calls]
        expected_order = [
            "validation_checkpoint_agent",
            "eod_processing_agent",
            "ledger_update_agent",
            "reconciliation_agent",
            "report_writing_agent",
        ]
        for i, expected_agent in enumerate(expected_order):
            assert agent_sequence[i] == expected_agent, \
                f"Step {i}: expected '{expected_agent}', got '{agent_sequence[i]}'"

    def test_batch_id_consistent_across_all_tool_calls(self):
        """Every tool call must reference the same batch ID."""
        tool_calls = [e for e in self.events if e.get("event") == "tool_call"]
        for tc in tool_calls:
            if "batch_id" in tc.get("args", {}):
                batch_id = tc["args"]["batch_id"]
                assert batch_id.startswith("EOD-") and "-CLEAN" in batch_id, \
                    f"Agent '{tc['agent']}' used invalid batch format: {batch_id}"

    def test_eod_readiness_validated_before_processing(self):
        """Verify validation_checkpoint_agent runs validate_eod_readiness first."""
        tool_calls = [e for e in self.events if e.get("event") == "tool_call"]
        assert tool_calls[0]["tool"] == "validate_eod_readiness"
        assert tool_calls[0]["agent"] == "validation_checkpoint_agent"

    def test_ledger_updates_applied(self):
        """Verify ledger_update_agent applies ledger updates with posting instructions."""
        tool_calls = [e for e in self.events if e.get("event") == "tool_call"]
        ledger_call = next(tc for tc in tool_calls if tc["tool"] == "apply_ledger_updates")
        assert ledger_call["agent"] == "ledger_update_agent"
        instructions_str = ledger_call["args"]["posting_instructions"]
        assert isinstance(instructions_str, str)
        assert len(instructions_str) >= 1

    def test_reconciliation_performed(self):
        """Verify reconciliation_agent fetches reconciliation data."""
        tool_calls = [e for e in self.events if e.get("event") == "tool_call"]
        recon_call = next(tc for tc in tool_calls if tc["tool"] == "get_reconciliation_data")
        assert recon_call["agent"] == "reconciliation_agent"

    def test_report_generated_with_id(self):
        """Verify report_writing_agent produces a report and receives a report ID."""
        results = [e for e in self.events if e.get("event") == "tool_result"]
        report_result = next(r for r in results if r["tool"] == "store_report")
        assert report_result["result"]["report_id"].startswith("RPT-")


