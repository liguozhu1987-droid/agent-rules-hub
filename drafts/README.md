# 候选区（drafts/）

这里放**尚未通过评审**的规则、经验与技能草稿。候选区的文件：

- 不参与 `resolver.load_active_set` 加载，不进入任何常驻视图与公开发布物。
- 允许 `status: draft` 或暂缺 `approved_by`，但新建时请直接复制 `TEMPLATE.md` 保持四段结构。
- 入库前必须走完评审四步：分类 → 查重 → 敏感检查 → 人工确认（见 `GOVERNANCE.md`），并在 `audit/decisions/` 写一条 ADR。
- 通过后由维护者把文件移到 `00-constitution/`、`10-preferences/`、`20-experience/`、`30-skills/` 或 `40-projects/` 对应目录，并在 `manifest.yaml` 的 `asset_index` 与 `id_registry` 登记。
- 查重判定为重复的草稿保留来源引用后归档，正文不复制到主干，避免 `content_hash` 冲突。

## 命名

文件名使用小写 kebab-case（经验文件按 `EXP-<4位>-<kebab-case-短标题>.md`）。`TEMPLATE.md` 是本目录的约定模板文件，不参与资产校验。
