"""
EduSync AI — Multi-Agent System Package
Exports SupervisorAgent, BaseAgent, and all specialist agents:
KnowledgeAgent, AssessmentAgent, PerformanceAgent, PlanningAgent, ProgressAgent.
"""

from agent.base import BaseAgent
from agent.specialists import (
    KnowledgeAgent,
    AssessmentAgent,
    PerformanceAgent,
    PlanningAgent,
    ProgressAgent,
)
from agent.supervisor import SupervisorAgent, MultiToolOrchestrator
from agent.state import AgentResult, ToolTrace, AgentTraceStep

__all__ = [
    "BaseAgent",
    "SupervisorAgent",
    "MultiToolOrchestrator",
    "KnowledgeAgent",
    "AssessmentAgent",
    "PerformanceAgent",
    "PlanningAgent",
    "ProgressAgent",
    "AgentResult",
    "ToolTrace",
    "AgentTraceStep",
]
