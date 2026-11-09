---
id: {{ id }}
layer: experience
asset_type: experience
source: "{{ source }}"
scope: { level: global }
version: 1
created_at: "{{ created_at }}"
updated_at: "{{ updated_at }}"
review_after: "{{ review_after }}"
status: draft
sensitivity: private
owner: {{ owner }}
approved_by: "{{ approved_by }}"
---

# {{ title }}

## 场景

描述在什么任务、什么环境、什么前提下遇到了这个判断。写具体触发条件，不写空泛描述。

## 结论

一句话给出可执行结论：以后遇到同类场景应该怎么做、不应该怎么做。

## 依据

写清证据：官方文档名称与链接、可复现的命令与输出，或已有 ADR 编号。每条标注核实状态（已核实 / 未经核实 / 经验判断）。查不到就写「未经核实」，严禁补造来源链接、版本号或机构名。

## 失效条件

写清结论在什么前提变化后不再成立（平台版本、权限、配置、工具行为变化），以及届时应如何重新验证。
