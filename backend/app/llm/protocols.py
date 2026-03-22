"""LLM 抽象：未来换模型 / 换网关只需新增 Provider 并在工厂注册。"""

from __future__ import annotations

from typing import Protocol

from app.llm.types import ChatMessage, LLMResult


class LLMProvider(Protocol):
    """统一对话补全接口。实现类可对接 OpenAI 兼容网关、Azure、本地 vLLM 等。"""

    name: str

    def complete(
        self,
        messages: list[ChatMessage],
        *,
        temperature: float = 0.2,
        max_tokens: int | None = None,
    ) -> LLMResult:
        """返回模型文本及可选元数据。"""
        ...
