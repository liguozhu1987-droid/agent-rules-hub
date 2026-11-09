---
id: EXP-0003
layer: experience
asset_type: experience
source: "[A2] GitHub Community 官方讨论 Verified answer（架构阶段已联网核实，本仓库未独立复验）"
scope: { level: global }
version: 1
created_at: "2026-11-05T11:00:00Z"
updated_at: "2026-11-09T08:00:00Z"
review_after: "2027-05-09T00:00:00Z"
status: active
sensitivity: private
owner: gao
approved_by: user
---

# EXP-0003 · GitHub 可见性是仓库级而非分支级

## 场景

希望只把规则中枢里的「可公开技能清单」公开出去，同时让含个人偏好的部分保持私有，考虑在私有仓库里单独开放一个公开分支。

## 结论

不可行。可见性是仓库级属性，必须拆成两个物理仓库：私有主干仓库 + 单独生成的公开子集仓库。因此本仓库整体为私有，`publish --scope public` 只导出显式标记的公开子集。

## 依据

已核实（架构阶段联网核实，来源：GitHub Community 官方讨论 Verified answer，https://github.com/orgs/community/discussions/131435 ；链接沿用 docs/02-架构设计.md 附录，本仓库未独立复验）。该回答明确「一个仓库要么公开要么私有，不能只公开某一个分支而把其余分支设为私有」；GitHub 官方文档亦说明可见性变更作用于整个仓库及其分支与 fork 网络。

## 失效条件

GitHub 后续若正式推出分支级或目录级可见性能力，本条需重新核实并更新；在官方能力上线且有文档佐证前，不得假设「公开分支」可用。本条只描述平台能力，不代表对具体账号权限设置的实测结论。
