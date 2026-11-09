---
id: PREF-0007
layer: L1
asset_type: preference
source: "L0 CONST-0001 不编造事实条款在 L1 的落地细化，见 ADR-0001"
scope: { level: global, agents: ["*"] }
applies_when: { task_types: ["调研", "文档撰写", "对比分析"], triggers: ["来源", "核实", "官方"], file_globs: ["docs/**/*.md", "20-experience/*.md"] }
version: 1
created_at: "2026-11-03T09:00:00Z"
updated_at: "2026-11-09T08:00:00Z"
priority: 16
status: active
sensitivity: public
owner: gao
approved_by: user
---

# 稳定偏好：事实附来源与核实状态

- 引用外部结论时同时写出来源名称与核实状态（已核实 / 未经核实 / 经验判断）；无法给出出处时只写「未经核实」，不补造链接、版本号或机构名。

> 适用范围：调研报告、经验条目、架构说明与 README。仓库内已有的设计文档可作为「已核实」的上游引用，但需注明未做独立复验。
