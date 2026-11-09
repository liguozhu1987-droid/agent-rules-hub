"""统一 CLI：validate / publish / status / sync --plan。

人读模式输出中文表格；``--json`` 输出统一结构
``{ok, data, warnings, errors}``；任一失败一律非零退出。
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

from hub import ROOT
from hub.frontmatter import FrontmatterError
from hub.model import dump_json
from hub.projection import ProjectionError
from hub.publish import PublishError, publish
from hub.sensitive import SensitiveBlocked
from hub.status import build_status, format_status
from hub.sync import build_plan, format_plan
from hub.validator import validate


def _emit(ok: bool, data: dict[str, Any], warnings: list[str], errors: list[str], as_json: bool) -> None:
    if as_json:
        print(dump_json({"ok": ok, "data": data, "warnings": warnings, "errors": errors}), end="")
    else:
        for line in warnings:
            print(line if line.startswith("[") else f"[提示] {line}")
        for line in errors:
            print(line if line.startswith("[") else f"[错误] {line}", file=sys.stderr)


def _cmd_validate(root: Path, as_json: bool) -> int:
    report = validate(root)
    data = {
        "ok": report.ok,
        "assets": len(report.assets),
        "errors": len(report.errors),
        "warnings": len(report.warnings),
        "asset_ids": [a.id for a in report.assets],
    }
    warnings = [str(i) for i in report.warnings]
    errors = [str(i) for i in report.errors]
    if as_json:
        _emit(report.ok, data, warnings, errors, True)
    else:
        print(f"ok | 资产 {len(report.assets)} 条 | 错误 {len(report.errors)} 项 | 提示 {len(report.warnings)} 项"
              if report.ok else f"FAILED | 错误 {len(report.errors)} 项")
        _emit(report.ok, data, warnings, errors, False)
    return 0 if report.ok else 1


def _cmd_publish(root: Path, scope: str, now_iso: str | None, as_json: bool) -> int:
    result = publish(root, scope=scope, now_iso=now_iso)
    data = result.to_dict()
    if as_json:
        _emit(True, data, result.warnings, [], True)
    else:
        print(
            f"publish ok | 版本 {result.version} | 范围 {result.scope} | "
            f"派生产物 {result.derived_count} 个 | 快照文件 {result.files_hashed} 个"
        )
        print(f"core_sha256: {result.core_sha256}")
        print(
            f"哈希断言: 常驻视图 {result.hash_summary.get('resident_views', 0)} 个全部相等，"
            f"内嵌 core_block 视图 {result.hash_summary.get('embedded_views', 0)} 个"
        )
        print(f"changed_ids: {result.changed_ids or '（无）'}")
        print(f"affected_agents: {', '.join(result.affected_agents)}")
        print(f"快照: {result.snapshot_path}")
        print(f"清单: {result.generated_manifest_path}")
        _emit(True, data, result.warnings, [], False)
    return 0


def _cmd_status(root: Path, as_json: bool) -> int:
    data = build_status(root)
    if as_json:
        _emit(True, data, [], [], True)
    else:
        print(format_status(data), end="")
    return 0


def _cmd_sync(root: Path, plan: bool, as_json: bool) -> int:
    data = build_plan(root)
    if as_json:
        _emit(True, data, [], [], True)
    elif plan:
        print(format_plan(data), end="")
    else:
        print("sync 当前只支持 --plan（只读差异报告，不落盘）：")
        print(format_plan(data), end="")
    return 0


def build_parser() -> argparse.ArgumentParser:
    """构造 argparse 解析器。"""
    parser = argparse.ArgumentParser(
        prog="hub",
        description="个人 Agent 规则中枢：validate / publish / status / sync --plan",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_validate = sub.add_parser("validate", help="校验主干资产（schema / 条件必填 / ID / 查重）")
    p_validate.add_argument("--json", action="store_true", help="输出机器可读 JSON")
    p_validate.add_argument("--root", default="", help="仓库根目录（默认自动解析）")

    p_publish = sub.add_parser("publish", help="编译 5 类只读投影并写版本快照")
    p_publish.add_argument("--scope", default="all", choices=["all", "public"], help="发布范围")
    p_publish.add_argument("--now", default="", help="裁决基准时刻（ISO 8601 UTC，默认 manifest.published_at）")
    p_publish.add_argument("--json", action="store_true", help="输出机器可读 JSON")
    p_publish.add_argument("--root", default="", help="仓库根目录（默认自动解析）")

    p_status = sub.add_parser("status", help="输出 5 类 Agent 的版本 / 一致性 / 漂移表")
    p_status.add_argument("--json", action="store_true", help="输出机器可读 JSON")
    p_status.add_argument("--root", default="", help="仓库根目录（默认自动解析）")

    p_sync = sub.add_parser("sync", help="增量同步计划")
    p_sync.add_argument("--plan", action="store_true", help="只读差异报告（不落盘）")
    p_sync.add_argument("--json", action="store_true", help="输出机器可读 JSON")
    p_sync.add_argument("--root", default="", help="仓库根目录（默认自动解析）")
    return parser


def main(argv: list[str] | None = None) -> int:
    """CLI 入口；返回进程退出码。"""
    args = build_parser().parse_args(argv)
    root = Path(args.root).resolve() if args.root else ROOT
    as_json = bool(getattr(args, "json", False))

    try:
        if not (root / "manifest.yaml").is_file():
            raise PublishError(f"目录不是有效仓库根（缺 manifest.yaml）: {root}")
        if args.command == "validate":
            return _cmd_validate(root, as_json)
        if args.command == "publish":
            return _cmd_publish(root, args.scope, args.now or None, as_json)
        if args.command == "status":
            return _cmd_status(root, as_json)
        if args.command == "sync":
            return _cmd_sync(root, bool(args.plan), as_json)
        raise PublishError(f"未知子命令: {args.command}")
    except (PublishError, ProjectionError, SensitiveBlocked, FrontmatterError, OSError, ValueError) as exc:
        if as_json:
            _emit(False, {}, [], [str(exc)], True)
        else:
            print(f"失败: {exc}", file=sys.stderr)
        return 1


__all__ = ["main", "build_parser"]
