---
id: PREF-0005
layer: L1
asset_type: preference
source: "用户确认的交付形态要求，见 ADR-0001 与 docs/01-PRD.md R16"
scope: { level: global, agents: ["*"] }
applies_when: { task_types: ["文档撰写", "开发", "方案输出"], triggers: ["交付", "生成", "报告"] }
version: 1
created_at: "2026-11-03T09:00:00Z"
updated_at: "2026-11-09T08:00:00Z"
priority: 14
status: active
sensitivity: public
owner: gao
approved_by: user
---

# 稳定偏好：交付同时给可读正文与可交付文件

- 每次交付都同时提供「对话内可直接阅读的正文摘要」与「落盘可复用的文件」；摘要中给出文件相对路径，不让用户自己猜产物在哪。

> 适用范围：文档、代码、配置、报告。若任务确实不产生文件，明确写出「本次无文件产物」及原因。
