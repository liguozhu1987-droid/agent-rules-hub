"""接入状态自检：5 类 Agent 的版本 / 一致性 / 漂移表。"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from hub.hashing import file_sha256
from hub.model import HubConfig, Manifest, load_json
from hub.projection import load_agents_config
from hub.publish import GENERATED_MANIFEST


def _primary_target(agent: dict[str, Any]) -> str:
    """每个 Agent 的主常驻目标文件（cursor 用 core.mdc）。"""
    return str(agent.get("core_target_path") or agent.get("target_path") or "")


def _snapshot_path(root: Path) -> Path:
    cfg = HubConfig.load(root)
    manifest = Manifest.load(root)
    return root / str(
        cfg.version_strategy.get("snapshot_path", "audit/releases/{version}/snapshot.json")
    ).format(version=manifest.version)


def build_status(root: Path) -> dict[str, Any]:
    """读取 generated-manifest 与快照，逐 Agent 计算一致性并做全量漂移检测。"""
    manifest = Manifest.load(root)
    agents_cfg = load_agents_config(root)
    gm_path = root / GENERATED_MANIFEST
    gm = load_json(gm_path) if gm_path.is_file() else {}
    snap_path = _snapshot_path(root)
    snapshot = load_json(snap_path) if snap_path.is_file() else {}

    records: list[dict[str, Any]] = list(gm.get("files") or [])
    by_path = {str(r.get("path", "")): r for r in records}
    rows: list[dict[str, Any]] = []

    for agent in agents_cfg.get("agents") or []:
        agent_id = str(agent.get("id", ""))
        mine = [r for r in records if str(r.get("agent_id", "")) == agent_id]
        primary = _primary_target(agent)
        record = by_path.get(primary, {})
        target = root / primary
        exists = target.is_file() if primary else False
        actual = file_sha256(target) if exists else ""
        consistent = bool(record) and exists and actual == str(record.get("sha256", ""))
        rows.append({
            "agent_id": agent_id,
            "target": primary,
            "version": str(gm.get("version", manifest.version)),
            "core_sha256": str(record.get("core_sha256", gm.get("core_sha256", ""))),
            "consistent": consistent,
            "drift": "否" if consistent else "是",
            "files": len(mine),
            "always_on": bool(agent.get("always_on", False)),
            "note": "" if consistent else ("目标文件缺失" if not exists else "SHA-256 与快照不符"),
        })

    drift_files: list[str] = []
    for record in records:
        rel = str(record.get("path", ""))
        path = root / rel
        if not path.is_file() or file_sha256(path) != str(record.get("sha256", "")):
            drift_files.append(rel)

    return {
        "version": str(gm.get("version", manifest.version)),
        "manifest_version": manifest.version,
        "snapshot_version": str(snapshot.get("version", "")),
        "core_sha256": str(gm.get("core_sha256", "")),
        "generated_manifest_exists": bool(gm),
        "snapshot_exists": bool(snapshot),
        "agents": rows,
        "drift_files": sorted(drift_files),
        "drift_count": len(drift_files),
        "derived_count": len(records),
    }


def format_status(data: dict[str, Any]) -> str:
    """把状态数据渲染成可读 Markdown 表格。"""
    lines = [
        "# hub status · 接入状态自检",
        "",
        f"仓库版本：{data['version']} | 快照版本：{data['snapshot_version'] or '（无）'} "
        f"| core_sha256：{data['core_sha256'] or '（无）'}",
        f"派生产物：{data['derived_count']} 个 | 漂移：{data['drift_count']} 项",
        "",
        "| Agent | 目标文件 | 版本 | 一致 | 漂移 | 文件数 | 备注 |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for row in data["agents"]:
        lines.append(
            f"| {row['agent_id']} | {row['target']} | {row['version']} | "
            f"{'是' if row['consistent'] else '否'} | {row['drift']} | {row['files']} | {row['note']} |"
        )
    lines.extend(["", "## 漂移明细"])
    if data["drift_files"]:
        for rel in data["drift_files"]:
            lines.append(f"- {rel}（下次 publish 会覆盖并告警）")
    else:
        lines.append("- 无漂移：全部派生产物与 generated-manifest 记录的 SHA-256 一致。")
    if not data["generated_manifest_exists"]:
        lines.append("- 提示：尚未执行 publish，请先运行 `python -m hub publish`。")
    return "\n".join(lines) + "\n"
