"""
Compatibility helpers for RAGAS 0.4.3.

RAGAS 0.4.3 imports ChatVertexAI from the old
langchain_community.chat_models.vertexai path.

The Vertex AI integration now lives in
langchain_google_vertexai.

This shim aliases the new module to the legacy path
before RAGAS is imported.
"""

import sys
import types

from langchain_google_vertexai import ChatVertexAI


def setup_ragas_compatibility() -> None:
    """Register the legacy Vertex AI import path expected by RAGAS."""

    module_name = "langchain_community.chat_models.vertexai"

    if module_name not in sys.modules:
        compatibility_module = types.ModuleType(module_name)
        compatibility_module.ChatVertexAI = ChatVertexAI

        sys.modules[module_name] = compatibility_module