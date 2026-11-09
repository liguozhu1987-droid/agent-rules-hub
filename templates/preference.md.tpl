---
id: {{ id }}
layer: {{ layer }}
asset_type: preference
source: "{{ source }}"
scope: { level: global, agents: ["*"] }
applies_when: { task_types: ["文档撰写"], triggers: ["说明"] }
version: 1
created_at: "{{ created_at }}"
updated_at: "{{ updated_at }}"
review_after: "{{ review_after }}"
priority: 20
status: draft
sensitivity: public
owner: {{ owner }}
approved_by: "{{ approved_by }}"
---

# {{ title }}

- {{ clause }}

> 适用范围：写明本条覆盖的任务类型与不覆盖的场景。规则正文保持一条祈使句，说明写在本引用块里，不进入常驻视图。
