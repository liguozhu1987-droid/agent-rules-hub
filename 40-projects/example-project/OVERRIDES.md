---
id: PROJ-example-project-0001
layer: L3
asset_type: preference
source: "示例项目交付规范（演示用示例数据，见同目录 README.md）"
scope: { level: project, projects: ["example-project"], paths: ["40-projects/example-project/**"] }
expires: "2026-12-31T00:00:00Z"
version: 1
created_at: "2026-11-09T08:00:00Z"
updated_at: "2026-11-09T08:00:00Z"
status: active
sensitivity: private
owner: gao
approved_by: user
---

# 项目临时例外（PROJ-example-project-0001）

- 本示例项目的对外交付物在正文首页附一页「版本与核实状态」说明，列明仓库版本、规则 ID 与未核实项；其余格式与语言仍遵循 L0 与 L1。

> 本条目仅用于演示 L3 的 `expires` 与 `sensitivity: private` 机制，不改写也不覆盖任何 L0 硬约束。有效期至 2026-12-31T00:00:00Z（UTC），到期后不再加载，也不进入 `publish --scope public` 的公开子集。
