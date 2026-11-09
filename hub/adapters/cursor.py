"""Cursor 投影：*.mdc 的 description / globs / alwaysApply 全部由 scope 生成。"""

from __future__ import annotations

from typing import Any

from hub.adapters.base import Adapter
from hub.model import Asset, DerivedFile


class CursorAdapter(Adapter):
    """core.mdc 内嵌唯一 core_block；分主题 .mdc 只含对应条款。"""

    agent_id = "cursor"

    def _frontmatter(self, asset: Asset | None, core: bool = False) -> str:
        ctx = self.ctx
        if core:
            data: dict[str, Any] = {
                "description": "全量常驻规则（L0 + 裁决链 + L1 + 技能索引），由 manifest.yaml 生成",
                "alwaysApply": True,
            }
            return ctx.yaml_frontmatter(data)

        assert asset is not None
        globs = list(dict.fromkeys(asset.applies_when.to_globs() + asset.scope.paths))
        if asset.layer == "L3":
            project = asset.scope.projects[0] if asset.scope.projects else "example-project"
            globs.append(f"40-projects/{project}/**")
            globs = list(dict.fromkeys(globs))
        data = {"description": asset.applies_when.to_description(asset.id)}
        if globs:
            data["globs"] = globs
        data["alwaysApply"] = bool(
            asset.layer in ("L0", "L1") and asset.scope.level == "global"
        )
        return ctx.yaml_frontmatter(data)

    def render(self) -> list[DerivedFile]:
        ctx = self.ctx
        files: list[DerivedFile] = []
        core_path = str(ctx.agent.get("core_target_path", "90-adapters/cursor/rules/core.mdc"))
        files.append(self.make(
            core_path,
            self._frontmatter(None, core=True) + ctx.header + "\n\n" + ctx.core_block + "\n",
            embeds_core=True,
            always_on=bool(ctx.agent.get("always_on", False)),
        ))

        template = str(ctx.agent.get("target_path", "90-adapters/cursor/rules/{name}.mdc"))
        for asset in [*ctx.loadset.preferences, *ctx.loadset.project_overrides]:
            rel = template.format(name=asset.id.lower(), id=asset.id.lower())
            body = ctx.clause_block(asset)
            if asset.layer == "L3":
                body += "\n\n" + ctx.expiry_note(asset)
            files.append(self.make(
                rel,
                self._frontmatter(asset) + ctx.header + "\n\n" + body + "\n",
                source_id=asset.id,
                source_version=asset.version,
                always_on=False,
            ))
        return files
