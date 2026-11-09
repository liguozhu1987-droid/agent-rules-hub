"""Claude Code 投影：CLAUDE.md 指针模式 + 项目级 claude/rules/*.md。"""

from __future__ import annotations

from hub.adapters.base import Adapter
from hub.model import DerivedFile


class ClaudeAdapter(Adapter):
    """指针模式避免与 AGENTS.md 形成两份互相矛盾的正文。"""

    agent_id = "claude"

    def render(self) -> list[DerivedFile]:
        ctx = self.ctx
        pointer = str(ctx.agent.get("pointer_target", "@AGENTS.md"))
        text = "\n".join([
            ctx.header,
            "",
            "# Claude Code 规则入口（指针模式）",
            "",
            pointer,
            "",
            "> 全部规则正文物理上只有一份，位于部署后的 AGENTS.md；本文件不复制正文，避免两份相互矛盾的副本。",
            f"> 仓库版本：{ctx.manifest.version}；发布时间（UTC）：{ctx.manifest.published_at}；core_sha256：{ctx.core_sha256}",
            "> 指针导入是否受目标版本支持未经官方核实，需本机实测（见 README.md 开放问题清单）；不生效时改用 inline 模式。",
        ]) + "\n"
        files = [
            self.make(
                str(ctx.agent.get("target_path", "90-adapters/CLAUDE.md")),
                text,
                embeds_core=False,
                always_on=bool(ctx.agent.get("always_on", True)),
            )
        ]

        template = str(ctx.agent.get("rules_target_path", "90-adapters/claude/rules/{id}.md"))
        for asset in ctx.loadset.project_overrides:
            rel = template.format(id=asset.id.lower(), name=asset.name or asset.id.lower())
            frontmatter = ctx.yaml_frontmatter({"paths": asset.scope.paths or ["**"]})
            body = ctx.clause_block(asset) + "\n\n" + ctx.expiry_note(asset)
            files.append(self.make(
                rel,
                frontmatter + ctx.header + "\n\n" + body + "\n",
                source_id=asset.id,
                source_version=asset.version,
                always_on=False,
            ))
        return files
