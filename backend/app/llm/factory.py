"""根据环境变量选择 LLM 实现；新增厂商时在此注册，不改动业务编排。"""

from __future__ import annotations

import logging
import os

from app.llm.protocols import LLMProvider
from app.llm.providers.openai_compatible import OpenAICompatibleProvider, from_env as openai_from_env

logger = logging.getLogger(__name__)


def get_llm_provider() -> LLMProvider | None:
    """
    LLM_PROVIDER:
      - openai_compatible（默认）：LLM_API_BASE + LLM_API_KEY + LLM_MODEL
    未来可在此增加: azure_openai, anthropic, ollama, local_http 等。
    """
    kind = (os.getenv("LLM_PROVIDER") or "openai_compatible").strip().lower()
    if kind in ("openai_compatible", "openai", "compatible"):
        p = openai_from_env()
        if p is None:
            logger.warning("LLM 未配置完整：需要 LLM_API_BASE 与 LLM_MODEL（可选 LLM_API_KEY）")
        return p
    return None
