"""LLM 调用层共用类型（与具体厂商无关）。"""

from __future__ import annotations

from typing import Literal, TypedDict


class ChatMessage(TypedDict):
    role: Literal["system", "user", "assistant"]
    content: str


class LLMUsageMeta(TypedDict, total=False):
    model: str
    prompt_tokens: int
    completion_tokens: int


class LLMResult(TypedDict, total=False):
    text: str
    raw: dict
    usage: LLMUsageMeta
