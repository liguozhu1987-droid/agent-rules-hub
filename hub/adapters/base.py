"""Adapter 抽象接口、渲染上下文与统一只读头工具。"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml
from jinja2 import Environment

from hub.model import Asset, DerivedFile, HubConfig, LoadSet, Manifest, read_text


@dataclass
class RenderContext:
    """一次投影所需的全部只读输入。"""

    root: Path
    manifest: Manifest
    loadset: LoadSet
    hub_config: HubConfig
    agents_config: dict[str, Any]
    agent: dict[str, Any]
    header: str
    core_block: str
    core_sha256: str
    scope: str = "all"

    def core_text(self) -> str:
        """用唯一模板渲染常驻正文；结果与根目录 AGENTS.md 逐字节一致。"""
        template = read_text(self.root / "templates" / "adapters" / "core.md.tpl")
        env = Environment(
            trim_blocks=True,
            lstrip_blocks=True,
            keep_trailing_newline=False,
            autoescape=False,
        )
        rendered = env.from_string(template).render(
            version=self.manifest.version,
            core_block=self.core_block,
        )
        return rendered.lstrip("\n").rstrip("\n") + "\n"

    def clause_block(self, asset: Asset) -> str:
        """把一条资产的条款渲染成 ``- [ID] 条款`` 行（不改写原句）。"""
        return "\n".join(f"- [{asset.id}] {clause}" for clause in asset.clauses())

    def yaml_frontmatter(self, data: dict[str, Any]) -> str:
        """生成 YAML frontmatter 块（LF、中文不转义、不排序键）。"""
        block = yaml.safe_dump(
            data, allow_unicode=True, sort_keys=False, default_flow_style=False
        ).rstrip("\n")
        return f"---\n{block}\n---\n"

    def expiry_note(self, asset: Asset) -> str:
        """L3 例外由生成器附加的有效期提示，不改写规则正文。"""
        return f"本例外有效期至 {asset.expires}（UTC），过期自动失效。"


class Adapter(ABC):
    """所有 Agent 适配器的共同接口；新增 Agent 只需新增一个子类。"""

    agent_id: str = ""

    def __init__(self, ctx: RenderContext) -> None:
        self.ctx = ctx

    @abstractmethod
    def render(self) -> list[DerivedFile]:
        """产出该 Agent 的全部派生产物（内存中，不写盘）。"""

    def verify(self, derived: DerivedFile) -> bool:
        """校验产物带统一只读头且绑定同一 core_sha256。"""
        return derived.is_readonly() and derived.core_sha256 == self.ctx.core_sha256

    def make(
        self,
        target_path: str,
        text: str,
        *,
        embeds_core: bool = False,
        source_id: str = "",
        source_version: int = 0,
        always_on: bool = True,
    ) -> DerivedFile:
        """构造 DerivedFile，统一绑定 core_sha256 与只读头。"""
        return DerivedFile(
            agent_id=str(self.ctx.agent.get("id", self.agent_id)),
            target_path=target_path,
            content=text.encode("utf-8"),
            core_sha256=self.ctx.core_sha256,
            generated_header=self.ctx.header,
            embeds_core=embeds_core,
            source_id=source_id,
            source_version=source_version,
            always_on=always_on,
        )
