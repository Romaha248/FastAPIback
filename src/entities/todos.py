from src.database.dbcore import Base
from sqlalchemy import (
    Column,
    String,
    Boolean,
    Integer,
    DateTime,
    func,
    ForeignKey,
    Enum,
    Index,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from src.enums.todos import TodoCategory


class Todos(Base):
    __tablename__ = "todos"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        unique=True,
        nullable=False,
    )
    user_id = Column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    title = Column(String(100), nullable=False)
    description = Column(String(200), nullable=False)
    categories = Column(
        Enum(TodoCategory, name="todo_category"),
        default=TodoCategory.OTHER,
        nullable=False,
    )
    priority = Column(Integer, nullable=False)
    complete = Column(Boolean, default=False, nullable=False)
    deadline = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    user = relationship("Users", back_populates="todos")

    __table_args__ = (Index("ix_todos_user_id", "user_id"),)
