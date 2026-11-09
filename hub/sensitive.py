"""敏感模式扫描：fail-closed，报错绝不回显命中内容本身。

扫描范围只包括主干资产与内存中的派生产物；**不扫描 config/sensitive-patterns.yaml
自身**（模式定义里含 ghp_ / sk- / AKIA 等字面量，扫自身会自命中）。
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Pattern

from hub.model import Asset, DerivedFile, load_yaml, read_text


class SensitiveBlocked(Exception):
    """敏感模式命中，发布必须中止（不产生半份产物）。"""


@dataclass
class Finding:
    """一条脱敏后的命中记录：只保存路径 / 行号 / 模式编号，不保存匹配文本。"""

    path: str = ""
    line: int = 0
    pattern_id: str = ""
    description: str = ""

    def message(self) -> str:
        return (
            f"{self.path} 第 {self.line} 行命中敏感模式 {self.pattern_id}"
            f"（{self.description}）；命中内容已隐藏，不回显"
        )


def load_patterns(root: Path) -> list[tuple[str, str, Pattern[str]]]:
    """加载并编译全部敏感模式；编译失败即 fail-closed 抛错。"""
    cfg = load_yaml(root / "config" / "sensitive-patterns.yaml")
    compiled: list[tuple[str, str, Pattern[str]]] = []
    for item in cfg.get("patterns") or []:
        pid = str(item.get("id", "unnamed"))
        desc = str(item.get("description", "敏感内容"))
        try:
            compiled.append((pid, desc, re.compile(str(item.get("regex", "")))))
        except re.error as exc:
            raise SensitiveBlocked(f"敏感模式 {pid} 正则无法编译，按 fail-closed 阻断: {exc}") from exc

    terms_rel = str(cfg.get("private_terms_file", ""))
    if terms_rel:
        terms_path = root / terms_rel
        if terms_path.is_file():
            for line in read_text(terms_path).splitlines():
                term = line.strip()
                if term and not term.startswith("#"):
                    try:
                        compiled.append(("private_term", "用户自定义私有词表", re.compile(re.escape(term))))
                    except re.error as exc:
                        raise SensitiveBlocked(f"私有词表编译失败，按 fail-closed 阻断: {exc}") from exc
    return compiled


def scan_text(rel: str, text: str, patterns: list[tuple[str, str, Pattern[str]]]) -> list[Finding]:
    """逐行扫描文本，返回脱敏后的命中记录。"""
    findings: list[Finding] = []
    for lineno, line in enumerate(text.splitlines(), start=1):
        for pid, desc, rx in patterns:
            if rx.search(line):
                findings.append(Finding(path=rel, line=lineno, pattern_id=pid, description=desc))
    return findings


def scan_assets(
    root: Path,
    assets: list[Asset],
    patterns: list[tuple[str, str, Pattern[str]]],
) -> list[Finding]:
    """扫描主干资产全文（含 frontmatter 与正文）。"""
    findings: list[Finding] = []
    for asset in assets:
        path = root / asset.path
        if path.is_file():
            findings.extend(scan_text(asset.path, read_text(path), patterns))
    return findings


def scan_derived(files: list[DerivedFile], patterns: list[tuple[str, str, Pattern[str]]]) -> list[Finding]:
    """扫描内存中的派生产物；写盘前执行。"""
    findings: list[Finding] = []
    for derived in files:
        text = derived.content.decode("utf-8", errors="replace")
        findings.extend(scan_text(derived.target_path, text, patterns))
    return findings


def format_findings(findings: list[Finding]) -> list[str]:
    """生成可打印的脱敏错误行。"""
    return [f.message() for f in findings]


def assert_no_findings(findings: list[Finding]) -> None:
    """任一命中即阻断；错误信息不含匹配内容本身。"""
    if findings:
        lines = format_findings(findings)
        raise SensitiveBlocked(
            "敏感扫描 fail-closed 阻断发布，共 "
            f"{len(findings)} 处命中（内容已隐藏）：\n  - " + "\n  - ".join(lines[:20])
        )
