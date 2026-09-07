import os
from typing import Optional, Union, TYPE_CHECKING
from google.adk.models.lite_llm import LiteLlm
from .settings import settings

if TYPE_CHECKING:
    from .mock_llm import MockLlm

# Set once per experiment run via NativeBankingAdapter.reset(seed) so every
# agent built afterwards requests the same sampling seed from the model
# gateway. This narrows (does not guarantee) run-to-run output variance;
# LLM sampling remains inherently non-deterministic even with a fixed seed.
_current_seed: Optional[int] = None


def set_seed(seed: Optional[int]) -> None:
    global _current_seed
    _current_seed = seed


def build_model() -> Union[LiteLlm, "MockLlm"]:
    if os.getenv("MANTIS_MOCK_LLM", "").lower() in {"1", "true", "yes"}:
        from .mock_llm import MockLlm
        return MockLlm()

    kwargs = {}
    if _current_seed is not None:
        kwargs["seed"] = _current_seed
    return LiteLlm(
        model=f"openai/{settings.model_name}",
        api_base=settings.api_base,
        api_key=settings.api_key or "missing-api-key",
        **kwargs,
    )
