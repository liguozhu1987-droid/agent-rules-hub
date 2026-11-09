# 示例项目例外说明

本目录是 L3「项目临时例外」的可运行示例，用于验证生成器能否正确处理 `expires`、`sensitivity: private` 与项目级 `scope`。

## 为何需要例外

`OVERRIDES.md` 要求本示例项目的交付物额外附一页「版本与核实状态」说明。它只影响 `40-projects/example-project/**` 路径下的产物，不改变全局的简体中文、结构化输出与不编造事实等 L0 约束。按裁决链，L3 在有效期内优先于 L1，但**永远不能覆盖 L0**。

## 何时清理

- 硬期限：`expires: 2026-12-31T00:00:00Z`（UTC）。到期后 `resolver.load_active_set` 自动不再加载，`status` 会把它列入待复核队列。
- 提前清理：示例项目归档、或用户确认不再需要该附加说明页时立即删除，并写一条 ADR 记录。
- 清理动作：删除本目录或把 `OVERRIDES.md` 的 `status` 改为 `deprecated`，随后重新 `python -m hub publish` 并核对 `audit/releases/` 快照。

## 谁确认

| 角色 | 职责 |
| --- | --- |
| 用户（approved_by: user） | 确认例外内容、有效期与是否提前清理 |
| 仓库维护者（owner: gao） | 维护 frontmatter、走评审四步、更新 `manifest.yaml` 与 ADR |
| 生成器 | 只读本文件，负责把 `expires` 追加到项目级投影末尾，不改写规则正文 |

## 私有说明

本目录 `sensitivity: private`，**不进入任何公开发布物**。演示数据不含真实客户信息；若替换为真实项目，须同步检查 `config/private-terms.txt`（不入库）。
