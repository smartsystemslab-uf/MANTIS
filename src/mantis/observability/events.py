import hashlib
import json
from pydantic import BaseModel, Field, model_validator
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum

class EventType(str, Enum):
    # Experiment
    EXPERIMENT_START = "EXPERIMENT_START"
    EXPERIMENT_END = "EXPERIMENT_END"
    # Workflow
    WORKFLOW_START = "WORKFLOW_START"
    WORKFLOW_END = "WORKFLOW_END"
    ROUTE_DECISION = "ROUTE_DECISION"
    # Agent
    AGENT_START = "AGENT_START"
    AGENT_END = "AGENT_END"
    AGENT_ERROR = "AGENT_ERROR"
    # Interaction
    MESSAGE_SEND = "MESSAGE_SEND"
    MESSAGE_RECEIVE = "MESSAGE_RECEIVE"
    MESSAGE_MUTATE = "MESSAGE_MUTATE"
    # Tool
    TOOL_CALL = "TOOL_CALL"
    TOOL_RESULT = "TOOL_RESULT"
    TOOL_ERROR = "TOOL_ERROR"
    # Security
    ATTACK_INJECTED = "ATTACK_INJECTED"
    POLICY_EVENT = "POLICY_EVENT"
    ANOMALY = "ANOMALY"
    # Evaluation
    EVALUATION_RESULT = "EVALUATION_RESULT"

class BaseTraceEvent(BaseModel):
    event_type: EventType
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    run_id: str
    
class ExperimentEvent(BaseTraceEvent):
    config_hash: Optional[str] = None
    seed: Optional[int] = None
    status: Optional[str] = None

class WorkflowEvent(BaseTraceEvent):
    workflow_id: str
    business_domain: Optional[str] = None
    workflow_type: Optional[str] = None
    step: Optional[str] = None
    source: Optional[str] = None
    target: Optional[str] = None
    outcome: Optional[str] = None

class AgentEvent(BaseTraceEvent):
    agent_id: str
    role: Optional[str] = None
    model: Optional[str] = None
    latency_ms: Optional[float] = None
    input_ref: Optional[str] = None
    output_ref: Optional[str] = None

class ToolEvent(BaseTraceEvent):
    tool_name: str
    arguments: Optional[Dict[str, Any]] = None
    arguments_hash: Optional[str] = None
    business_domain: Optional[str] = None
    operation_type: Optional[str] = None
    risk_level: Optional[str] = None
    data_sensitivity: Optional[str] = None
    financial_side_effect: Optional[bool] = None
    result: Optional[str] = None
    latency_ms: Optional[float] = None

    @model_validator(mode="after")
    def _derive_arguments_hash(self):
        if self.arguments_hash is None and self.arguments is not None:
            canonical = json.dumps(self.arguments, sort_keys=True, default=str)
            self.arguments_hash = hashlib.sha256(canonical.encode()).hexdigest()
        return self

class InteractionEvent(BaseTraceEvent):
    """Agent <-> model message boundary (before_message / after_message)."""
    agent_id: str
    business_domain: Optional[str] = None
    content_hash: Optional[str] = None
    content_length: Optional[int] = None
    latency_ms: Optional[float] = None

class SecurityEvent(BaseTraceEvent):
    stage: str
    target: str
    plugin: str
    expected_impact: Optional[str] = None
    observed_impact: Optional[str] = None
    details: Optional[Dict[str, Any]] = None

class EvaluationEvent(BaseTraceEvent):
    evaluator: str
    metric: str
    score: float
    evidence_ref: Optional[str] = None
