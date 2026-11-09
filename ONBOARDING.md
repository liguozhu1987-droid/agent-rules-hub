# 一页接入清单（ONBOARDING）

目标：把 `python -m hub publish` 产出的只读文件放到 5 类 Agent 约定的位置，并验证确实生效。全部路径以本仓库根为基准；`sync --plan` 只出差异报告，**不自动写你的 Agent 目录**。

| Agent | 认哪些文件 | 放在哪 | 如何验证生效 |
| --- | --- | --- | --- |
| **通用 / Codex（`agents_md`）** | 根目录 `AGENTS.md`；`90-adapters/AGENTS.md` 为其字节级副本 | 项目根目录（就近优先，离被编辑文件最近的一份生效） | 新开会话问「列出当前加载的规则 ID 与版本」，应能看到 `CONST-0001`、`PREF-0001` 等，且版本等于 `manifest.yaml.version` |
| **Claude Code（`claude`）** | `90-adapters/CLAUDE.md`（默认指针模式 `@AGENTS.md`）；`90-adapters/claude/rules/*.md` 为分主题补充 | 项目根 `CLAUDE.md`；补充规则放 `.claude/rules/` | 指针模式需实测目标版本是否支持 `@` 导入；不生效时改用 inline 模式（同一 `core_block`，`core_sha256` 相等） |
| **Cursor（`cursor`）** | `90-adapters/cursor/rules/*.mdc` | 项目 `.cursor/rules/` | 打开匹配 `globs` 的文件，查看规则是否被引用；`alwaysApply: true` 的规则应常驻 |
| **GitHub Copilot（`copilot`）** | `90-adapters/copilot/copilot-instructions.md`（全仓常驻）；`90-adapters/copilot/instructions/*.instructions.md`（按 `applyTo` 生效） | `.github/` 下对应文件 | 打开 `applyTo` 命中的路径，确认指令出现在上下文；`applyTo` 语法需本机实测 |
| **WorkBuddy（`workbuddy`）** | `90-adapters/workbuddy/MEMORY.md`；`90-adapters/workbuddy/skills/<name>/SKILL.md` 及 `references/` | 用户级记忆目录与用户级技能目录（**真实路径未经官方核实，需实测**） | 新会话询问已加载规则 ID；技能应只暴露 `name` + `description`，命中触发词后才读入完整正文 |

## 通用三步

1. 生成：`python -m hub validate` → `python -m hub publish`。
2. 预检：`python -m hub status` 看 5 类 Agent 的版本 / 一致性 / 漂移；`python -m hub sync --plan` 看按规则 ID 的差异报告。
3. 落盘：确认 diff 后，把 `90-adapters/` 下对应文件复制到各自目标目录；复制前后用 SHA-256 比对（快照里有每文件校验和）。

## 字段由配置生成，禁止手写

- Cursor `.mdc` 的 `description` ← `applies_when.triggers` + `task_types`；`globs` ← `applies_when.file_globs ∪ scope.paths`；`alwaysApply` ← `layer ∈ {L0,L1} 且 scope.level == global`。
- Copilot `*.instructions.md` 的 `applyTo` ← `scope.paths ∪ applies_when.file_globs`（为空填 `**`）；L3 额外强制带项目路径 glob，并在正文末尾追加 `expires` 提示。
- L2 技能在各常驻视图**只保留 `name` + `description` 索引行**；完整 `SKILL.md` 只在 WorkBuddy 的 `skills/` 下以副本形式出现。
- 经验区（`20-experience/`）**零投影**：物理上不会出现在任何常驻视图。

## 接入风险提示

- 指针模式 `@AGENTS.md`、WorkBuddy 用户级路径、Cursor / Copilot 的字段语义均**未经官方核实，需本机实测**（详见 `README.md` 开放问题清单）。
- 不要在派生文件里直接改内容；改动会被漂移检测标红并在下次 `publish` 覆盖。
- 含空格路径请始终加引号；所有产物为 UTF-8 无 BOM + LF，不要用会转换换行的编辑器另存。

## 验证清单（逐条打勾）

- [ ] `python -m hub validate` 返回 `ok`
- [ ] `python -m hub publish` 生成 5 类投影，所有常驻视图 `core_sha256` 相等
- [ ] `python -m hub status` 中 5 行均为一致、无漂移
- [ ] 新会话能列出正确的规则 ID 与版本
- [ ] 手工改动一个派生文件后，`sync --plan` 能报出漂移
