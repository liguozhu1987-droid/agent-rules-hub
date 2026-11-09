"""agent-rules-hub 工具链：把规则主干编译成 5 类只读派生产物。

设计要点：主干是唯一可编辑源码，``90-adapters/**`` 与根目录 ``AGENTS.md``
是生成物；任何产物都不得写入当前时间，以保证 publish 幂等。
"""

from __future__ import annotations

import os
from pathlib import Path

__version__ = "1.0.0"
GENERATED_BY = "agent-rules-hub"


def find_hub_root(start: Path | None = None) -> Path:
    """解析仓库根目录：优先 HUB_ROOT 环境变量，其次从包位置向上找 manifest.yaml。

    Args:
        start: 可选的起始目录；默认取本包所在目录的父目录。

    Returns:
        含 ``manifest.yaml`` 与 ``config/`` 的仓库根目录。
    """
    env_root = os.environ.get("HUB_ROOT", "").strip()
    if env_root:
        candidate = Path(env_root).expanduser().resolve()
        if (candidate / "manifest.yaml").is_file():
            return candidate

    base = (start or Path(__file__).resolve().parent.parent).resolve()
    for candidate in (base, *base.parents):
        if (candidate / "manifest.yaml").is_file() and (candidate / "config").is_dir():
            return candidate
    return base


ROOT: Path = find_hub_root()

__all__ = ["ROOT", "GENERATED_BY", "__version__", "find_hub_root"]
