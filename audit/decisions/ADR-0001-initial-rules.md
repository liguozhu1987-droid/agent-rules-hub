# ADR-0001 · 初始规则集入库

| 项 | 内容 |
| --- | --- |
| 状态 | 已确认 |
| 日期（UTC） | 2026-11-09 |
| 决策人 | 用户（approved_by: user） |
| 维护人 | gao |
| 影响范围 | `00-constitution/`、`10-preferences/`、`20-experience/`、`30-skills/`、`40-projects/` |

## 背景

用户希望把散落在多次会话里的偏好、经验与常用流程收敛成一个可版本化、可离线使用、可被多类 Agent 读取的单一事实源。初始输入是 `docs/01-PRD.md` 与 `docs/02-架构设计.md`，二者已完成需求与架构阶段评审，但本阶段**不产出可运行代码**，需要一次落地决策来确定首批入库范围。

## 决策

1. 首批入库 2 条 L0 宪法、7 条 L1 稳定偏好、3 条经验、2 个技能、1 条 L3 项目临时例外，共 15 条资产；全部写入 `manifest.yaml` 的 `asset_index`。
2. 事实源为私有 Git 仓库中的 Markdown + YAML frontmatter；派生产物一律由生成器写入 `90-adapters/`，标记只读，禁止手工编辑。
3. 经验区不参与约束裁决、零投影到常驻视图；技能按渐进式披露只暴露 `name` + `description` 索引行。
4. 裁决链固定为 rank 0~4：用户会话显式指令 > L0 宪法 > L3 项目临时（有效期内）> L1 稳定偏好 >（L2 技能与经验区不参与覆盖）。
5. 分发方式采用「生成器投影 + 纯文件复制」，不使用符号链接；依据是 `EXP-0002`（Git for Windows 官方 Wiki，架构阶段联网核实，本仓库未独立复验）。

## 评审四步结论

| 步骤 | 结论 | 证据 |
| --- | --- | --- |
| 分类 | L0 两条（硬约束、安全红线）、L1 七条、经验三条、技能两个、L3 一条；分类与 `schema/frontmatter.schema.json` 枚举一致 | 各文件 frontmatter 的 `layer` 与 `asset_type` |
| 查重 | 15 条正文两两不同，无重复条款；经验与 L0 的「不编造事实」为上下游细化关系，非重复正文 | 逐条人工比对；后续由 `content_hash` 机器复核 |
| 敏感检查 | 2 条 L0、7 条 L1、2 个技能为 `public`；3 条经验与 1 条 L3 为 `private`；正文中无令牌、密钥、邮箱、手机号或客户代号 | 人工检查 + 后续由 `config/sensitive-patterns.yaml` 机器复核 |
| 人工确认 | 用户确认首批范围与 `approved_by: user`；所有条目 `status: active` | 本 ADR |

## 影响

- 正向：规则 ID、版本、优先级与核实状态首次可机器判定，`validate / publish / status / sync --plan` 具备稳定输入。
- 约束：新增或修订必须回到 `drafts/` 走四步评审，运行时 Agent 只读主干与派生产物，不得自动写回（见 `BOUNDARY.md`）。
- 待办：`EXP-0001` ~ `EXP-0003` 的链接可达性、WorkBuddy 用户级目录实际路径、Claude `@AGENTS.md` 指针是否被目标版本支持，均**未经本仓库官方核实，需本机实测**（见 `README.md` 开放问题清单）。
