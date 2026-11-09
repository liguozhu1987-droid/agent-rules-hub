"""数据契约：资产、作用域、清单、加载集合与派生产物。

本模块只依赖标准库与 PyYAML，供其余模块共享，避免循环导入。
所有时间比较使用 ISO 8601 UTC；所有文本统一 LF + UTF-8 无 BOM + NFC。
"""

from __future__ import annotations

import json
import unicodedata
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any

import yaml


class Layer(str, Enum):
    """规则层级枚举，与 schema/frontmatter.schema.json 完全一致。"""

    L0 = "L0"
    L1 = "L1"
    L2 = "L2"
    L3 = "L3"
    EXPERIENCE = "experience"


class AssetType(str, Enum):
    """资产类别枚举。"""

    EXPERIENCE = "experience"
    PREFERENCE = "preference"
    SKILL = "skill"


class Status(str, Enum):
    """资产状态机；仅 active 参与加载。"""

    DRAFT = "draft"
    ACTIVE = "active"
    DEPRECATED = "deprecated"
    SUPERSEDED = "superseded"


class Sensitivity(str, Enum):
    """公开 / 私有隔离标记。"""

    PUBLIC = "public"
    PRIVATE = "private"


class OverridePolicy(str, Enum):
    """L0 覆盖策略。"""

    ALLOWED = "allowed"
    FORBIDDEN = "forbidden"


ISO_FMT = "%Y-%m-%dT%H:%M:%SZ"


def parse_iso_utc(value: str) -> datetime:
    """把 ISO 8601 UTC 字符串解析为带时区的 datetime。

    Args:
        value: 形如 ``2026-11-09T08:30:00Z`` 的字符串。

    Returns:
        UTC 时区的 datetime。

    Raises:
        ValueError: 值不是合法 ISO 8601 字符串。
    """
    if not isinstance(value, str) or not value.strip():
        raise ValueError("时间字段必须是非空的 ISO 8601 UTC 字符串")
    text = value.strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    parsed = datetime.fromisoformat(text)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def iso_utc(value: datetime) -> str:
    """把 datetime 格式化为 ISO 8601 UTC 字符串。"""
    return value.astimezone(timezone.utc).strftime(ISO_FMT)


def normalize_text(text: str) -> str:
    """统一换行、去 BOM、Unicode NFC。"""
    value = text.replace("\r\n", "\n").replace("\r", "\n").lstrip("\ufeff")
    return unicodedata.normalize("NFC", value)


def read_text(path: Path) -> str:
    """以 UTF-8 读取文件并规范化文本。"""
    return normalize_text(path.read_bytes().decode("utf-8"))


