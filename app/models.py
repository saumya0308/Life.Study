from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .db import Base


class Student(Base):
    __tablename__ = "students"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    sessions: Mapped[list["GameSession"]] = relationship(back_populates="student")


class GameSession(Base):
    __tablename__ = "game_sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id"), nullable=False)
    game_name: Mapped[str] = mapped_column(String(120), default="Jungle Ancient Ruin Adventure")
    started_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    score: Mapped[int] = mapped_column(Integer, default=0)
    rooms_completed: Mapped[int] = mapped_column(Integer, default=0)
    correct_answers: Mapped[int] = mapped_column(Integer, default=0)
    incorrect_answers: Mapped[int] = mapped_column(Integer, default=0)
    longest_streak: Mapped[int] = mapped_column(Integer, default=0)
    treasures_found: Mapped[int] = mapped_column(Integer, default=0)
    torches_remaining: Mapped[int] = mapped_column(Integer, default=5)
    current_streak: Mapped[int] = mapped_column(Integer, default=0)
    current_room: Mapped[int] = mapped_column(Integer, default=1)
    total_rooms: Mapped[int] = mapped_column(Integer, default=15)
    completed: Mapped[bool] = mapped_column(Boolean, default=False)
    game_over: Mapped[bool] = mapped_column(Boolean, default=False)

    student: Mapped["Student"] = relationship(back_populates="sessions")
    attempts: Mapped[list["QuestionAttempt"]] = relationship(
        back_populates="session", cascade="all, delete-orphan"
    )
    treasures: Mapped[list["SessionTreasure"]] = relationship(
        back_populates="session", cascade="all, delete-orphan"
    )


class QuestionAttempt(Base):
    __tablename__ = "question_attempts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    session_id: Mapped[int] = mapped_column(ForeignKey("game_sessions.id"), nullable=False)
    question_id: Mapped[int] = mapped_column(Integer, nullable=False)
    question_text: Mapped[str] = mapped_column(Text, nullable=False)
    selected_answer: Mapped[str] = mapped_column(Text, nullable=False)
    correct_answer: Mapped[str] = mapped_column(Text, nullable=False)
    explanation: Mapped[str] = mapped_column(Text, nullable=False)
    topic: Mapped[str] = mapped_column(String(120), nullable=False)
    correct: Mapped[bool] = mapped_column(Boolean, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    session: Mapped["GameSession"] = relationship(back_populates="attempts")


class SessionTreasure(Base):
    __tablename__ = "session_treasures"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    session_id: Mapped[int] = mapped_column(ForeignKey("game_sessions.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    unlocked_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    session: Mapped["GameSession"] = relationship(back_populates="treasures")
