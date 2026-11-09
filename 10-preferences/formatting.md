---
id: PREF-0002
layer: L1
asset_type: preference
source: "用户长期阅读偏好，见 ADR-0001 评审结论；与 docs/01-PRD.md 的结构化输出要求一致"
scope: { level: global, agents: ["*"] }
applies_when: { task_types: ["文档撰写", "方案输出", "对比分析"], triggers: ["表格", "对比", "结构"], file_globs: ["docs/**/*.md", "*.md"] }
version: 1
created_at: "2026-11-02T10:00:00Z"
updated_at: "2026-11-09T08:00:00Z"
review_after: "2027-05-09T00:00:00Z"
priority: 11
status: active
sensitivity: public
owner: gao
approved_by: user
---

# 稳定偏好：表格与 Mermaid 优先

- 涉及多项并列信息、流程或层级关系时，优先使用表格或 Mermaid 图，其次才是分点叙述；纯长段落仅用于解释因果。

> 适用范围：设计文档、调研对比、方案说明与状态报告。表格必须有表头，Mermaid 图必须能独立读懂，不依赖图外口头补充。
