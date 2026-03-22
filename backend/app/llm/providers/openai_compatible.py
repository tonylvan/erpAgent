"""OpenAI 兼容 HTTP API（/v1/chat/completions），适用于多数云与本地推理网关。"""

from __future__ import annotations

import logging
import os
from typing import Any

import httpx

from app.llm.types import ChatMessage, LLMResult

logger = logging.getLogger(__name__)


def chat_completions_url(base_url: str) -> str:
    """
    OpenAI 兼容端点为 .../v1/chat/completions。
    若 LLM_API_BASE 已以 /v1 结尾（如阿里云等），则不再重复拼接 /v1。
    """
    b = base_url.rstrip("/")
    if b.endswith("/v1"):
        return f"{b}/chat/completions"
    return f"{b}/v1/chat/completions"


class OpenAICompatibleProvider:
    name = "openai_compatible"

    def __init__(
        self,
        *,
        base_url: str,
        api_key: str,
        model: str,
        timeout_s: float = 120.0,
    ) -> None:
        self._base = base_url.rstrip("/")
        self._api_key = api_key
        self._model = model
        self._timeout = timeout_s

    def complete(
        self,
        messages: list[ChatMessage],
        *,
        temperature: float = 0.2,
        max_tokens: int | None = None,
    ) -> LLMResult:
        url = chat_completions_url(self._base)
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }
        body: dict[str, Any] = {
            "model": self._model,
            "messages": messages,
            "temperature": temperature,
        }
        if max_tokens is not None:
            body["max_tokens"] = max_tokens

        with httpx.Client(timeout=self._timeout) as client:
            r = client.post(url, headers=headers, json=body)
            r.raise_for_status()
            data = r.json()

        choice = (data.get("choices") or [{}])[0]
        msg = choice.get("message") or {}
        text = (msg.get("content") or "").strip()
        usage = data.get("usage") or {}
        return {
            "text": text,
            "raw": data,
            "usage": {
                "model": self._model,
                "prompt_tokens": int(usage.get("prompt_tokens", 0)),
                "completion_tokens": int(usage.get("completion_tokens", 0)),
            },
        }


def from_env() -> OpenAICompatibleProvider | None:
    """从环境变量构造；缺关键项时返回 None（调用方未配置 LLM）。"""
    base = os.getenv("LLM_API_BASE", "").strip().rstrip("/")
    key = os.getenv("LLM_API_KEY", "").strip()
    model = os.getenv("LLM_MODEL", "").strip()
    if not base or not model:
        return None
    timeout = float(os.getenv("LLM_TIMEOUT_SECONDS", "120") or "120")
    return OpenAICompatibleProvider(
        base_url=base,
        api_key=key or "",
        model=model,
        timeout_s=timeout,
    )
