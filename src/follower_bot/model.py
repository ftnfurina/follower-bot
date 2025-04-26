from datetime import datetime
from enum import IntEnum
from typing import List, Optional

from pydantic import BaseModel
from sqlmodel import Field, SQLModel


class User(BaseModel):
    id: int = Field(description="User ID")
    login: str = Field(description="User login")


class FollowingCreateBy(IntEnum):
    FOLLOWING_BOT = 1
    FOLLOWER_BOT = 2


class Following(SQLModel, table=True):
    id: Optional[int] = Field(default=None, description="User ID", primary_key=True)
    login: str = Field(description="User login", unique=True)
    create_by: FollowingCreateBy = Field(description="Create by")
    followed: bool = Field(
        default=False, description="Whether the user is followed or not"
    )
    join_date: datetime = Field(
        default_factory=datetime.now, description="Join date of the user"
    )
    followed_date: Optional[datetime] = Field(
        default=None, description="Date when the user was followed"
    )
    fail_count: int = Field(
        default=0, description="Number of times the user failed to follow"
    )


def user2following(user: User, create_by: FollowingCreateBy) -> Following:
    return Following(id=user.id, login=user.login, create_by=create_by)


def users2followings(
    users: List[User], create_by: FollowingCreateBy
) -> List[Following]:
    return [user2following(user, create_by) for user in users]


class Follower(SQLModel, table=True):
    id: Optional[int] = Field(default=None, description="User ID", primary_key=True)
    login: str = Field(description="User login", unique=True)
    join_date: datetime = Field(
        default_factory=datetime.now, description="Join date of the user"
    )
    follower: bool = Field(
        default=True, description="Whether the user is a follower or not"
    )
    follow_date: datetime = Field(
        default_factory=datetime.now, description="Date when the user was followed"
    )
    search_id: int = Field(description="Search ID")
    unfollow_count: int = Field(
        default=0, description="Number of times the user unfollow"
    )


def user2follower(user: User, search_id: int) -> Follower:
    return Follower(id=user.id, login=user.login, search_id=search_id)


def users2followers(users: List[User], search_id: int) -> List[Follower]:
    return [user2follower(user, search_id) for user in users]


class State(SQLModel, table=True):
    id: Optional[int] = Field(default=None, description="State ID", primary_key=True)
    following_last_page: int = Field(default=1, description="Last page of following")
    follower_last_page: int = Field(default=1, description="Last page of follower")
    follower_search_id: int = Field(default=-1, description="Search ID")


class HistoryType(IntEnum):
    FOLLOWING = 1
    FOLLOWER = 2


class HistoryState(IntEnum):
    SUCCESS = 1
    FAIL = 2


class History(SQLModel, table=True):
    id: Optional[int] = Field(default=None, description="History ID", primary_key=True)
    type: HistoryType = Field(description="History type")
    start_date: datetime = Field(
        default_factory=datetime.now, description="Start date of the history"
    )
    end_date: datetime = Field(
        default_factory=datetime.now, description="End date of the history"
    )
    state: HistoryState = Field(default=HistoryState.SUCCESS, description="Job state")
    message: str = Field(default="", description="Job failure message")
    count: int = Field(default=0, description="Number of users processed")
