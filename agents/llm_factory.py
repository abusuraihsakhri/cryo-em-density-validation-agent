"""
Deterministic mock adapter. External model providers are not implemented.
"""
from typing import Dict, Any, Optional
from .base import PHIGuard


class MockLLM:
    def __init__(self, system_name: str = "Cryo Em Density Validation Agent"):
        self.system_name = system_name

    def invoke(self, prompt: str) -> str:
        PHIGuard.assert_no_phi(prompt)
        return f"[{self.system_name} mock]: Received query '{prompt[:60]}...'. This is a deterministic placeholder, not model inference or scientific verification."


class LLMFactory:
    """Creates configured LLM client instances with zero-PHI protection."""

    @staticmethod
    def create(provider: str = "mock", system_name: str = "Cryo Em Density Validation Agent"):
        prov = str(provider).lower()
        if prov in ["mock", "deterministic", "test"]:
            return MockLLM(system_name)
        raise ValueError(f"Unsupported model provider: {provider!r}. Only mock is implemented.")
