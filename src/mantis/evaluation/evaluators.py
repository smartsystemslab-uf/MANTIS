import json
from pathlib import Path
from typing import Dict, Any, List

class TraceEvaluator:
    def __init__(self, run_dir: str):
        self.run_dir = Path(run_dir)
        self.trace_file = self.run_dir / "traces.jsonl"
        self.events: List[Dict[str, Any]] = []
        if self.trace_file.exists():
            with open(self.trace_file, "r") as f:
                for line in f:
                    if line.strip():
                        self.events.append(json.loads(line))

    def evaluate_all(self) -> Dict[str, Any]:
        if not self.events:
            return {"error": "No traces found."}

        return {
            "trace_completeness": self.evaluate_completeness(),
            "tool_use_correctness": self.evaluate_tool_use(),
            "workflow_outcome": self.evaluate_workflow_outcome()
        }

    def evaluate_completeness(self) -> Dict[str, Any]:
        event_types = [e.get("event_type") for e in self.events]
        has_workflow_start = "WORKFLOW_START" in event_types
        has_workflow_end = "WORKFLOW_END" in event_types
        has_agent_start = "AGENT_START" in event_types

        # Tools are not strictly required if the workflow didn't need them,
        # but for MANTIS testbed we expect at least some events if it ran successfully.

        is_complete = has_workflow_start and has_workflow_end and has_agent_start

        domain = None
        workflow_id = None
        for e in self.events:
            if e.get("event_type") == "WORKFLOW_START":
                domain = e.get("business_domain")
                workflow_id = e.get("workflow_id")
                break

        return {
            "score": 1.0 if is_complete else 0.0,
            "has_workflow_start": has_workflow_start,
            "has_workflow_end": has_workflow_end,
            "has_agent_start": has_agent_start,
            "total_events": len(self.events),
            "business_domain": domain,
            "workflow_id": workflow_id,
        }

    def evaluate_tool_use(self) -> Dict[str, Any]:
        # We can read expected_tools and forbidden_tools from run_manifest.json
        manifest_file = self.run_dir / "run_manifest.json"
        expected_tools = []
        forbidden_tools = []
        if manifest_file.exists():
            with open(manifest_file, "r") as f:
                manifest = json.load(f)
                config = manifest.get("config", {})
                eval_config = config.get("evaluation", {})
                if eval_config:
                    expected_tools = eval_config.get("expected_tools", [])
                    forbidden_tools = eval_config.get("forbidden_tools", [])

        actual_tools = set(
            e.get("tool_name") for e in self.events 
            if e.get("event_type") == "TOOL_CALL"
        )

        missing_expected = [t for t in expected_tools if t not in actual_tools]
        used_forbidden = [t for t in forbidden_tools if t in actual_tools]

        score = 1.0
        if missing_expected or used_forbidden:
            score = 0.0

        return {
            "score": score,
            "actual_tools": list(actual_tools),
            "missing_expected": missing_expected,
            "used_forbidden": used_forbidden
        }

    def evaluate_workflow_outcome(self) -> Dict[str, Any]:
        manifest_file = self.run_dir / "run_manifest.json"
        expected_outcome = None
        if manifest_file.exists():
            with open(manifest_file, "r") as f:
                manifest = json.load(f)
                config = manifest.get("config", {})
                eval_config = config.get("evaluation", {})
                if eval_config:
                    expected_outcome = eval_config.get("expected_terminal_state")

        actual_outcome = None
        for e in self.events:
            if e.get("event_type") == "WORKFLOW_END":
                actual_outcome = e.get("outcome")

        # If expected_outcome is not defined, we just return actual
        score = 1.0
        if expected_outcome and actual_outcome != expected_outcome:
            score = 0.0

        return {
            "score": score,
            "expected_outcome": expected_outcome,
            "actual_outcome": actual_outcome
        }
