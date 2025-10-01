from pydantic import BaseModel, Field, field_validator
from datetime import datetime, timezone
from src.enums.todos import TodoCategory
from uuid import UUID


class TodoRequest(BaseModel):
    title: str = Field(
        min_length=5,
        max_length=100,
        description="Title should be between 5 and 100 chars",
    )
    description: str = Field(
        min_length=20,
        max_length=200,
        description="Description could be up to 200 chars",
    )
    categories: TodoCategory
    priority: int = Field(gt=0, lt=11)
    complete: bool = False
    deadline: datetime | None = None

    @field_validator("deadline")
    @classmethod
    def deadline_must_be_future(cls, v):
        if v and v < datetime.now(timezone.utc):
            raise ValueError("Deadline must be in the future")
        return v


class TodoResponse(BaseModel):
    id: UUID
    title: str
    description: str
    categories: TodoCategory
    priority: int
    complete: bool
    deadline: datetime

    model_config = {"from_attributes": True}
