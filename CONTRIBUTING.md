# 贡献指南（CONTRIBUTING）

本仓库是私有个人规则库；「贡献」主要指维护者本人新增或修订条目，也适用于日后公开子集的外部建议。

## 一、先确认要不要沉淀

只有**反复出现、可判定、能写成祈使句**的内容才值得入库。一次性的任务参数、临时路径、会话摘要请留在会话里，不要写入主干（见 `BOUNDARY.md`）。

## 二、四步评审（缺一不可）

| 步骤 | 你要做什么 | 机器怎么复核 |
| --- | --- | --- |
| 分类 | 判定三类资产与层级，填 `layer` / `asset_type` | `schema/frontmatter.schema.json` 枚举校验 |
| 查重 | 检索 `manifest.yaml` 的 `asset_index` 与既有正文 | `content_hash` 相同即阻断发布 |
| 敏感检查 | 检查令牌、密钥、邮箱、手机号、客户代号；判定 `sensitivity` | `config/sensitive-patterns.yaml` fail-closed 扫描 |
| 人工确认 | 用户确认并写 `approved_by`，`status: active` | `hub validate` 校验 `approved_by` 非空 |

结论写入 `audit/decisions/ADR-<4位>-*.md`，格式见 `templates/adr.md.tpl`。

## 三、frontmatter 与命名

必填字段：`id, layer, asset_type, source, scope, version, created_at, updated_at, status, sensitivity, owner, approved_by`。

- L0 额外必填 `override: forbidden`；L3 额外必填 `expires`（ISO 8601 UTC）。
- 技能额外必填 `name`（小写 kebab-case，与目录名一致）与 `description`（含触发条件 / 何时使用）。
- 可选：`applies_when`、`review_after`、`priority`、`supersedes`、`superseded_by`。
- 时间全部写带引号的 ISO 8601 UTC 字符串，避免 YAML 解析器把值转成日期对象。
- 文件名小写 kebab-case（禁空格、中文、下划线）；约定名 `CORE.md`、`SAFETY.md`、`SKILL.md`、`OVERRIDES.md`、`TEMPLATE.md`、`_index.md` 与经验文件的 `EXP-<4位>-` 前缀为例外，例外时短标题部分仍须 kebab-case。

## 四、正文要求

- 简体中文、真实可执行的句子；不写占位符、不写 lorem ipsum、不写笼统套话。
- 偏好一条一句祈使句；经验严格四段「场景 / 结论 / 依据 / 失效条件」。
- 引用外部事实附来源名称与核实状态；查不到写「未经核实」，**严禁编造链接**。
- 跨层引用只写规则 ID；经验晋升只写 `supersedes`，不复制旧正文。
- 文件 UTF-8 无 BOM + LF（`.gitattributes` 与 `.editorconfig` 已强制）。

## 五、提交前自检

```bash
python -m hub validate                    # 必须返回 ok
python -m hub publish                     # 生成物由生成器统一产出
python -m hub status                      # 5 类 Agent 一致、无漂移
python -m hub sync --plan                 # 差异报告符合预期
python -m hub publish --scope public      # 公开子集必须通过敏感扫描
```

- 不要手工编辑 `90-adapters/**` 与根目录 `AGENTS.md`。
- 不要把 `99-private/`、`config/hub.local.yaml`、`config/private-terms.txt`、`.state/`、`.env` 加入提交。
- 连续两次 `publish` 后 `git diff` 必须干净；派生产物正文不得出现当前时间。
- 提交信息用简体中文，说明改了哪条规则 ID 与为什么。
