from functools import lru_cache
from app.core.config import settings
from app.core.logging import logger
from app.services.ai.base import AIProvider
from app.services.ai.gemini_provider import GeminiProvider
from app.services.ai.mock import MockAIProvider
from app.services.ai.openai_provider import OpenAIProvider


@lru_cache()
def get_ai_provider() -> AIProvider:
    """Factory returning configured AI Provider singleton."""
    provider_name = (settings.AI_PROVIDER or "mock").lower()
    logger.info(f"Initializing AI Provider: {provider_name}")

    if provider_name == "mock":
        return MockAIProvider()
    elif provider_name == "openai":
        return OpenAIProvider()
    elif provider_name == "gemini":
        return GeminiProvider()
    else:
        logger.warning(f"Unknown AI_PROVIDER '{provider_name}', falling back to MockAIProvider")
        return MockAIProvider()
