"""校验器：schema + 必填 + 三条条件必填 + ID 唯一 + 文件名 + 正文查重。

资产发现按固定目录通配 + manifest.asset_index 并集，显式排除 drafts/、
20-experience/_index.md、各目录 README.md、99-private/、audit/、docs/。
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

from hub.frontmatter import FrontmatterError, read_asset
from hub.hashing import content_hash
from hub.model import Asset, Layer, Manifest, load_json

ALLOWED_NAMES = frozenset({
    "CORE.md", "SAFETY.md", "SKILL.md", "OVERRIDES.md",
    "TEMPLATE.md", "_index.md", "README.md",
})
KEBAB = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
EXP_NAME = re.compile(r"^EXP-\d{4}-[a-z0-9]+(-[a-z0-9]+)*\.md$")
ID_PATTERN = re.compile(
    r"^(?:CONST|PREF|EXP|ADR)-\d{4}$"
    r"|^PROJ-[a-z0-9]+(?:-[a-z0-9]+)*-\d{4}$"
    r"|^SKILL-[a-z0-9]+(?:-[a-z0-9]+)*$"
)
ASSET_DIR_GLOBS = (
    "00-constitution/*.md",
    "10-preferences/*.md",
    "20-experience/EXP-*.md",
    "30-skills/*/SKILL.md",
    "40-projects/*/OVERRIDES.md",
)


@dataclass
class ValidationIssue:
    """一条校验结果。"""

    path: str = ""
    level: str = "error"
    message: str = ""

    def __str__(self) -> str:
        prefix = "错误" if self.level == "error" else "提示"
        return f"[{prefix}] {self.path}: {self.message}"


@dataclass
class ValidationReport:
    """一次 validate 的完整结果。"""

    issues: list[ValidationIssue] = field(default_factory=list)
    assets: list[Asset] = field(default_factory=list)

    @property
    def errors(self) -> list[ValidationIssue]:
        return [i for i in self.issues if i.level == "error"]

    @property
    def warnings(self) -> list[ValidationIssue]:
        return [i for i in self.issues if i.level == "warning"]

    @property
    def ok(self) -> bool:
        return not self.errors

    def lines(self) -> list[str]:
        return [str(i) for i in self.issues]


def _error(rel: str, message: str) -> ValidationIssue:
    return ValidationIssue(path=rel, level="error", message=message)


def _warning(rel: str, message: str) -> ValidationIssue:
    return ValidationIssue(path=rel, level="warning", message=message)


def discover_asset_paths(root: Path, manifest: Manifest) -> list[Path]:
    """发现全部资产文件：目录通配 + manifest.asset_index 并集（按相对路径排序）。"""
    found: dict[str, Path] = {}
    for pattern in ASSET_DIR_GLOBS:
        for path in sorted(root.glob(pattern)):
            rel = path.relative_to(root).as_posix()
            if rel.startswith(("drafts/", "99-private/", "audit/", "docs/")):
                continue
            if path.name in {"README.md", "_index.md", "TEMPLATE.md"}:
                continue
            found[rel] = path
    for row in manifest.asset_index:
        rel = str(row.get("path", ""))
        if rel:
            path = root / rel
            if path.is_file():
                found.setdefault(rel, path)
    return [found[key] for key in sorted(found)]


def _check_filename(rel: str) -> list[str]:
    """文件名 kebab-case 校验；约定名与 EXP-<4位>- 前缀按契约豁免。"""
    path = Path(rel)
    name = path.name
    problems: list[str] = []
    if name in ALLOWED_NAMES:
        if name in {"SKILL.md", "OVERRIDES.md"} and not KEBAB.match(path.parent.name):
            problems.append(f"约定名 {name} 的父目录 {path.parent.name} 不是小写 kebab-case")
        return problems
    if EXP_NAME.match(name):
        tail = re.sub(r"^EXP-\d{4}-", "", name)[:-3]
        if not KEBAB.match(tail):
            problems.append(f"经验文件短标题 {tail} 不是小写 kebab-case")
        return problems
    if not KEBAB.match(path.stem):
        problems.append(f"文件名 {name} 不是小写 kebab-case（禁空格 / 中文 / 大写 / 下划线）")
    return problems


def _format_schema_error(err: Any) -> str:
    """把 jsonschema 的错误翻译成中文，并明确点出缺失字段名。"""
    message = str(err.message)
    if err.validator == "required":
        matched = re.search(r"'([^']+)' is a required property", message)
        name = matched.group(1) if matched else "未知字段"
        return f"缺少必填字段 '{name}'"
    if err.validator == "enum":
        return f"字段取值不在允许枚举内: {message}"
    if err.validator == "const":
        return f"字段取值不符合固定要求: {message}"
    if err.validator == "pattern":
        return f"字段格式不符合正则约束: {message}"
    location = "/".join(str(x) for x in err.absolute_path) or "(根)"
    return f"字段 {location} 校验失败: {message}"


def validate(root: Path, manifest: Manifest | None = None) -> ValidationReport:
    """执行全量校验；失败项集中返回，不提前退出。

    Args:
        root: 仓库根目录。
        manifest: 已加载的 Manifest；为空时从磁盘读取。

    Returns:
        ValidationReport，``ok`` 为 True 才允许 publish。
    """
    manifest = manifest or Manifest.load(root)
    schema = load_json(root / "schema" / "frontmatter.schema.json")
    schema_validator = Draft202012Validator(schema)
    issues: list[ValidationIssue] = []
    assets: list[Asset] = []
    seen_ids: dict[str, str] = {}
    seen_hashes: dict[str, str] = {}
    indexed = manifest.by_id()

    for path in discover_asset_paths(root, manifest):
        rel = path.relative_to(root).as_posix()
        try:
            meta, body = read_asset(path)
        except (FrontmatterError, UnicodeDecodeError, OSError) as exc:
            issues.append(_error(rel, f"无法解析 YAML frontmatter: {exc}"))
            continue

        asset = Asset.from_dict(meta, body, rel)
        asset.content_hash = content_hash(body)
        assets.append(asset)

        for err in sorted(
            schema_validator.iter_errors(meta),
            key=lambda e: (tuple(str(x) for x in e.absolute_path), str(e.message)),
        ):
            issues.append(_error(rel, _format_schema_error(err)))

        # 三条条件必填（与 schema 的 allOf 一一对应，额外给出中文明确原因）
        if meta.get("layer") == Layer.L0.value:
            if "override" not in meta:
                issues.append(_error(rel, "L0 条目缺少条件必填字段 'override'"))
            elif meta.get("override") != "forbidden":
                issues.append(_error(rel, "L0 条目的 override 必须为 'forbidden'"))
        if meta.get("layer") == Layer.L3.value and not meta.get("expires"):
            issues.append(_error(rel, "L3 条目缺少条件必填字段 'expires'"))
        if meta.get("asset_type") == "skill":
            for required in ("name", "description"):
                if not meta.get(required):
                    issues.append(_error(rel, f"技能条目缺少条件必填字段 '{required}'"))
            if meta.get("name") and str(meta["name"]) != path.parent.name:
                issues.append(_error(rel, f"技能 name '{meta['name']}' 与目录名 '{path.parent.name}' 不一致"))

        if not ID_PATTERN.match(asset.id):
            issues.append(_error(rel, f"ID 格式不合法: '{asset.id}'"))
        if asset.id in seen_ids:
            issues.append(_error(rel, f"ID 重复: {asset.id} 也出现在 {seen_ids[asset.id]}"))
        seen_ids[asset.id] = rel

        for problem in _check_filename(rel):
            issues.append(_error(rel, problem))

        if asset.content_hash in seen_hashes:
            issues.append(_error(
                rel,
                f"正文重复（content_hash 相同）：{seen_hashes[asset.content_hash]} 与 {rel}；"
                "请合并为一条并用 supersedes 关联，不复制正文",
            ))
        seen_hashes[asset.content_hash] = rel

        if asset.id not in indexed:
            issues.append(_warning(rel, f"资产 {asset.id} 尚未登记到 manifest.asset_index，请补登记"))

    # manifest.asset_index 单向一致性：索引中每条必须存在且与 frontmatter 逐字段一致
    for row in manifest.asset_index:
        rel = str(row.get("path", ""))
        path = root / rel
        if not path.is_file():
            issues.append(_error(rel, "manifest.asset_index 指向的文件不存在"))
            continue
        try:
            meta, _ = read_asset(path)
        except (FrontmatterError, UnicodeDecodeError, OSError) as exc:
            issues.append(_error(rel, f"manifest.asset_index 指向的文件无法解析: {exc}"))
            continue
        for key in ("id", "layer", "asset_type", "status", "version", "sensitivity"):
            if meta.get(key) != row.get(key):
                issues.append(_error(
                    rel,
                    f"manifest.asset_index 的 {key}={row.get(key)!r} 与 frontmatter 的 {meta.get(key)!r} 不一致",
                ))

    return ValidationReport(issues=issues, assets=sorted(assets, key=lambda a: a.path))
