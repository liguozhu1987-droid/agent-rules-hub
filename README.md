# agent-rules-hub · 个人 Agent 规则中枢

一个**私有 Git 仓库**，把散落在多次会话里的偏好、经验与常用流程收敛成单一事实源，再由确定性生成器编译成 5 类 Agent 各自能读的只读视图。

核心思路是「编译器隐喻」：只有 `00/` ~ `40/`、`drafts/` 下的 Markdown + YAML frontmatter 是**可编辑源码**；`90-adapters/**` 与根目录 `AGENTS.md` 是**生成物，禁止手改**；`manifest.yaml` 是构建清单与 ID 注册表；`audit/releases/<版本>/snapshot.json` 是每次发布的校验和快照。任何时刻只有一份可编辑正文。

## 5 分钟快速开始

环境要求：Python 3.11+；Windows / macOS / Linux 均可（本仓库在含空格路径 `C:/Users/Hello World/...` 下开发与验证）。

```bash
# 1. 进入仓库（路径含空格时务必加引号）
cd "C:/Users/Hello World/WorkBuddy/My Memory/agent-rules-hub"

# 2. 安装依赖（仅 3 个第三方包，其余用标准库）
python -m pip install -r requirements.txt

# 3. 校验主干：schema / 条件必填 / ID 唯一 / 文件名 / 正文查重
python -m hub validate

# 4. 编译全部投影并写发布快照
python -m hub publish

# 5. 查看 5 类 Agent 的版本、一致性与漂移
python -m hub status
python -m hub sync --plan
```

期望结果：`validate` 打印 `ok` 并退出码 0；`publish` 生成 5 类投影且所有常驻视图 `core_sha256` 相等；连续两次 `publish` 后 `git diff` 干净（产物逐字节相同，正文不含当前时间）。

其他命令：`python -m hub publish --scope public` 只导出公开子集；`python -m hub status --json` / `python -m hub sync --plan --json` 输出机器可读结构 `{ok, data, warnings, errors}`。

## 目录导航

| 目录 / 文件 | 作用 | 可编辑 |
| --- | --- | --- |
| `00-constitution/` | L0 宪法：硬约束与安全红线，`override: forbidden` | 是 |
| `10-preferences/` | L1 稳定偏好：一条一文件、一条祈使句 | 是 |
| `20-experience/` | 经验知识区：四段结构，不参与裁决、零投影 | 是 |
| `30-skills/` | L2 技能：`SKILL.md` + `references/`，渐进式披露 | 是 |
| `40-projects/` | L3 项目临时例外，必填 `expires` | 是 |
| `drafts/` | 候选区，评审四步前不参与任何发布 | 是 |
| `90-adapters/` | 5 类 Agent 的只读派生产物 | **否** |
| `audit/decisions/` | ADR 决策记录 | 是 |
| `audit/releases/` | 版本快照（全文件 SHA-256 + 变更 ID + 影响 Agent） | 否（生成） |
| `99-private/` | 本机私有覆盖层，不入库、不公开 | 否（本地） |
| `config/` | 优先级、Agent 注册表、敏感模式、全局配置 | 是 |
| `schema/` | frontmatter 机器契约（必填 / 条件必填 / 枚举） | 是 |
| `templates/` | 新建条目与各 Agent 投影的模板 | 是 |
| `hub/` | Python 工具链（`validate / publish / status / sync`） | 是 |
| `manifest.yaml` | 版本、裁决链镜像、ID 注册表、资产索引 | 是 |

## 如何接入各 Agent

一页清单见 `ONBOARDING.md`。摘要：

| Agent | 认哪些文件 | 放到哪 |
| --- | --- | --- |
| 通用 `AGENTS.md` | 根目录 `AGENTS.md`（或 `90-adapters/AGENTS.md`） | 项目根 |
| Claude Code | `90-adapters/CLAUDE.md`（指针 `@AGENTS.md`）+ `claude/rules/` | 项目根 + `.claude/rules/` |
| Cursor | `90-adapters/cursor/rules/*.mdc` | 项目 `.cursor/rules/` |
| GitHub Copilot | `90-adapters/copilot/copilot-instructions.md` + `instructions/*.instructions.md` | `.github/` |
| WorkBuddy | `90-adapters/workbuddy/MEMORY.md` + `skills/**` | 用户级记忆与技能目录 |

