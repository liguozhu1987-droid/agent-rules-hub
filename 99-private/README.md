# 99-private/ · 本机私有覆盖层（不入库）

> **本目录只有一个说明文件入库，其余内容一律不进 Git、不进公开发布物。** `.gitignore` 已排除 `99-private/`。

## 用途

放置本设备专用的覆盖规则、临时例外与不便公开的私有词表，例如：

- `overrides.yaml`：只在本机生效的规则补充或关闭项。
- 尚未走完评审四步、但需要在本机临时试用的条目。

## 合并顺序

`主干（manifest.yaml + 各资产目录）` < `99-private/overrides.yaml` < `用户当前会话显式指令`。

私有覆盖层**不能覆盖 L0 宪法**（`override: forbidden`）；若试图覆盖，生成器应记为 `needs_review` 并向用户提问，而不是静默生效。

## 硬性边界

- 本目录、`config/hub.local.yaml`、`config/private-terms.txt`、`.state/`、`.env` 均不入库、不公开。
- 运行时 Agent 只读主干与派生产物，不得把会话里的动态记忆自动写入本目录或主干（见 `BOUNDARY.md`）。
- `publish --scope public` 只导出 `sensitivity: public` 的显式子集；私有覆盖层永远不参与公开投影。
- 若本目录出现真实密钥或客户信息，仍须遵守 `CONST-0002` 的敏感红线，不得提交到任何仓库。
