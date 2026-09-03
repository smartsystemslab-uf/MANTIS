from typing import Dict, Any, TypeVar, Generic

T = TypeVar('T')

class Registry(Generic[T]):
    def __init__(self, name: str):
        self.name = name
        self._registry: Dict[str, T] = {}

    def register(self, key: str, item: T) -> None:
        if key in self._registry:
            raise ValueError(f"Key '{key}' already registered in {self.name}")
        self._registry[key] = item

    def get(self, key: str) -> T:
        if key not in self._registry:
            raise KeyError(f"Key '{key}' not found in {self.name}. Available: {list(self._registry.keys())}")
        return self._registry[key]

    def all(self) -> Dict[str, T]:
        return self._registry.copy()

domain_registry = Registry[Any]("Domains")
scenario_registry = Registry[str]("Scenarios")
workflow_registry = Registry[str]("Workflows")
plugin_registry = Registry[Any]("Plugins")
exporter_registry = Registry[Any]("Exporters")
evaluator_registry = Registry[Any]("Evaluators")

from mantis.plugins.attacks.mock_attack import MockAttackPlugin
from mantis.plugins.attacks.prompt_injection import PromptInjectionPlugin
from mantis.plugins.attacks.message_spoofing import MessageSpoofingPlugin
from mantis.plugins.attacks.route_confusion import RouteConfusionPlugin
from mantis.plugins.attacks.tool_mutation import ToolParameterMutationPlugin
from mantis.plugins.failures.reliability import ReliabilityFailurePlugin

plugin_registry.register("mock_attack", MockAttackPlugin)
plugin_registry.register("prompt_injection", PromptInjectionPlugin)
plugin_registry.register("message_spoofing", MessageSpoofingPlugin)
plugin_registry.register("route_confusion", RouteConfusionPlugin)
plugin_registry.register("tool_mutation", ToolParameterMutationPlugin)
plugin_registry.register("reliability_failure", ReliabilityFailurePlugin)

# Banking-specific data (which agents belong to which domain, scenario
# prompts, workflow->domain mapping) lives under mantis.banking -- this
# module only wires it into the shared registries. Keeps shared MANTIS
# infrastructure free of hardcoded banking branches (WP1 acceptance
# criterion) while still registering banking as the primary domain.
from mantis.banking.domains import DOMAIN_AGENTS
from mantis.banking.scenarios import SCENARIOS
from mantis.banking.workflows import WORKFLOW_DOMAINS

for _domain_name, _agents in DOMAIN_AGENTS.items():
    domain_registry.register(_domain_name, {"agents": _agents})

for _scenario_id, _prompt in SCENARIOS.items():
    scenario_registry.register(_scenario_id, _prompt)

for _workflow_id, _domain_name in WORKFLOW_DOMAINS.items():
    workflow_registry.register(_workflow_id, _domain_name)

# Lightweight metadata only -- no imports of mantis.observability.* here, so
# that importing mantis.core.registry never pulls in mlflow/opentelemetry
# (the CLI must boot without the full observability/ADK stack for commands
# like --validate, --inventory, --generate-schemas).
exporter_registry.register("jsonl", {"description": "Portable JSONL trace artifacts", "module": "mantis.observability.artifacts:TraceArtifactWriter"})
exporter_registry.register("mlflow", {"description": "MLflow experiment tracking export", "module": "mantis.observability.mlflow_exporter:MLflowExporter"})
exporter_registry.register("otel", {"description": "OpenTelemetry span export", "module": "mantis.observability.otel:setup_otel"})

evaluator_registry.register("trace_completeness", {"description": "Checks mandatory workflow/agent events are present", "module": "mantis.evaluation.evaluators:TraceEvaluator.evaluate_completeness"})
evaluator_registry.register("tool_use_correctness", {"description": "Checks expected/forbidden tool usage", "module": "mantis.evaluation.evaluators:TraceEvaluator.evaluate_tool_use"})
evaluator_registry.register("workflow_outcome", {"description": "Checks the terminal state against expected_terminal_state", "module": "mantis.evaluation.evaluators:TraceEvaluator.evaluate_workflow_outcome"})
