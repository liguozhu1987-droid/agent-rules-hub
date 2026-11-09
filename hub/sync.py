"""增量同步计划：按规则 ID 输出 diff 报告并检测派生产物漂移。

本阶段只实现 ``sync --plan``（只读、不落盘），满足 R15 的「先 diff 后确认」。
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from hub.frontmatter import read_asset
from hub.hashing import file_sha256
from hub.model import HubConfig, Manifest, load_json, parse_iso_utc
from hub.projection import load_agents_config
from hub.publish import GENERATED_MANIFEST
from hub.status import _snapshot_path

_COMPARE_FIELDS = ("path", "layer", "asset_type", "status", "version", "sensitivity")


def build_plan(root: Path) -> dict[str, Any]:
    """比较 manifest.asset_index 与上一快照的资产清单，产出按 ID 粒度的差异。"""
    manifest = Manifest.load(root)
    agents_cfg = load_agents_config(root)
    snap_path = _snapshot_path(root)
    snapshot = load_json(snap_path) if snap_path.is_file() else {}
    gm_path = root / GENERATED_MANIFEST
    gm = load_json(gm_path) if gm_path.is_file() else {}

    current = {str(row.get("id", "")): row for row in manifest.asset_index}
    previous = {str(row.get("id", "")): row for row in (snapshot.get("assets") or [])}
    added = sorted(set(current) - set(previous))
    removed = sorted(set(previous) - set(current))
    modified = sorted(
        key for key in (set(current) & set(previous))
        if any(previous[key].get(field) != current[key].get(field) for field in _COMPARE_FIELDS)
    )

    try:
        baseline = parse_iso_utc(manifest.published_at)
    except ValueError:
        baseline = None
    expired: list[str] = []
    if baseline is not None:
        for key, row in sorted(current.items()):
            rel = str(row.get("path", ""))
            path = root / rel
            if not path.is_file():
                continue
            try:
                meta, _ = read_asset(path)
            except Exception:
                continue
            expires = str(meta.get("expires", ""))
            if expires:
                try:
                    if baseline >= parse_iso_utc(expires):
                        expired.append(key)
                except ValueError:
                    expired.append(key)

    drift: list[str] = []
    for record in gm.get("files") or []:
        rel = str(record.get("path", ""))
        path = root / rel
        if not path.is_file() or file_sha256(path) != str(record.get("sha256", "")):
            drift.append(rel)

    return {
        "version": manifest.version,
        "baseline_utc": manifest.published_at,
        "snapshot_exists": bool(snapshot),
        "snapshot_version": str(snapshot.get("version", "")),
        "from_version": str(snapshot.get("version", "")) or "（无）",
        "to_version": manifest.version,
        "added": added,
        "removed": removed,
        "modified": modified,
        "expired": expired,
        "unchanged": sorted(set(current) & set(previous) - set(modified)),
        "drift": sorted(drift),
        "affected_agents": [str(a.get("id", "")) for a in (agents_cfg.get("agents") or [])],
    }


def format_plan(data: dict[str, Any]) -> str:
    """渲染可读的 diff 报告。"""
    total = len(data["added"]) + len(data["removed"]) + len(data["modified"]) + len(data["expired"])
    lines = [
        "# hub sync --plan · 差异报告（只读，不落盘）",
        "",
        f"版本变化：{data['from_version']} → {data['to_version']} "
        f"| 裁决基准（UTC）：{data['baseline_utc']}",
        f"影响 Agent：{', '.join(data['affected_agents'])}",
        "",
        "## 按规则 ID 的差异",
        "",
    ]
    if not data["snapshot_exists"]:
        lines.append("- 尚无发布快照，请先执行 `python -m hub publish` 后再看差异。")
    elif total == 0:
        lines.append("- 无变更：manifest.asset_index 与上一快照的资产清单逐字段一致。")
    else:
        for label, keys in (
            ("新增", data["added"]),
            ("修订", data["modified"]),
            ("移除", data["removed"]),
            ("已过期", data["expired"]),
        ):
            if keys:
                lines.append(f"- {label}（{len(keys)}）：{', '.join(keys)}")
    lines.extend([
        "",
        "## 漂移检测",
        "",
    ])
    if data["drift"]:
        for rel in data["drift"]:
            lines.append(f"- {rel}：与 generated-manifest 记录的 SHA-256 不一致，下次 publish 会覆盖并告警")
    else:
        lines.append("- 无漂移：全部派生产物与记录一致。")
    lines.extend([
        "",
        "## 下一步",
        "",
        "- 确认上述差异后再把 `90-adapters/` 下对应文件复制到各 Agent 目标目录（见 ONBOARDING.md）。",
        "- 本阶段 `sync` 只支持 `--plan`，不自动写用户 Agent 配置目录。",
    ])
    return "\n".join(lines) + "\n"
