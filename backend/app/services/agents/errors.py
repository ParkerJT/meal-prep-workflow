from __future__ import annotations


class WorkflowRejection(Exception):
    """Semantic validation failure during recipe generation."""

    def __init__(self, code: str, message: str) -> None:
        self.code = code
        self.message = message
        super().__init__(message)
