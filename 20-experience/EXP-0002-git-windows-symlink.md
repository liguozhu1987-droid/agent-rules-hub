---
id: EXP-0002
layer: experience
asset_type: experience
source: "[A1] Git for Windows 官方 Wiki《Symbolic Links》（架构阶段已联网核实，本仓库未独立复验）"
scope: { level: global }
version: 1
created_at: "2026-11-05T11:00:00Z"
updated_at: "2026-11-09T08:00:00Z"
review_after: "2027-05-09T00:00:00Z"
status: active
sensitivity: private
owner: gao
approved_by: user
---

# EXP-0002 · Windows 上软链不能作为分发主方案

## 场景

在 Windows 工作区（路径含空格）里，想把各 Agent 的规则文件用符号链接指向同一份主干文件，以省去复制与同步。

## 结论

放弃软链，改用「生成器投影 + 纯文件复制 + SHA-256 校验」。本仓库的 `hub publish` 只做复制，不创建任何 symlink 或 junction。

## 依据

已核实（架构阶段联网核实，来源：Git for Windows 官方 Wiki《Symbolic Links》，https://github.com/git-for-windows/git/wiki/Symbolic-Links ；链接沿用 docs/02-架构设计.md 附录，本仓库未独立复验）。要点：Windows 上创建 symlink 默认需要管理员权限或开启开发者模式；Git for Windows 默认 `core.symlinks=false`，克隆时会把符号链接降级为仅含目标路径的纯文本文件；目录 junction 虽无需 UAC，但只支持本地绝对目录路径，无法覆盖 `AGENTS.md`、`MEMORY.md` 这类单文件约定名。

## 失效条件

用户已开启 Windows 开发者模式、以管理员运行、且显式设置 `core.symlinks=true` 并确认目标 Agent 能正确解析链接时，本条结论可被重新评估；评估前仍需保留复制方案作为默认路径。若官方 Wiki 后续变更默认行为，以实测结果为准，不得沿用本条字面结论。
