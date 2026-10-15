"""
EduSync AI — Base Agent Interface
Defines the standard contract for specialist and supervisor agents.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional


class BaseAgent(ABC):
    """
    Common abstract interface for all EduSync AI agents.
    Provides standardized execution, error handling, and reporting.
    """

    def __init__(self, name: str, description: str, db_path: str = "edusync.db"):
        self.name = name
        self.description = description
        self.db_path = db_path

    @abstractmethod
    def run(self, query: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Executes the agent's core responsibility.

        Returns a dictionary containing:
            - status: 'SUCCESS' or 'FAILED'
            - message: human-readable summary
            - data: structured result
            - error: optional error message
        """
        pass

    def safe_run(self, query: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Executes run with catch-all exception handling to guarantee
        that a specialist failure never crashes the application.
        """
        try:
            return self.run(query, context=context)
        except Exception as e:
            return {
                "status": "FAILED",
                "message": f"{self.name} encountered an error: {str(e)}",
                "data": {},
                "error": str(e),
                "agent": self.name,
            }
