import pytest
from pydantic import ValidationError
from mantis.config.models import (
    ExperimentConfig,
    ExperimentMetadata,
    AttackConfig,
    ObservabilityConfig,
    ModificationsConfig,
    AgentConfig,
)


def test_valid_experiment_config():
    data = {
        "experiment": {
            "name": "test_exp",
            "seed": 123,
            "domain": "front_office",
            "workflow": "front_office_monitoring",
            "scenario": "front_office_monitoring",
        },
        "observability": {
            "mode": "full",
            "export": ["jsonl", "otel"],
        },
        "attack": {
            "plugin": "prompt_injection",
            "control_point": "input",
            "target": "transaction_monitoring_agent",
            "parameters": {"payload_file": "attacks/p1.txt"},
        },
        "modifications": {
            "agents": {
                "transaction_monitoring_agent": {"model": "gpt-4", "enabled": True}
            }
        },
    }
    cfg = ExperimentConfig(**data)
    assert cfg.experiment.name == "test_exp"
    assert cfg.experiment.seed == 123
    assert cfg.observability.mode == "full"
    assert cfg.attack.plugin == "prompt_injection"
    assert cfg.modifications.agents["transaction_monitoring_agent"].model == "gpt-4"


def test_invalid_experiment_missing_required_fields():
    with pytest.raises(ValidationError):
        # Missing domain, workflow, scenario
        ExperimentConfig(experiment={"name": "incomplete"})


def test_default_observability_config():
    meta = ExperimentMetadata(
        name="test",
        seed=42,
        domain="mid_office",
        workflow="mid_office_planning",
        scenario="mid_office_planning",
    )
    cfg = ExperimentConfig(experiment=meta)
    assert cfg.observability is None
    assert cfg.attack is None
    assert cfg.modifications is None


def test_json_schema_generation():
    schema = ExperimentConfig.model_json_schema()
    assert "properties" in schema
    assert "experiment" in schema["properties"]
    assert "observability" in schema["properties"]
    assert "attack" in schema["properties"]
