---
id: PREF-0006
layer: L1
asset_type: preference
source: "用户确认的评审要求，见 ADR-0001 评审四步结论"
scope: { level: global, agents: ["*"] }
applies_when: { task_types: ["方案输出", "开发", "测试"], triggers: ["需求", "验收", "测试"] }
version: 1
created_at: "2026-11-03T09:00:00Z"
updated_at: "2026-11-09T08:00:00Z"
priority: 15
status: active
sensitivity: public
owner: gao
approved_by: user
---

# 稳定偏好：每条需求带验收标准

- 写需求或任务分解时，每条都附一条可机器或人工判定的验收标准，写清「执行什么命令 / 观察什么输出 / 什么结果算通过」。

> 适用范围：PRD、任务清单、测试用例与实施报告。禁止使用「功能正常」「体验良好」这类无法判定的表述。
