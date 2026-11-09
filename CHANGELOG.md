# 变更记录（示例）

> 本文件当前为**示例**，用于说明发布记录的格式。后续版本由 `hub publish` 从 `audit/decisions/` 的 ADR 汇总生成，禁止手写覆盖生成结果。

## [2026.11.09-1] - 2026-11-09

### 新增

- 初始规则集：2 条 L0 宪法（`CONST-0001`、`CONST-0002`）、7 条 L1 稳定偏好（`PREF-0001` ~ `PREF-0007`）。
- 经验知识区：3 条经验（`EXP-0001` ~ `EXP-0003`）与 `_index.md` 索引，零投影到常驻视图。
- 技能区：`weekly-report`、`ecosystem-research` 两个技能及各自的 `references/` 模板。
- 项目例外示例：`PROJ-example-project-0001`，带 `expires` 与 `sensitivity: private`。
- 治理文档：`README.md`、`GOVERNANCE.md`、`ONBOARDING.md`、`BOUNDARY.md`、`CONTRIBUTING.md`、`SKILLS-INDEX.md`。
- 机器契约：`manifest.yaml`、`schema/frontmatter.schema.json`、`config/*.yaml`、`templates/`。
- 决策记录：`ADR-0001-initial-rules.md`（背景 / 决策 / 评审四步结论 / 影响）。

### 决策依据

- `ADR-0001`：确定首批入库范围、裁决链 rank 0~4、纯文件复制分发方案。
- `EXP-0002`：Windows 软链默认行为（Git for Windows 官方 Wiki，架构阶段联网核实，本仓库未独立复验）→ 不使用符号链接。
- `EXP-0003`：GitHub 可见性为仓库级（GitHub Community Verified answer，架构阶段联网核实，本仓库未独立复验）→ 私有主干 + 独立公开子集。

### 仍需实测

- 见 `README.md` 开放问题清单：WorkBuddy 落盘路径、`@AGENTS.md` 指针、Cursor / Copilot 字段语义、长度预算、官方链接复验。
