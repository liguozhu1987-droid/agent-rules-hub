# 公开技能清单（SKILLS-INDEX）

> 只列出 `sensitivity: public` 且 `status: active` 的技能。常驻视图只暴露下表的 `name` + `description` 索引行；完整正文按需加载。`publish --scope public` 只导出这些条目。

| name | 触发条件 / 何时使用 | 完整文件 | 附属资源 |
| --- | --- | --- | --- |
| `ecosystem-research` | 需要技术选型、方案对比、竞品调研或核实某项官方能力时；触发词 调研、选型、对比、有没有更好的、是否官方支持 | `30-skills/ecosystem-research/SKILL.md` | `references/source-checklist.md` |
| `weekly-report` | 需要写周报、周总结、周期性进展汇报时；触发词 周报、周总结、本周进展、汇报 | `30-skills/weekly-report/SKILL.md` | `references/weekly-report-template.md` |

## 渐进式披露约定

- 会话启动只加载 `name` + `description`（约百 token 级），不读入完整 `SKILL.md`。
- 命中 `applies_when.task_types` 或 `triggers` 后才读入完整正文与 `references/`。
- `name` 必须小写 kebab-case 且与目录名一致；`description` 必须写清触发条件与何时使用。
- WorkBuddy 的 `90-adapters/workbuddy/skills/<name>/` 是完整副本（含 `references/`），其余 4 类常驻视图只保留索引行。
- 经验区不属于技能清单，零投影。

## 新增技能

复制 `templates/skill/SKILL.md.tpl` 到 `30-skills/<kebab-case>/SKILL.md`，补齐 frontmatter 与「触发条件 / 步骤 / 验收」，走评审四步后登记 `manifest.yaml`，再执行 `python -m hub publish`。
