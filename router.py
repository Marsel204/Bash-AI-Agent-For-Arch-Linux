"""
Hybrid LLM Router — decides whether a query goes to the local Ollama
model or to the cloud API based on keyword matching + timeout fallback.
"""

from enum import Enum

class Route(str, Enum):
    LOCAL = "local"
    CLOUD = "cloud"


def classify_route(query: str) -> str:
    """Always use LOCAL route."""
    return Route.LOCAL


def get_model_for_route(route: str) -> str | list[str]:
    """Return the configured model for a given route."""
    import config
    return config.LOCAL_MODEL
