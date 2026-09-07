import os
from typing import Dict, Optional, Union, TYPE_CHECKING
from google.adk.models.lite_llm import LiteLlm
from .settings import settings

if TYPE_CHECKING:
    from .mock_llm import MockLlm

# Set once per experiment run via NativeBankingAdapter.reset(seed) so every
# agent built afterwards requests the same sampling seed from the model
# gateway. This narrows (does not guarantee) run-to-run output variance;
# LLM sampling remains inherently non-deterministic even with a fixed seed.
_current_seed: Optional[int] = None

# Set once per run from ExperimentConfig.modifications.agents[*].model, keyed
# by agent name. Populated by cli.main.run_experiment() before the banking
# agent tree is built.
_model_overrides: Dict[str, str] = {}


def set_seed(seed: Optional[int]) -> None:
    global _current_seed
    _current_seed = seed


def set_model_overrides(overrides: Optional[Dict[str, str]]) -> None:
    global _model_overrides
    _model_overrides = dict(overrides) if overrides else {}


def build_model(agent_name: Optional[str] = None) -> Union[LiteLlm, "MockLlm"]:
    if os.getenv("MANTIS_MOCK_LLM", "").lower() in {"1", "true", "yes"}:
        from .mock_llm import MockLlm
        return MockLlm()

    kwargs = {}
    if _current_seed is not None:
        kwargs["seed"] = _current_seed

    model_name = settings.model_name
    if agent_name:
        override = _model_overrides.get(agent_name)
        if override and override != "default":
            model_name = override

    return LiteLlm(
        model=f"openai/{model_name}",
        api_base=settings.api_base,
        api_key=settings.api_key or "missing-api-key",
        **kwargs,
    )
