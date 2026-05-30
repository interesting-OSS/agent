from typing import TypedDict, Annotated


class Todo(TypedDict):
    content: str
    status: str  # "pending" | "in_progress" | "completed"


class DeepAgentState(TypedDict):
    messages: list
    todos: list[Todo]
    files: dict[str, str]