def atomic_write(path: Path, data: bytes) -> bool:
    """原子替换写盘；内容相同则跳过，避免无意义的时间戳变化。

    Returns:
        True 表示实际写盘，False 表示内容已一致。
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.is_file() and path.read_bytes() == data:
        return False
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_bytes(data)
    tmp.replace(path)
    return True


def load_yaml(path: Path) -> dict[str, Any]:
    """读取 YAML 映射；空文件返回空字典。"""
    data = yaml.safe_load(read_text(path))
    return data if isinstance(data, dict) else {}


def load_json(path: Path) -> dict[str, Any]:
    """读取 JSON 映射；非映射返回空字典。"""
    data = json.loads(read_text(path))
    return data if isinstance(data, dict) else {}


def dump_json(data: Any) -> str:
    """确定性 JSON 序列化：中文不转义、键排序、LF 结尾。"""
    return json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def to_jsonable(value: Any) -> Any:
    """把 YAML 解析出的日期等非 JSON 类型转成字符串，便于 jsonschema 校验。"""
    if isinstance(value, datetime):
        return iso_utc(value)
    if isinstance(value, dict):
        return {str(k): to_jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [to_jsonable(v) for v in value]
    return value


@dataclass
class Scope:
    """机器可判定的作用域。"""

    level: str = "global"
    projects: list[str] = field(default_factory=list)
    agents: list[str] = field(default_factory=list)
    paths: list[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> "Scope":
        data = data or {}
        return cls(
            level=str(data.get("level", "global")),
            projects=[str(x) for x in (data.get("projects") or [])],
            agents=[str(x) for x in (data.get("agents") or [])],
            paths=[str(x) for x in (data.get("paths") or [])],
        )

    def specificity_score(self) -> int:
        """数值越大越「就近具体」；用于 tie_break 的 specificity_desc。"""
        base = {"global": 0, "agent": 10, "project": 20, "path": 30}.get(self.level, 0)
        score = base
        if self.projects:
            score += 20
        if self.agents:
            score += 10
        if self.paths:
            score += 30
        return score

    def matches(self, ctx: dict[str, Any]) -> bool:
        """判断当前上下文是否命中该作用域。"""
        project = ctx.get("project", "")
        agent_id = ctx.get("agent_id", "")
        if self.projects and not any(p in ("*", project) for p in self.projects):
            return False
        if self.agents and not any(a in ("*", agent_id) for a in self.agents):
            return False
        return True


@dataclass
class AppliesWhen:
    """触发条件，用于技能 description 与 Cursor / Copilot frontmatter。"""

    task_types: list[str] = field(default_factory=list)
    triggers: list[str] = field(default_factory=list)
    file_globs: list[str] = field(default_factory=list)
    time_window: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> "AppliesWhen":
        data = data or {}
        return cls(
            task_types=[str(x) for x in (data.get("task_types") or [])],
            triggers=[str(x) for x in (data.get("triggers") or [])],
            file_globs=[str(x) for x in (data.get("file_globs") or [])],
            time_window=dict(data.get("time_window") or {}),
        )

    def to_description(self, asset_id: str = "") -> str:
        """生成人可读的「何时使用」短句。"""
        types = " / ".join(self.task_types) if self.task_types else "通用任务"
        words = " / ".join(self.triggers) if self.triggers else "常规请求"
        tail = f"（id: {asset_id}）" if asset_id else ""
        return f"当涉及 {types} 且命中 {words} 时使用{tail}"

    def to_globs(self) -> list[str]:
        """返回去重后的文件 glob 列表。"""
        return list(dict.fromkeys(self.file_globs))


@dataclass
class Asset:
    """一条可编辑主干资产（规则 / 经验 / 技能）。"""

    id: str = ""
    layer: str = ""
    asset_type: str = ""
    source: str = ""
    scope: Scope = field(default_factory=Scope)
    applies_when: AppliesWhen = field(default_factory=AppliesWhen)
    version: int = 1
    created_at: str = ""
    updated_at: str = ""
    status: str = ""
    sensitivity: str = ""
    owner: str = ""
    approved_by: str = ""
    path: str = ""
    body: str = ""
    meta: dict[str, Any] = field(default_factory=dict)
    override: str = ""
    expires: str = ""
    review_after: str = ""
    supersedes: str = ""
    superseded_by: str = ""
    name: str = ""
    description: str = ""
    priority: int = 100
    content_hash: str = ""

    @classmethod
    def from_dict(cls, meta: dict[str, Any], body: str, rel_path: str) -> "Asset":
        """从 frontmatter 字典、正文与相对路径构造 Asset。"""
        data = to_jsonable(meta)
        return cls(
            id=str(data.get("id", "")),
            layer=str(data.get("layer", "")),
            asset_type=str(data.get("asset_type", "")),
            source=str(data.get("source", "")),
            scope=Scope.from_dict(data.get("scope")),
            applies_when=AppliesWhen.from_dict(data.get("applies_when")),
            version=int(data.get("version", 1) or 1),
            created_at=str(data.get("created_at", "")),
            updated_at=str(data.get("updated_at", "")),
            status=str(data.get("status", "")),
            sensitivity=str(data.get("sensitivity", "")),
            owner=str(data.get("owner", "")),
            approved_by=str(data.get("approved_by", "")),
            path=rel_path,
            body=normalize_text(body),
            meta=data,
            override=str(data.get("override", "")),
            expires=str(data.get("expires", "")),
            review_after=str(data.get("review_after", "")),
            supersedes=str(data.get("supersedes", "")),
            superseded_by=str(data.get("superseded_by", "")),
            name=str(data.get("name", "")),
            description=str(data.get("description", "")),
            priority=int(data.get("priority", 100) or 100),
        )

    def is_loadable(self, now_utc: datetime) -> bool:
        """仅 active 且未过期的条目参与加载。"""
        if self.status != Status.ACTIVE.value:
            return False
        if self.expires:
            try:
                if now_utc >= parse_iso_utc(self.expires):
                    return False
            except ValueError:
                return False
        return True

    def specificity(self) -> int:
        return self.scope.specificity_score()

    def clauses(self) -> list[str]:
        """提取正文中以 ``- `` 开头的条款行（去掉列表前缀）。"""
        return [
            line[2:].strip()
            for line in self.body.split("\n")
            if line.startswith("- ") and line[2:].strip()
        ]

    def rank(self, priority_order: list[dict[str, Any]]) -> int:
        """按 config/priority.yaml 的 layer 映射返回 rank。"""
        for row in priority_order:
            if row.get("layer") == self.layer:
                return int(row.get("rank", 4))
        return 4


@dataclass
class Manifest:
    """manifest.yaml 的对象表示；publish 只读本对象，不回写文件。"""

    schema_version: int = 1
    repo: str = ""
    version: str = ""
    published_at: str = ""
    prev_snapshot_sha256: str = ""
    priority_order: list[dict[str, Any]] = field(default_factory=list)
    tie_break: list[str] = field(default_factory=list)
    id_registry: dict[str, Any] = field(default_factory=dict)
    asset_index: list[dict[str, Any]] = field(default_factory=list)
    raw: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def load(cls, root: Path) -> "Manifest":
        data = load_yaml(root / "manifest.yaml")
        return cls(
            schema_version=int(data.get("schema_version", 1) or 1),
            repo=str(data.get("repo", "")),
            version=str(data.get("version", "")),
            published_at=str(data.get("published_at", "")),
            prev_snapshot_sha256=str(data.get("prev_snapshot_sha256", "")),
            priority_order=list(data.get("priority_order") or []),
            tie_break=[str(x) for x in (data.get("tie_break") or [])],
            id_registry=dict(data.get("id_registry") or {}),
            asset_index=list(data.get("asset_index") or []),
            raw=data,
        )

    def by_id(self) -> dict[str, dict[str, Any]]:
        return {str(row.get("id", "")): row for row in self.asset_index}


@dataclass
class DerivedFile:
    """一份内存中的派生产物；写盘前全部完成校验。"""

    agent_id: str = ""
    target_path: str = ""
    content: bytes = b""
    core_sha256: str = ""
    generated_header: str = ""
    embeds_core: bool = False
    source_id: str = ""
    source_version: int = 0
    always_on: bool = True

    def is_readonly(self) -> bool:
        return self.content.startswith(self.generated_header.encode("utf-8")) or (
            self.generated_header.encode("utf-8") in self.content
        )


@dataclass
class LoadSet:
    """resolver 的产物：分层加载集合与唯一 core_block。"""

    constitution: list[Asset] = field(default_factory=list)
    preferences: list[Asset] = field(default_factory=list)
    skills: list[Asset] = field(default_factory=list)
    project_overrides: list[Asset] = field(default_factory=list)
    needs_review: list[str] = field(default_factory=list)
    core_block: str = ""
    core_sha256: str = ""
    priority_order: list[dict[str, Any]] = field(default_factory=list)
    assets: list[Asset] = field(default_factory=list)
    now_utc: str = ""


@dataclass
class HubConfig:
    """config/hub.yaml 的对象表示。"""

    raw: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def load(cls, root: Path) -> "HubConfig":
        return cls(raw=load_yaml(root / "config" / "hub.yaml"))

    def generated_header(self, version: str) -> str:
        template = str(self.raw.get("generated_header", ""))
        return template.format(version=version)

    def path(self, key: str, default: str = "") -> str:
        return str((self.raw.get("paths") or {}).get(key, default))

    @property
    def length_budget(self) -> dict[str, Any]:
        return dict(self.raw.get("length_budget") or {})

    @property
    def publish_scope(self) -> dict[str, Any]:
        return dict(self.raw.get("publish_scope") or {})

    @property
    def version_strategy(self) -> dict[str, Any]:
        return dict(self.raw.get("version_strategy") or {})
