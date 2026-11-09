"""通用 AGENTS.md 投影：仓库根 + 90-adapters/ 两个字节级副本。"""

from __future__ import annotations

from hub.adapters.base import Adapter
from hub.model import DerivedFile


class AgentsMdAdapter(Adapter):
    """inline 模式：直接内嵌唯一 core_block。"""

    agent_id = "agents_md"

    def render(self) -> list[DerivedFile]:
        ctx = self.ctx
        text = ctx.core_text()
        targets = [
            str(ctx.agent.get("target_path", "90-adapters/AGENTS.md")),
            str(ctx.agent.get("root_target_path", "AGENTS.md")),
        ]
        return [
            self.make(
                target,
                text,
                embeds_core=True,
                always_on=bool(ctx.agent.get("always_on", True)),
            )
            for target in dict.fromkeys(targets)
        ]
