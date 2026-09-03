from pydantic import BaseModel, Field
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
    operation_type: Optional[str] = None
    risk_level: Optional[str] = None
    data_sensitivity: Optional[str] = None
    financial_side_effect: Optional[bool] = None
    result: Optional[str] = None
    latency_ms: Optional[float] = None

class SecurityEvent(BaseTraceEvent):
    stage: str
    target: str
    plugin: str
    expected_impact: Optional[str] = None
    observed_impact: Optional[str] = None
    details: Optional[Dict[str, Any]] = None
