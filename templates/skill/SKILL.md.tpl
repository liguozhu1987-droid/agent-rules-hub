---
id: {{ id }}
name: {{ name }}
description: "{{ description }}"
layer: L2
asset_type: skill
source: "{{ source }}"
scope: { level: global }
applies_when:
  task_types: ["文档撰写"]
  triggers: ["触发词"]
  file_globs: ["docs/**/*.md"]
version: 1
created_at: "{{ created_at }}"
updated_at: "{{ updated_at }}"
status: draft
sensitivity: public
owner: {{ owner }}
approved_by: "{{ approved_by }}"
---

# {{ title }}（{{ name }}）

## 触发条件

写清什么时候使用、什么时候不使用。`name` 必须小写 kebab-case 且与目录名一致，`description` 必须包含触发条件与「何时使用」。

## 步骤

1. 第一步：写清输入来自哪里、产出什么。
2. 第二步：写清分类或处理规则。
3. 第三步：写清依据与核实状态怎么标注。
4. 第四步：写清使用哪个 `references/` 模板。
5. 第五步：写清自检与交付形态（可读正文 + 落盘文件）。

## 验收

- 每条验收标准可机器或人工判定，写清执行什么命令、观察什么输出。
- 无编造的来源链接或数据；未核实项明确标注。
- 文件为 UTF-8 无 BOM、LF 换行，含空格路径可正常读写。

## 附属资源

- `references/` 下放模板或检查清单，按需加载，不在会话启动时读入。
