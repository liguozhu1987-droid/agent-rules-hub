---
id: CONST-0002
layer: L0
asset_type: preference
source: "PRD 约束 C4 与用户确认：私有仓库为本仓库唯一事实源，公开物必须是显式筛选的子集"
scope: { level: global }
version: 1
created_at: "2026-11-02T10:00:00Z"
updated_at: "2026-11-09T08:00:00Z"
status: active
override: forbidden
sensitivity: public
owner: gao
approved_by: user
---

# L0 安全红线：敏感隔离与审批（CONST-0002）

本文件是 L0 宪法，`override: forbidden`。它规定「什么绝不能自动做」，与 `CORE.md` 同级且互不覆盖。

## 条款

- 标记为 `sensitivity: private` 的条目、密钥、令牌、客户代号、联系方式与内部术语，不得进入任何公开发布物；公开子集只能由 `publish --scope public` 显式生成。
- `99-private/`、`config/hub.local.yaml`、`config/private-terms.txt`、`.state/`、`.env` 一律不入库、不公开；运行时若存在，仅在本地合并，且不得回写主干。
- 敏感扫描采用 fail-closed：任一模式命中即中止发布，报错只给出文件路径、行号与模式编号，绝不回显命中内容本身。
- 任何新增或修订规则必须走「分类 → 查重 → 敏感检查 → 人工确认」四步评审；未取得 `approved_by` 的条目保持 `draft`，不参与加载与投影。
- 经验晋升、查重合并只写 `supersedes` 关联，不复制旧正文；跨层引用只写规则 ID，不复制条款句子。
