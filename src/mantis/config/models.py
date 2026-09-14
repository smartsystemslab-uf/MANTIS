from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field

class ExperimentMetadata(BaseModel):
    name: str = Field(description="Name of the experiment")
    seed: int = Field(default=42, description="Random seed for reproducibility")
    domain: str = Field(description="Target banking domain (e.g., front_office, mid_office, back_office)")
    workflow: str = Field(description="Target workflow (e.g., fraud_review, front_office_monitoring)")
    scenario: str = Field(description="Specific scenario ID mapping to a concrete prompt")

class AgentConfig(BaseModel):
    model: str = Field(default="default", description="Model to use for this agent")
    enabled: bool = Field(default=True, description="Whether this agent is enabled")

class ModificationsConfig(BaseModel):
    agents: Dict[str, AgentConfig] = Field(default_factory=dict, description="Agent specific overrides")

class AttackConfig(BaseModel):
    plugin: str = Field(description="Attack plugin to load")
    control_point: str = Field(description="Insertion point (e.g., input, agent, tool)")
    target: str = Field(description="Target component ID")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Plugin specific parameters")

class ObservabilityConfig(BaseModel):
    mode: str = Field(default="full", description="Observability mode: off, selective, full")
    export: List[str] = Field(default_factory=lambda: ["jsonl"], description="Exporters to enable")
    jaeger_endpoint: Optional[str] = Field(default=None, description="OTLP gRPC endpoint for the Jaeger exporter (only used when 'jaeger' is in export); defaults to http://localhost:4317")

class EvaluationConfig(BaseModel):
    expected_tools: List[str] = Field(default_factory=list, description="Tools that must be called")
    forbidden_tools: List[str] = Field(default_factory=list, description="Tools that must not be called")
    expected_terminal_state: Optional[str] = Field(default=None, description="Expected outcome state")

class BenchmarkConfig(BaseModel):
    concurrency: int = Field(default=1, description="Number of concurrent workflow executions")
    repetitions: int = Field(default=1, description="Number of repetitions per configuration")
    mock_llm: bool = Field(default=False, description="Use a zero-latency mock model instead of a live LLM, to isolate instrumentation overhead from LLM sampling latency")
    scaling_repetitions: Optional[List[int]] = Field(default=None, description="If set, run the benchmark once per repetition count in this list (at the configured concurrency) to measure how latency/trace volume scale with transaction volume, instead of a single repetitions run")
    scaling_concurrency: Optional[List[int]] = Field(default=None, description="If set, run the benchmark once per concurrency level in this list (at the configured repetitions) to measure how latency/throughput scale with concurrent load, instead of a single concurrency run. Mutually exclusive with scaling_repetitions -- if both are set, scaling_concurrency takes precedence.")

class ExperimentConfig(BaseModel):
    """Root configuration model for MANTIS experiments."""
    experiment: ExperimentMetadata
    modifications: Optional[ModificationsConfig] = None
    attack: Optional[AttackConfig] = None
    observability: Optional[ObservabilityConfig] = None
    evaluation: Optional[EvaluationConfig] = None
    benchmark: Optional[BenchmarkConfig] = None
