"""WorkBuddy 投影：MEMORY.md 常驻视图 + skills/ 下的完整 SKILL.md 副本。"""

from __future__ import annotations

from hub.adapters.base import Adapter
from hub.model import DerivedFile, read_text


class WorkBuddyAdapter(Adapter):
    """技能以完整副本落位（渐进式披露），其余常驻视图只保留索引行。"""

    agent_id = "workbuddy"

    def render(self) -> list[DerivedFile]:
        ctx = self.ctx
        memory = ctx.core_text() + "\n".join([
            "",
            "## WorkBuddy 部署说明",
            "",
            f"- 本文件由 manifest.yaml v{ctx.manifest.version} 生成，请勿手工编辑；技能完整正文见同目录 skills/。",
            "- 用户级 MEMORY.md 与 skills/ 的真实落盘路径未经官方核实，需本机实测（见 README.md 开放问题清单）。",
            "",
        ])
        files = [
            self.make(
                str(ctx.agent.get("target_path", "90-adapters/workbuddy/MEMORY.md")),
                memory,
                embeds_core=True,
                always_on=bool(ctx.agent.get("always_on", True)),
            )
        ]

        skill_template = str(ctx.agent.get(
            "skills_target_path", "90-adapters/workbuddy/skills/{name}/SKILL.md"
        ))
        refs_template = str(ctx.agent.get(
            "skills_references_path", "90-adapters/workbuddy/skills/{name}/references/"
        ))
        for asset in ctx.loadset.skills:
            name = asset.name or asset.id.lower()
            source = ctx.root / asset.path
            original = read_text(source)
            parts = original.split("---\n", 2)
            if len(parts) == 3:
                skill_text = "---\n" + parts[1] + "---\n" + ctx.header + "\n\n" + parts[2]
            else:
                skill_text = ctx.header + "\n\n" + original
            files.append(self.make(
                skill_template.format(name=name),
                skill_text,
                source_id=asset.id,
                source_version=asset.version,
                always_on=False,
            ))

            refs_dir = ctx.root / "30-skills" / name / "references"
            if refs_dir.is_dir():
                for ref in sorted(refs_dir.glob("*.md")):
                    rel = refs_template.format(name=name).rstrip("/") + "/" + ref.name
                    files.append(self.make(
                        rel,
                        ctx.header + "\n\n" + read_text(ref),
                        source_id=asset.id,
                        source_version=asset.version,
                        always_on=False,
                    ))
        return files
