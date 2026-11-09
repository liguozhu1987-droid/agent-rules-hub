"""投影编排：唯一 core_block → 遍历 config/agents.yaml → 跨视图哈希相等断言。

R04 核心保证：core_block 只在 resolver 里构造一次，所有常驻视图从同一字符串渲染；
任何分叉都会让 assert_hash_equality 抛错并使 publish 失败（fail-closed）。
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from hub.adapters import ADAPTER_REGISTRY
from hub.adapters.base import RenderContext
from hub.model import DerivedFile, HubConfig, LoadSet, Manifest, load_yaml


class ProjectionError(RuntimeError):
    """投影失败：缺失 adapter、只读头丢失或跨视图哈希分叉。"""


def load_agents_config(root: Path) -> dict[str, Any]:
    """读取 Agent 注册表。"""
    return load_yaml(root / "config" / "agents.yaml")


def render_all(
    root: Path,
    loadset: LoadSet,
    manifest: Manifest,
    hub_config: HubConfig,
    agents_config: dict[str, Any] | None = None,
    scope: str = "all",
) -> list[DerivedFile]:
    """按 Agent 注册表分派渲染，返回全部内存产物（不写盘）。"""
    agents_config = agents_config or load_agents_config(root)
    header = hub_config.generated_header(manifest.version)
    files: list[DerivedFile] = []

    for agent in agents_config.get("agents") or []:
        agent_id = str(agent.get("id", ""))
        adapter_cls = ADAPTER_REGISTRY.get(agent_id)
        if adapter_cls is None:
            raise ProjectionError(f"config/agents.yaml 中的 Agent {agent_id} 没有对应 adapter")
        ctx = RenderContext(
            root=root,
            manifest=manifest,
            loadset=loadset,
            hub_config=hub_config,
            agents_config=agents_config,
            agent=agent,
            header=header,
            core_block=loadset.core_block,
            core_sha256=loadset.core_sha256,
            scope=scope,
        )
        adapter = adapter_cls(ctx)
        produced = adapter.render()
        for derived in produced:
            if not adapter.verify(derived):
                raise ProjectionError(
                    f"{agent_id} 的派生产物 {derived.target_path} 缺少统一只读头或 core_sha256 不一致"
                )
        files.extend(produced)
    return files


def assert_hash_equality(files: list[DerivedFile], core_block: str) -> dict[str, Any]:
    """断言所有派生产物绑定同一 core_sha256，且内嵌视图包含完整 core_block 字节。

    Args:
        files: render_all 的全部产物。
        core_block: resolver 构造的唯一常驻正文。

    Returns:
        含 core_sha256、常驻视图数、产物数的摘要字典。

    Raises:
        ProjectionError: 任一视图哈希分叉、缺只读头或 core_block 字节缺失。
    """
    if not files:
        raise ProjectionError("没有生成任何派生产物，无法断言 core_sha256")

    all_hashes = {f.core_sha256 for f in files}
    if len(all_hashes) != 1:
        raise ProjectionError(f"派生产物 core_sha256 出现分叉: {sorted(all_hashes)}")

    resident = [f for f in files if f.always_on or f.embeds_core]
    resident_hashes = {f.core_sha256 for f in resident}
    if len(resident_hashes) != 1:
        raise ProjectionError(f"常驻视图 core_sha256 不相等: {sorted(resident_hashes)}")

    core_bytes = core_block.encode("utf-8")
    for derived in files:
        if derived.generated_header.encode("utf-8") not in derived.content:
            raise ProjectionError(f"{derived.target_path} 缺少统一只读头 DO NOT EDIT")
        if derived.embeds_core and core_bytes not in derived.content:
            raise ProjectionError(f"{derived.target_path} 未逐字节内嵌唯一 core_block")

    return {
        "core_sha256": next(iter(all_hashes)),
        "resident_views": len(resident),
        "all_views": len(files),
        "embedded_views": len([f for f in files if f.embeds_core]),
    }
