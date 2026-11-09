"""5 类 Agent 的 Strategy 适配器集合。"""

from hub.adapters.agents_md import AgentsMdAdapter
from hub.adapters.claude import ClaudeAdapter
from hub.adapters.copilot import CopilotAdapter
from hub.adapters.cursor import CursorAdapter
from hub.adapters.workbuddy import WorkBuddyAdapter

ADAPTER_REGISTRY = {
    "agents_md": AgentsMdAdapter,
    "claude": ClaudeAdapter,
    "cursor": CursorAdapter,
    "copilot": CopilotAdapter,
    "workbuddy": WorkBuddyAdapter,
}

__all__ = [
    "ADAPTER_REGISTRY",
    "AgentsMdAdapter",
    "ClaudeAdapter",
    "CopilotAdapter",
    "CursorAdapter",
    "WorkBuddyAdapter",
]
