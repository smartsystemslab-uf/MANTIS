from typing import Optional
from google.adk.models.lite_llm import LiteLlm
from .settings import settings

# Set once per experiment run via NativeBankingAdapter.reset(seed) so every
# agent built afterwards requests the same sampling seed from the model
# gateway. This narrows (does not guarantee) run-to-run output variance;
# LLM sampling remains inherently non-deterministic even with a fixed seed.
_current_seed: Optional[int] = None


def set_seed(seed: Optional[int]) -> None:
    global _current_seed
    _current_seed = seed


def build_model() -> LiteLlm:
    kwargs = {}
    if _current_seed is not None:
        kwargs["seed"] = _current_seed
    return LiteLlm(
        model=f"openai/{settings.model_name}",
        api_base=settings.api_base,
        api_key=settings.api_key or "missing-api-key",
        **kwargs,
    )
