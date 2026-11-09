# 经验索引（20-experience/）

> 经验区属于**知识区**：只作为规则修订的输入，**不参与约束裁决**，且被生成器完全排除在常驻视图之外（零投影）。本索引仅供人查阅与 ADR 引用。
> 核实状态说明：「已核实」指架构阶段联网核实、来源见 `docs/02-架构设计.md` 附录；**本仓库未对链接可达性做独立复验**，落地前建议实测。

| ID | 文件 | 主题 | 核实状态 | 状态 | 复核时间（UTC） |
| --- | --- | --- | --- | --- | --- |
| EXP-0001 | `EXP-0001-agents-md-nearest-wins.md` | `AGENTS.md` 就近优先、会话显式指令覆盖一切 | 已核实（agents.md 官方规范，未独立复验） | active | 2027-05-09T00:00:00Z |
| EXP-0002 | `EXP-0002-git-windows-symlink.md` | Windows 软链需管理员/开发者模式，`core.symlinks=false` 会降级为纯文本 | 已核实（Git for Windows 官方 Wiki，未独立复验） | active | 2027-05-09T00:00:00Z |
| EXP-0003 | `EXP-0003-github-visibility-repo-level.md` | GitHub 可见性是仓库级，不能只公开某个分支 | 已核实（GitHub Community Verified answer，未独立复验） | active | 2027-05-09T00:00:00Z |

## 使用方式

- 新增经验：复制 `drafts/TEMPLATE.md`，按「场景 / 结论 / 依据 / 失效条件」四段填写，保持 `status: draft` 直到走完评审四步。
- 经验晋升为偏好时，只在新条目的 frontmatter 写 `supersedes: EXP-00xx`，**不复制旧正文**，并在 ADR 中记录理由。
- 经验正文出现「已核实」字样时必须同时写清来源名称；查不到就写「未经核实」，不得补造链接。
