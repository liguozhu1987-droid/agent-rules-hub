"""发布：validate → resolve → project → hash → snapshot，全程 fail-closed。

顺序固定（K9），任何一步失败都不产生半份发布物；产物正文只含 manifest.version
与 manifest.published_at，绝不写入当前时间，连续 publish 逐字节相同。
publish 只读 manifest.yaml，不回写（prev_snapshot_sha256 首次为 ""）。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from hub import __version__
from hub.hashing import bytes_sha256, file_sha256
from hub.model import (
    Asset,
    DerivedFile,
    HubConfig,
    Manifest,
    atomic_write,
    dump_json,
    load_json,
    read_text,
)
from hub.projection import assert_hash_equality, load_agents_config, render_all
from hub.resolver import load_active_set
from hub.sensitive import (
    SensitiveBlocked,
    assert_no_findings,
    load_patterns,
    scan_assets,
    scan_derived,
)
from hub.validator import validate

GENERATED_MANIFEST = "90-adapters/.generated-manifest.json"


class PublishError(RuntimeError):
    """发布前置条件不满足，必须非零退出且不写盘。"""


@dataclass
class PublishResult:
    """一次 publish 的可读摘要（供 CLI 与 --json 输出）。"""

    version: str = ""
    scope: str = "all"
    core_sha256: str = ""
    derived_count: int = 0
    files_hashed: int = 0
    changed_ids: list[str] = field(default_factory=list)
    affected_agents: list[str] = field(default_factory=list)
    needs_review: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    written: list[str] = field(default_factory=list)
    unchanged: list[str] = field(default_factory=list)
    removed_stale: list[str] = field(default_factory=list)
    snapshot_path: str = ""
    generated_manifest_path: str = GENERATED_MANIFEST
    hash_summary: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "version": self.version,
            "scope": self.scope,
            "core_sha256": self.core_sha256,
            "derived_count": self.derived_count,
            "files_hashed": self.files_hashed,
            "changed_ids": self.changed_ids,
            "affected_agents": self.affected_agents,
            "needs_review": self.needs_review,
            "warnings": self.warnings,
            "written": self.written,
            "unchanged_count": len(self.unchanged),
            "removed_stale": self.removed_stale,
            "snapshot_path": self.snapshot_path,
            "generated_manifest_path": self.generated_manifest_path,
            "hash_summary": self.hash_summary,
        }


def _excluded(rel: str) -> bool:
    """快照中排除的文件（不入库 / 自指 / 缓存）。"""
    prefixes = (".git/", ".state/", "99-private/", "audit/releases/", "__pycache__/", ".venv/")
    if rel.startswith(prefixes) or "/__pycache__/" in rel:
        return True
    if rel in {"config/hub.local.yaml", "config/private-terms.txt", ".env"}:
        return True
    return rel.endswith((".pyc", ".tmp"))


def _snapshot_paths(root: Path) -> list[str]:
    """返回参与快照的全部文件相对路径（排序，确定性）。"""
    return sorted(
        p.relative_to(root).as_posix()
        for p in root.rglob("*")
        if p.is_file() and not _excluded(p.relative_to(root).as_posix())
    )


def _asset_records(assets: list[Asset]) -> list[dict[str, Any]]:
    """当前资产清单，供 sync 做按规则 ID 的 diff。"""
    records = [
        {
            "id": a.id,
            "path": a.path,
            "layer": a.layer,
            "asset_type": a.asset_type,
            "status": a.status,
            "version": a.version,
            "sensitivity": a.sensitivity,
            "expires": a.expires,
            "content_hash": a.content_hash,
        }
        for a in assets
    ]
    return sorted(records, key=lambda r: str(r["id"]))


def _changed_ids(current: list[dict[str, Any]], previous_snapshot: dict[str, Any]) -> list[str]:
    """按规则 ID 比较当前资产与上一快照，返回变化的 ID 列表。"""
    if not previous_snapshot:
        return []
    previous = {str(a.get("id", "")): a for a in previous_snapshot.get("assets") or []}
    now = {str(a["id"]): a for a in current}
    keys = sorted(set(previous) | set(now))
    keys_compare = ("path", "layer", "asset_type", "status", "version", "sensitivity", "expires", "content_hash")
    changed: list[str] = []
    for key in keys:
        if key not in previous or key not in now:
            changed.append(key)
            continue
        if any(previous[key].get(field_name) != now[key].get(field_name) for field_name in keys_compare):
            changed.append(key)
    return changed


def _derived_records(files: list[DerivedFile], header: str) -> list[dict[str, Any]]:
    """派生产物清单（含 sha256 与 core_sha256），写入 generated-manifest 与快照。"""
    records = []
    for derived in files:
        records.append({
            "path": derived.target_path,
            "sha256": bytes_sha256(derived.content),
            "size": len(derived.content),
            "agent_id": derived.agent_id,
            "source_id": derived.source_id,
            "source_version": derived.source_version,
            "core_sha256": derived.core_sha256,
            "embeds_core": derived.embeds_core,
            "always_on": derived.always_on,
            "has_readonly_header": header.encode("utf-8") in derived.content,
        })
    return sorted(records, key=lambda r: str(r["path"]))


def _cleanup_stale(root: Path, current_paths: set[str]) -> list[str]:
    """删除上次发布登记、本次不再生成的孤儿派生产物（仅限 90-adapters/）。"""
    gm_path = root / GENERATED_MANIFEST
    if not gm_path.is_file():
        return []
    previous = load_json(gm_path)
    removed: list[str] = []
    for row in previous.get("files") or []:
        rel = str(row.get("path", ""))
        if not rel.startswith("90-adapters/") or rel == GENERATED_MANIFEST:
            continue
        if rel in current_paths:
            continue
        path = root / rel
        if path.is_file():
            path.unlink()
            removed.append(rel)
    return removed


def _length_warnings(files: list[DerivedFile], cfg: HubConfig) -> list[str]:
    """长度预算检查：只告警，不改写正文（生成器绝不摘要或截断规则）。"""
    budget = cfg.length_budget
    warnings: list[str] = []
    agents_limit = int(budget.get("agents_md_bytes", 8192) or 8192)
    per_topic_limit = int(budget.get("per_topic_bytes", 2048) or 2048)
    for derived in files:
        size = len(derived.content)
        if derived.embeds_core or derived.target_path in {"AGENTS.md", "90-adapters/AGENTS.md"}:
            # 常驻全量视图按 AGENTS.md 预算（8 KiB），分主题文件才按 2 KiB 预算
            if size > agents_limit:
                warnings.append(f"{derived.target_path} 超出常驻视图预算 {agents_limit} 字节（实际 {size}）")
        elif derived.target_path.endswith((".mdc", ".instructions.md")) and size > per_topic_limit:
            warnings.append(f"{derived.target_path} 超出单文件预算 {per_topic_limit} 字节（实际 {size}）")
    return warnings


def publish(root: Path, scope: str = "all", now_iso: str | None = None) -> PublishResult:
    """执行一次确定性发布；失败时抛异常且不写任何文件。

    Args:
        root: 仓库根目录。
        scope: all / public；public 时排除 sensitivity != public 的资产。
        now_iso: 可选裁决基准时刻（ISO 8601 UTC）；为空取 manifest.published_at。

    Returns:
        PublishResult 摘要。

    Raises:
        PublishError: 校验 / 敏感 / 投影 / 哈希断言任一失败。
        SensitiveBlocked: 敏感模式命中（脱敏报错，不回显内容）。
    """
    manifest = Manifest.load(root)
    cfg = HubConfig.load(root)
    agents_cfg = load_agents_config(root)

    allowed = [str(x) for x in (cfg.publish_scope.get("allowed") or ["all", "public"])]
    if scope not in allowed:
        raise PublishError(f"发布范围 {scope!r} 不在 config/hub.yaml 允许集合 {allowed} 内")

    # 1. 校验（schema + 三条条件必填 + ID 唯一 + kebab-case + content_hash 查重）
    report = validate(root, manifest)
    if not report.ok:
        raise PublishError(
            f"主干校验未通过，共 {len(report.errors)} 项，已阻断发布：\n  - "
            + "\n  - ".join(str(i) for i in report.errors[:30])
        )

    # 2. 敏感扫描：只扫主干资产（绝不扫 config/sensitive-patterns.yaml 自身）
    patterns = load_patterns(root)
    assert_no_findings(scan_assets(root, report.assets, patterns))

    # 3. 裁决（时间源 = manifest.published_at，不依赖系统时钟）
    loadset = load_active_set(root, manifest, report.assets, now_iso, scope)

    # 4. 投影（唯一 core_block → 5 类 Agent）
    files = render_all(root, loadset, manifest, cfg, agents_cfg, scope)
    hash_summary = assert_hash_equality(files, loadset.core_block)

    # 5. 派生产物二次敏感扫描（写盘前）
    assert_no_findings(scan_derived(files, patterns))
    warnings = _length_warnings(files, cfg)

    # 6. 全部通过后一次性落盘（原子替换；内容相同则跳过）
    header = cfg.generated_header(manifest.version)
    written: list[str] = []
    unchanged: list[str] = []
    for derived in files:
        if atomic_write(root / derived.target_path, derived.content):
            written.append(derived.target_path)
        else:
            unchanged.append(derived.target_path)

    removed_stale = _cleanup_stale(root, {f.target_path for f in files})
    derived_records = _derived_records(files, header)

    # 7. 生成 90-adapters/.generated-manifest.json（先写，随后纳入全文件哈希）
    generated_manifest = {
        "schema_version": 1,
        "version": manifest.version,
        "published_at": manifest.published_at,
        "generated_header": header,
        "core_sha256": loadset.core_sha256,
        "generator_version": __version__,
        "scope": scope,
        "agent_count": len(agents_cfg.get("agents") or []),
        "files": derived_records,
    }
    atomic_write(root / GENERATED_MANIFEST, dump_json(generated_manifest).encode("utf-8"))

    # 8. 版本化快照（全文件 SHA-256 + changed_ids + affected_agents）；不回写 manifest
    snapshot_rel = str(
        cfg.version_strategy.get("snapshot_path", "audit/releases/{version}/snapshot.json")
    ).format(version=manifest.version)
    snapshot_path = root / snapshot_rel
    previous_snapshot = load_json(snapshot_path) if snapshot_path.is_file() else {}
    current_assets = _asset_records(report.assets)
    changed_ids = _changed_ids(current_assets, previous_snapshot)
    affected_agents = [str(a.get("id", "")) for a in (agents_cfg.get("agents") or [])]

    file_records = []
    for rel in _snapshot_paths(root):
        path = root / rel
        file_records.append({
            "path": rel,
            "sha256": file_sha256(path),
            "size": path.stat().st_size,
        })
    snapshot = {
        "schema_version": 1,
        "version": manifest.version,
        "published_at": manifest.published_at,
        "prev_snapshot_sha256": manifest.prev_snapshot_sha256,
        "core_sha256": loadset.core_sha256,
        "scope": scope,
        "generator_version": __version__,
        "changed_ids": changed_ids,
        "affected_agents": affected_agents,
        "needs_review": loadset.needs_review,
        "assets": current_assets,
        "derived": derived_records,
        "files": file_records,
        "file_count": len(file_records),
    }
    atomic_write(snapshot_path, dump_json(snapshot).encode("utf-8"))

    return PublishResult(
        version=manifest.version,
        scope=scope,
        core_sha256=loadset.core_sha256,
        derived_count=len(files),
        files_hashed=len(file_records),
        changed_ids=changed_ids,
        affected_agents=affected_agents,
        needs_review=loadset.needs_review,
        warnings=warnings,
        written=written,
        unchanged=unchanged,
        removed_stale=removed_stale,
        snapshot_path=snapshot_rel,
        hash_summary=hash_summary,
    )
