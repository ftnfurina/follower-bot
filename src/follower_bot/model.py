from datetime import datetime
from typing import Optional
from enum import IntEnum

from sqlmodel import Field, SQLModel


class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, description="User ID", primary_key=True)
    login: str = Field(description="User login", unique=True)
    is_followed: bool = Field(
        default=False, description="Whether the user is followed or not"
    )
    join_at: datetime = Field(default_factory=datetime.now, description="Join date")
    followed_at: Optional[datetime] = Field(
        default=None, description="Date when the user was followed"
    )
    follow_fail_count: int = Field(
        default=0, description="Number of times the user failed to follow"
    )


class State(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    last_page: int = Field(
        default=0,
        description="Last page used to search users",
    )


class HistoryState(IntEnum):
    SUCCESS = 1
    FAIL = 2


class History(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    start_at: datetime = Field(
        default_factory=datetime.now, description="Date when the job was run"
    )
    end_at: datetime = Field(
        default_factory=datetime.now, description="Date when the job finished"
    )
    state: HistoryState = Field(
        default=HistoryState.SUCCESS,
        description="State of the job",
    )
    message: str = Field(default="", description="Job failure message")
    followed_count: int = Field(default=0, description="Number of followed users")
