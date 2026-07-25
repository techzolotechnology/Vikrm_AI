"""
Tool abstraction — every workflow "tool" node and (from Milestone 9
onward) every agent tool call goes through this interface. One method,
`run`, takes a plain string input and returns a plain string output,
so tools can be composed in a workflow without each node needing to
know a tool's internal argument shape.

`ToolContext` carries the request-scoped information a *user-scoped*
tool needs (whose memories/documents to search, a DB session to query
them with) without forcing every tool to accept a DB session — stateless
tools (calculator, http_request) simply ignore it.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any


class ToolError(Exception):
    pass


@dataclass
class ToolContext:
    user_id: int
    session: Any = None  # AsyncSession, typed loosely here to avoid a hard SQLAlchemy import


class Tool(ABC):
    name: str
    description: str

    @abstractmethod
    async def run(self, input_text: str, *, context: ToolContext | None = None) -> str:
        raise NotImplementedError
