"""
从 app/prompts/packs/<pack>/<name>.md 加载纯文本。
新增场景时复制 pack 或加文件即可，无需改业务代码（仅改 registry 或调用名）。
"""

from __future__ import annotations

from functools import lru_cache
from importlib import resources

from app.prompts import packs


def load_prompt(pack: str, name: str) -> str:
    """
    pack: 子目录名，如 nl_cypher
    name: 不含 .md，如 cypher_system
    """
    try:
        return resources.files(packs).joinpath(pack, f"{name}.md").read_text(encoding="utf-8")
    except OSError as e:
        raise FileNotFoundError(f"prompt 未找到: {pack}/{name}.md") from e


@lru_cache(maxsize=64)
def load_prompt_cached(pack: str, name: str) -> str:
    return load_prompt(pack, name)


def render(template: str, **kwargs: str) -> str:
    """简单 {{var}} 替换，避免引入 Jinja 依赖；复杂模板可后续换引擎。"""
    out = template
    for k, v in kwargs.items():
        out = out.replace("{{" + k + "}}", v)
    return out
