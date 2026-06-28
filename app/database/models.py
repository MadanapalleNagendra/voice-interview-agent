"""
app/database/models.py
SQLAlchemy ORM models for PostgreSQL.
"""

import uuid
from datetime import datetime

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.sql import func


class Base(DeclarativeBase):
    pass


class InterviewSession(Base):
    __tablename__ = "interview_sessions"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    candidate_name: Mapped[str | None] = mapped_column(String(255))
    language: Mapped[str] = mapped_column(String(10), default="en")
    started_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    ended_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    is_complete: Mapped[bool] = mapped_column(Boolean, default=False)
    overall_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    feedback_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    turns: Mapped[list["InterviewTurn"]] = relationship(back_populates="session", cascade="all, delete-orphan")


class InterviewTurn(Base):
    __tablename__ = "interview_turns"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[str] = mapped_column(ForeignKey("interview_sessions.id", ondelete="CASCADE"))
    turn_number: Mapped[int] = mapped_column(Integer)
    question_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    question_text: Mapped[str] = mapped_column(Text)
    candidate_answer: Mapped[str | None] = mapped_column(Text, nullable=True)
    interviewer_response: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_followup: Mapped[bool] = mapped_column(Boolean, default=False)
    score_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    session: Mapped["InterviewSession"] = relationship(back_populates="turns")
