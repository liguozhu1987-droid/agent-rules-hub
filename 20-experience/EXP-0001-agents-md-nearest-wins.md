---
id: EXP-0001
layer: experience
asset_type: experience
source: "[S1] agents.md 官方规范（链接沿用 docs/02-架构设计.md 附录，架构阶段已联网核实，本仓库未独立复验）"
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

# EXP-0001 · AGENTS.md 就近优先

## 场景

同一仓库的不同层级目录各放了一份 `AGENTS.md`，且用户又在会话里直接下了一条指令；需要判断最终哪一条生效。

## 结论

离当前正在编辑的文件最近的 `AGENTS.md` 优先；用户当前会话的显式指令覆盖一切文件级规则。本仓库据此把裁决链 rank 0 固定为「会话显式指令」，并把唯一正文收敛到根目录 `AGENTS.md`。

## 依据

已核实（架构阶段联网核实，来源：agents.md 官方规范，https://agents.md/ ；链接沿用 docs/02-架构设计.md 附录，本仓库未独立复验）。该结论同时是 docs/01-PRD.md 与 docs/02-架构设计.md 6.2 裁决链的设计输入。

## 失效条件

目标 Agent 不读取或不遵循 `AGENTS.md` 约定时，本条不适用，必须改用该 Agent 专属投影（Cursor `.mdc`、Copilot `*.instructions.md`、WorkBuddy `MEMORY.md`）；若某工具把用户级规则置于会话指令之上，需以该工具实测结果为准并回写新经验，不得直接套用本条。
