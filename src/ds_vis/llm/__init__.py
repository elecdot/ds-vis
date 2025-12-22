"""
LLM integration stubs.

This module exposes minimal adapter interfaces so future work can plug in a
real LLM provider to translate natural language into DSL/Command text.
"""

from .adapter import LLMAdapter, LLMClient

__all__ = ["LLMAdapter", "LLMClient"]
