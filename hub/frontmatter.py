"""YAML frontmatter 读写与规范化。"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import yaml

from hub.model import normalize_text, read_text, to_jsonable

DELIMITER = "---"
FM_PATTERN = re.compile(r"\A---\n(.*?)\n---\n(.*)\Z", re.S)


class FrontmatterError(ValueError):
    """frontmatter 分隔块缺失或 YAML 解析失败。"""


def split_frontmatter(text: str) -> tuple[dict[str, Any], str]:
    """把 Markdown 文本拆成 (frontmatter 字典, 正文)。

    Raises:
        FrontmatterError: 缺少 ``---`` 分隔块或 YAML 不是映射。
    """
    normalized = normalize_text(text)
    match = FM_PATTERN.match(normalized)
    if match is None:
        raise FrontmatterError("缺少 YAML frontmatter（文件须以 --- 开始并有闭合 --- 行）")
    try:
        meta = yaml.safe_load(match.group(1))
    except yaml.YAMLError as exc:
        raise FrontmatterError(f"frontmatter YAML 解析失败: {exc}") from exc
    if meta is None:
        meta = {}
    if not isinstance(meta, dict):
        raise FrontmatterError("frontmatter 必须是 YAML 映射（键值对）")
    return to_jsonable(meta), match.group(2)


def parse_frontmatter(text: str) -> tuple[dict[str, Any], str]:
    """split_frontmatter 的语义别名。"""
    return split_frontmatter(text)


def dump_frontmatter(meta: dict[str, Any], body: str) -> str:
    """把 frontmatter 与正文拼回 Markdown 文本（LF、UTF-8 友好）。"""
    block = yaml.safe_dump(meta, allow_unicode=True, sort_keys=False, default_flow_style=False).rstrip("\n")
    return f"---\n{block}\n---\n{normalize_text(body).lstrip(chr(10))}"


def read_asset(path: Path) -> tuple[dict[str, Any], str]:
    """从磁盘读取一个资产的 frontmatter 与正文。"""
    return split_frontmatter(read_text(path))
