"""
EduSync AI — Multi-Agent Architecture State & Trace Models
Defines execution traces, agent messages, structured responses, and multi-agent coordination states.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional


@dataclass
class AgentTraceStep:
    """Represents a single specialist or supervisor step in multi-agent execution."""

    step_number: int
    agent_name: str
    action: str
    status: str  # 'SUCCESS', 'FAILED', 'SKIPPED'
    summary: str
    data: Any = None
    timestamp: str = field(default_factory=lambda: datetime.now().strftime("%H:%M:%S"))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "step_number": self.step_number,
            "agent_name": self.agent_name,
            "action": self.action,
            "status": self.status,
            "summary": self.summary,
            "timestamp": self.timestamp,
        }


# Backward compatibility alias for UI rendering that accesses tool_name
@dataclass
class ToolTrace:
    """Represents a single step in execution trace (compatible with UI expectations)."""

    step_number: int
    tool_name: str
    arguments: Dict[str, Any]
    status: str  # 'SUCCESS', 'FAILED', 'SKIPPED'
    summary: str
    data: Any = None
    agent_name: str = ""
    timestamp: str = field(default_factory=lambda: datetime.now().strftime("%H:%M:%S"))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "step_number": self.step_number,
            "tool_name": self.tool_name,
            "agent_name": self.agent_name,
            "arguments": self.arguments,
            "status": self.status,
            "summary": self.summary,
            "timestamp": self.timestamp,
        }


@dataclass
class AgentResult:
    """Final outcome of a multi-agent orchestrator / supervisor run."""

    user_query: str
    goal: str
    mode: str  # 'AI Mode (Gemini)' or 'Demo Mode (Deterministic)'
    traces: List[ToolTrace] = field(default_factory=list)
    final_response: str = ""
    recommended_next_action: str = ""
    success: bool = True
    iterations: int = 0
    extracted_data: Dict[str, Any] = field(default_factory=dict)
    participating_agents: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "user_query": self.user_query,
            "goal": self.goal,
            "mode": self.mode,
            "traces": [t.to_dict() for t in self.traces],
            "final_response": self.final_response,
            "recommended_next_action": self.recommended_next_action,
            "success": self.success,
            "iterations": self.iterations,
            "participating_agents": self.participating_agents,
        }
