---
id: PREF-0001
layer: L1
asset_type: preference
source: "用户长期沟通习惯，见 ADR-0001 评审结论"
scope: { level: global, agents: ["*"] }
applies_when: { task_types: ["对话", "文档撰写", "方案输出"], triggers: ["回答", "汇报", "总结"] }
version: 1
created_at: "2026-11-02T10:00:00Z"
updated_at: "2026-11-09T08:00:00Z"
review_after: "2027-05-09T00:00:00Z"
priority: 10
status: active
sensitivity: public
owner: gao
approved_by: user
---

# 稳定偏好：输出语言与用户一致

- 回复语言始终与用户当前提问语种一致；用户使用简体中文时全程使用简体中文，专业术语首次出现时补一句中文解释，不整段切换为英文。

> 适用范围：全部会话与全部交付文档。代码、命令、路径、规则 ID、YAML 键名等机器可读标识保持 ASCII 原文，不属于语种切换。
