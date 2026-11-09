"""加载集合与裁决：仅 active、expires 未过、按 config/priority.yaml 分组。

时间源默认取 manifest.published_at（确定性、不依赖系统时钟），保证 publish 幂等。
经验区物理上被排除出 LoadSet，因此零投影到任何常驻视图。
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

from hub.hashing import core_sha256
from hub.model import (
    Asset,
    Layer,
    LoadSet,
    Manifest,
    Status,
    iso_utc,
    load_yaml,
    parse_iso_utc,
)


def load_priority(root: Path) -> dict[str, Any]:
    """读取裁决链唯一真源 config/priority.yaml。"""
    return load_yaml(root / "config" / "priority.yaml")


def _timestamp(value: str) -> float:
    try:
        return parse_iso_utc(value).timestamp()
    except (ValueError, TypeError):
        return 0.0


def resolve_conflict(left: Asset, right: Asset) -> str:
    """裁决两条同 rank 资产，返回 left / right / needs_review。

    - 显式 supersedes 关系：新者胜；
    - 显式 conflicts_with 且 tie-break 完全打平：无法裁决 → needs_review；
    - 否则按 specificity > updated_at > priority > id 排序取胜者。
    """
    if left.supersedes == right.id:
        return "left"
    if right.supersedes == left.id:
        return "right"
    declared = (
        left.meta.get("conflicts_with") == right.id
        or right.meta.get("conflicts_with") == left.id
    )
    tied = (
        left.specificity() == right.specificity()
        and left.updated_at == right.updated_at
        and left.priority == right.priority
    )
    if declared and tied:
        return "needs_review"
    key_left = (-left.specificity(), -_timestamp(left.updated_at), left.priority, left.id)
    key_right = (-right.specificity(), -_timestamp(right.updated_at), right.priority, right.id)
    return "left" if key_left <= key_right else "right"


def load_active_set(
    root: Path,
    manifest: Manifest,
    assets: list[Asset],
    now_utc: datetime | str | None = None,
    scope: str = "all",
) -> LoadSet:
    """构造 LoadSet 与唯一 core_block。

    Args:
        root: 仓库根目录。
        manifest: 当前清单。
        assets: validator 发现的全部资产。
        now_utc: 裁决基准时刻；为空时取 manifest.published_at。
        scope: all / public；public 时排除 sensitivity != public 的资产。

    Returns:
        LoadSet（含 core_block 与 core_sha256）。
    """
    priority = load_priority(root)
    order = priority.get("priority_order") or []
    if isinstance(now_utc, str):
        now = parse_iso_utc(now_utc)
    elif now_utc is not None:
        now = now_utc
    else:
        now = parse_iso_utc(manifest.published_at)

    candidates: list[Asset] = []
    for asset in assets:
        if asset.layer == Layer.EXPERIENCE.value:
            continue
        if scope == "public" and asset.sensitivity != "public":
            continue
        if not asset.is_loadable(now):
            continue
        candidates.append(asset)

    superseded = {a.supersedes for a in candidates if a.supersedes}
    candidates = [a for a in candidates if a.id not in superseded]

    groups: dict[int, list[Asset]] = {rank: [] for rank in range(5)}
    for asset in candidates:
        groups[asset.rank(order)].append(asset)

    needs_review: list[str] = []
    for rank, group in groups.items():
        group.sort(key=lambda a: (-a.specificity(), -_timestamp(a.updated_at), a.priority, a.id))
        for i, left in enumerate(group):
            for right in group[i + 1:]:
                if resolve_conflict(left, right) == "needs_review":
                    needs_review.append(
                        f"rank {rank} 内 {left.id} 与 {right.id} 无法裁决，需人工确认"
                    )

    constitution = sorted(groups.get(1, []), key=lambda a: a.id)
    project_overrides = sorted(groups.get(2, []), key=lambda a: a.id)
    preferences = sorted(groups.get(3, []), key=lambda a: a.id)
    skills = sorted(groups.get(4, []), key=lambda a: (a.name, a.id))

    loadset = LoadSet(
        constitution=constitution,
        preferences=preferences,
        skills=skills,
        project_overrides=project_overrides,
        needs_review=sorted(set(needs_review)),
        priority_order=order,
        assets=candidates,
        now_utc=iso_utc(now),
    )
    loadset.core_block = build_core_block(loadset, manifest, priority)
    loadset.core_sha256 = core_sha256(loadset.core_block)
    return loadset


def build_core_block(loadset: LoadSet, manifest: Manifest, priority: dict[str, Any]) -> str:
    """只在内存中构造一次的唯一常驻正文（不含当前时间）。

    顺序固定：版本头 → 裁决链 → tie_break 说明 → L0 → L1 → L2 索引 → 经验区说明。
    L3 不进 core_block，只在项目级 .mdc / instructions / claude rules 里就近投影。
    """
    version_head = "\n".join([
        "# 个人 Agent 规则中枢 · 常驻视图",
        "",
        "## 版本头",
        "",
        f"- 仓库版本：{manifest.version}",
        f"- 发布时间（UTC）：{manifest.published_at}",
        "- 事实源：manifest.yaml（本文件由生成器产出，禁止手工编辑）",
    ])

    chain_lines = [
        "## 裁决链（rank 0 → 4）",
        "",
        "| rank | 来源 | 生效条件 |",
        "| --- | --- | --- |",
    ]
    for row in sorted(priority.get("priority_order") or [], key=lambda r: int(r.get("rank", 0))):
        chain_lines.append(
            f"| {int(row.get('rank', 0))} | {row.get('label', '')} | {row.get('note', '')} |"
        )
    tie_text = " → ".join(manifest.tie_break)
    chain_lines.extend([
        "",
        f"同 rank 内冲突按 {tie_text} 裁决；"
        "无法裁决时标 needs_review 并向用户提问，不自行取舍。",
    ])
    chain = "\n".join(chain_lines)

    l0_lines = ["## L0 硬约束（override: forbidden）", ""]
    for asset in loadset.constitution:
        for clause in asset.clauses():
            l0_lines.append(f"- [{asset.id}] {clause}")

    l1_lines = ["## L1 稳定偏好", ""]
    for asset in loadset.preferences:
        for clause in asset.clauses():
            l1_lines.append(f"- [{asset.id}] {clause}")

    l2_lines = ["## L2 技能索引（渐进式披露，仅 name + description）", ""]
    for asset in sorted(loadset.skills, key=lambda a: a.name):
        l2_lines.append(f"- {asset.name} — {asset.description}")

    footer = (
        "> 经验区（20-experience/）不参与约束裁决，零投影到任何常驻视图。"
        "L3 项目临时例外只在项目级就近视图出现，并标注 expires。"
    )

    sections = [
        version_head,
        chain,
        "\n".join(l0_lines),
        "\n".join(l1_lines),
        "\n".join(l2_lines),
        footer,
    ]
    return "\n\n".join(sections)
