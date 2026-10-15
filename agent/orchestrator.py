"""
EduSync AI — Multi-Agent Orchestrator Module
Re-exports SupervisorAgent and MultiToolOrchestrator for full backwards compatibility.
"""

from agent.supervisor import SupervisorAgent, MultiToolOrchestrator
from agent.specialists import (
    KnowledgeAgent,
    AssessmentAgent,
    PerformanceAgent,
    PlanningAgent,
    ProgressAgent,
)
from agent.state import AgentResult, ToolTrace, AgentTraceStep

__all__ = [
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
