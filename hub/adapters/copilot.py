"""GitHub Copilot 投影：全仓常驻文件 + 按 applyTo 生成的分主题指令。"""

from __future__ import annotations

from typing import Any

from hub.adapters.base import Adapter
from hub.model import Asset, DerivedFile


class CopilotAdapter(Adapter):
    """copilot-instructions.md 内嵌核心块；*.instructions.md 的 applyTo 由 scope 生成。"""

    agent_id = "copilot"

    def _apply_to(self, asset: Asset) -> str:
        globs = list(dict.fromkeys(asset.scope.paths + asset.applies_when.to_globs()))
        if asset.layer == "L3":
            project = asset.scope.projects[0] if asset.scope.projects else "example-project"
            globs.append(f"40-projects/{project}/**")
            globs = list(dict.fromkeys(globs))
        return ", ".join(globs) if globs else "**"

    def render(self) -> list[DerivedFile]:
        ctx = self.ctx
        files: list[DerivedFile] = [
            self.make(
                str(ctx.agent.get("target_path", "90-adapters/copilot/copilot-instructions.md")),
                ctx.core_text(),
                embeds_core=True,
                always_on=bool(ctx.agent.get("always_on", True)),
            )
        ]
        template = str(ctx.agent.get(
            "instructions_target_path",
            "90-adapters/copilot/instructions/{id}.instructions.md",
        ))
        for asset in [*ctx.loadset.preferences, *ctx.loadset.project_overrides]:
            data: dict[str, Any] = {
                "name": asset.id,
                "description": asset.applies_when.to_description(asset.id),
                "applyTo": self._apply_to(asset),
            }
            body = ctx.clause_block(asset)
            if asset.layer == "L3":
                body += "\n\n" + ctx.expiry_note(asset)
            rel = template.format(id=asset.id.lower(), name=asset.name or asset.id.lower())
            files.append(self.make(
                rel,
                ctx.yaml_frontmatter(data) + ctx.header + "\n\n" + body + "\n",
                source_id=asset.id,
                source_version=asset.version,
                always_on=False,
            ))
        return files
