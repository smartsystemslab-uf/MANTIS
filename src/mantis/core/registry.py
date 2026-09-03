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

# Register the base scenarios
scenario_registry.register(
    "front_office_monitoring",
    "Review transaction TXN-1001 for customer CUST-001. Run the front-office transaction monitoring, fraud, and compliance workflow and decide whether to approve or send to manual review."
)
scenario_registry.register(
    "front_office_chatbot",
    "Customer asks: How do I dispute a debit card transaction and what is the expected timeline?"
)
scenario_registry.register(
    "front_office_transaction_execution",
    "Customer service request: Transfer 125.50 USD from source account CHK-002 to destination account EXT-998 for customer CUST-002 with memo Utility backup payment."
)
scenario_registry.register(
    "mid_office_planning",
    "Use the mid-office planning workflow to analyze operations data for 2026-04-21, forecast workload, propose staffing, validate it, and provide support guidance."
)
scenario_registry.register(
    "mid_office_rep_assist",
    "Representative assist request for customer CUST-001. Provide customer data, a product suggestion for idle cash, loan guidance for a home equity inquiry, and policy/risk checks."
)
scenario_registry.register(
    "back_office_clean",
    "Core banking system event: Run end-of-day processing for batch EOD-2026-04-21-CLEAN and complete reconciliation and reporting."
)
scenario_registry.register(
    "back_office_mismatch",
    "Core banking system event: Run end-of-day processing for batch EOD-2026-04-21-MISMATCH and handle any reconciliation mismatch according to the workflow."
)
