---
id: PREF-0003
layer: L1
asset_type: preference
source: "用户确认的工作方式，见 ADR-0001 评审结论；与 L0 CONST-0001 的破坏性操作条款呼应"
scope: { level: global, agents: ["*"] }
applies_when: { task_types: ["开发", "改造", "发布"], triggers: ["实现", "修改", "上线"] }
version: 1
created_at: "2026-11-02T10:00:00Z"
updated_at: "2026-11-09T08:00:00Z"
review_after: "2027-05-09T00:00:00Z"
priority: 12
status: active
sensitivity: public
owner: gao
approved_by: user
---

# 稳定偏好：先计划后执行

- 接到多文件或跨模块任务时，先给出「改动清单 + 顺序 + 验收方式」的简短计划，再开始写文件；计划中列出不会触碰的既有文件。

> 适用范围：新建仓库、重构、批量生成文件。单文件的小型修正可直接执行，但仍需在交付说明中写清改了什么。