**生成器只写到 `90-adapters/` 与本仓库根目录，不直接改动你机器上的 Agent 配置目录**；`sync --plan` 先输出差异报告，确认后再复制落盘，并做 SHA-256 漂移检测。

## 如何推送到 GitHub

本仓库是**私有仓库**。可见性是仓库级属性，不能只公开某个分支（依据 `EXP-0003`，GitHub Community Verified answer，架构阶段联网核实、本仓库未独立复验）。因此：

1. 由维护者在 GitHub 创建**私有**空仓库，不在本地执行任何 push。
2. 本地确认 `git status` 干净后，用 `git remote add origin <私有仓库地址>` 关联，再由维护者执行首次推送。
3. 公开内容只能由 `python -m hub publish --scope public` 生成显式子集，推送到**另一个**独立公开仓库；本仓库整体永不公开。
4. `.gitignore` 已排除 `99-private/`、`config/hub.local.yaml`、`config/private-terms.txt`、`.state/`、`.env` 等；推送前用 `python -m hub validate` 与敏感扫描复核。

## 设计文档（已完成产出，原样保留）

- `AI-Agent-经验偏好技能沉淀方案.md` — 初始策划方案
- `docs/01-PRD.md` — 产品需求（三类资产、四层模型、约束与需求）
- `docs/02-架构设计.md` — 系统架构、数据契约、投影映射、共享约定
- `docs/class-diagram.mermaid`、`docs/sequence-diagram.mermaid` — 类图与时序图

## 明确标注：哪些结论未经官方核实、必须实测

> 下表是**开放问题清单**，不是已确认事实。凡标注「未经核实」的结论都不得当作硬性前提使用。

| # | 结论 / 参数 | 当前状态 | 需怎么实测 |
| --- | --- | --- | --- |
| 1 | WorkBuddy 用户级 `MEMORY.md` 与 `skills/` 的真实落盘路径、加载优先级 | **未经官方核实**（来自 PRD 1.1 第三方资料） | 在新会话询问 Agent「列出你当前加载的规则 ID 与版本」，与 `python -m hub status` 比对 |
| 2 | Claude Code 是否支持 `@AGENTS.md` 指针导入、无 `CLAUDE.md` 时是否读取 `AGENTS.md` | **未经官方核实**（第三方资料） | 部署指针版 `CLAUDE.md` 后新开会话，检查规则 ID 是否可见；不生效则切 inline 模式 |
| 3 | Cursor `.mdc` 的 `globs` / `alwaysApply` 字段语义与生效范围 | **未经官方核实**（第三方资料） | 用 `config/agents.yaml` 的映射规则生成一个 `.mdc`，在目标版本 Cursor 中观察是否命中 |
| 4 | Copilot `*.instructions.md` 的 `applyTo` 语法与匹配行为 | **未经官方核实**（第三方资料） | 部署一条带 `applyTo` 的指令文件，打开匹配路径观察是否生效 |
| 5 | `AGENTS.md` 就近优先与 32 KiB 拼接上限等具体数值 | **未经官方核实**（第三方资料 / 保守值） | 用超过预算的样本在目标工具中实测，按结果调整 `config/hub.yaml` 长度预算 |
| 6 | `EXP-0001` ~ `EXP-0003` 引用的官方链接可达性与最新版措辞 | 架构阶段联网核实，**本仓库未独立复验** | 逐条打开 `docs/02-架构设计.md` 附录链接复验，变更则更新经验条目与 ADR |
| 7 | 长度预算 8 KiB / 200 行 / 2 KiB | **经验判断**，非官方限制 | 结合 #5 实测结果调整 |
| 8 | Windows 软链默认行为（`core.symlinks=false`） | 架构阶段联网核实（Git for Windows 官方 Wiki），**本机未复验** | 在目标设备执行 `git config --get core.symlinks` 与一次克隆实测 |

引用外部事实必须附来源名称与核实状态；查不到标注「未经核实」，严禁编造链接（`CONST-0001`、`CONST-0002`）。
